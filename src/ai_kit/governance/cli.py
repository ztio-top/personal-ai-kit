#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    import requests
    import yaml
except ImportError:
    print(
        "❌ 错误: 缺少依赖。请在 ai-kit 环境下执行: uv pip install requests pyyaml",
        file=sys.stderr,
    )
    sys.exit(1)


# ================= 规范：强制 PyYAML 输出单行数组标签 =================
class FlowList(list):
    """用于强制 PyYAML 将列表输出为单行 [a, b] 格式"""

    pass


def flow_list_representer(dumper, data):
    return dumper.represent_sequence("tag:yaml.org,2002:seq", data, flow_style=True)


yaml.add_representer(FlowList, flow_list_representer)
yaml.SafeDumper.add_representer(FlowList, flow_list_representer)
# =================================================================


# PEOS 架构推理映射表 (Type)
TYPE_INFERENCE = {
    "how-to": "how-to",
    "reference": "reference",
    "explanation": "explanation",
    "tutorials": "tutorial",
    "4-Runbooks": "runbook",
    "5-ADR": "adr",
    "7-Notes": "note",
}

IGNORE_FILES = {"README.md", "CHANGELOG.md", "glossary.md"}


def get_allowed_tags(knowledge_dir: Path) -> list:
    """从 9-Metadata/tags.yaml 提取 SSOT 合法标签池"""
    tags_file = knowledge_dir / "9-Metadata" / "tags.yaml"
    if not tags_file.exists():
        return []
    try:
        data = yaml.safe_load(tags_file.read_text(encoding="utf-8"))
        return data.get("tags", []) if data else []
    except Exception:
        return []


def get_tag_governance_config(knowledge_dir: Path) -> tuple:
    """从 9-Metadata/tags.yaml 提取 SSOT 规范标签池与别名映射表"""
    tags_file = knowledge_dir / "9-Metadata" / "tags.yaml"
    if not tags_file.exists():
        return [], {}
    try:
        data = yaml.safe_load(tags_file.read_text(encoding="utf-8")) or {}
        tags = data.get("tags", [])
        aliases = data.get("aliases", {})  # 别名映射，如 {"k8s": "kubernetes"}
        return tags, aliases
    except Exception:
        return [], {}


def ask_llm_for_tags(
    content: str, allowed_tags: list, model: str, api_url: str
) -> list:
    """调用本地 LLM 进行语义打标，实施双重防腐拦截"""
    if not allowed_tags:
        return []

    # 恢复适度截断 (5000字符)，既保证上下文足够，又防止超长文本冲刷掉大模型的指令注意力
    snippet = content[:5000]

    # 利用 LLM 的“近因效应 (Recency Bias)”，将正文放前面，规则放最后
    prompt = (
        f"以下是一篇技术知识库文档的片段：\n"
        f"---------------------\n{snippet}\n---------------------\n\n"
        f"作为严谨的知识库架构师，请为上述文档提取最核心的标签。\n"
        f"【合法标签池】(SSOT)：{allowed_tags}\n\n"
        f"【严格约束】：\n"
        f"1. **宁缺毋滥原则**：只需挑选真正切中核心的技术栈标签（通常 **1 到 5 个**即可）。**绝对不要为了凑数而选择关联度弱的泛概念标签**。\n"
        f"   - 反例：一篇关于 Ollama 命令行的 Cheat Sheet，核心是 'ollama'，**绝不能**因为它是大模型工具就生拉硬套 'gpu'、'ai' 或 'prompt-engineering'。\n"
        f"2. 绝不允许捏造、自创任何不在池中的标签！如果只有 1 个相关，就只返回 1 个。\n"
        f'3. 必须直接返回 JSON 对象，格式必须为：{{"tags": ["标签1", "标签2"]}}。不要输出任何其他解释。'
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "options": {
            "temperature": 0.0,
            # 将 num_predict 设置为 -1（无限），或直接删除该字段，交由模型自行决定何时停止
            "num_predict": -1,
            "num_ctx": 4096,  # 🚀 核心优化 3：显式扩大模型的上下文窗口，破解默认 2048 限制
        },
    }

    try:
        response = requests.post(api_url, json=payload, timeout=120)
        response.raise_for_status()

        result_text = response.json()["message"]["content"].strip()
        print(f"DEBUG - LLM Raw Output: '{result_text[:100]}'")

        if not result_text:
            print(
                "   [⚠️ AI 打标警告] LLM 依然返回为空，请检查模型日志或尝试更换小参数模型",
                file=sys.stderr,
            )
            return []

        # 核心正则提取：从模型的任何废话中精准抠出 JSON 对象
        json_match = re.search(r"\{[\s\S]*\}", result_text)
        if not json_match:
            print("   [⚠️ AI 打标警告] 未在输出中找到 JSON 格式的内容", file=sys.stderr)
            return []

        json_str = json_match.group(0)
        predicted_tags = json.loads(json_str)

        # 柔性兼容：处理返回结果
        if isinstance(predicted_tags, dict):
            if "tags" in predicted_tags and isinstance(predicted_tags["tags"], list):
                predicted_tags = predicted_tags["tags"]
            else:
                for val in predicted_tags.values():
                    if isinstance(val, list):
                        predicted_tags = val
                        break

        # 大小写不敏感的物理防腐层 + 拦截审计日志
        if isinstance(predicted_tags, list):
            # 将合法标签池全部转换为小写，并建立映射字典
            allowed_lower_map = {str(t).lower(): str(t) for t in allowed_tags}

            valid_tags = []
            hallucinated_tags = []

            for tag in predicted_tags:
                tag_lower = str(tag).lower()
                if tag_lower in allowed_lower_map:
                    # 如果匹配成功，存入 `tags.yaml` 中标准的大小写格式
                    valid_tags.append(allowed_lower_map[tag_lower])
                else:
                    # 记录被防腐层拦截的幻觉标签
                    hallucinated_tags.append(tag)

            if hallucinated_tags:
                print(
                    f"   [🛡️ 防腐拦截] LLM 捏造了不在 SSOT 字典中的标签，已剔除: {hallucinated_tags}"
                )

            return valid_tags[:5]

        return []

    except json.JSONDecodeError as e:
        print(f"   [⚠️ AI 打标警告] 抠出的 JSON 解析失败: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"   [⚠️ AI 打标警告] LLM 调用失败或网络异常: {e}", file=sys.stderr)
        return []


def extract_h1_title(content: str, fallback_name: str) -> str:
    match = re.search(r"^#\s+(.+)$", content, flags=re.MULTILINE)
    if match:
        return match.group(1).replace(":", " -").replace('"', "'").strip()
    return fallback_name.replace("-", " ").replace("_", " ").title()


def infer_metadata(filepath: Path) -> dict:
    parts = filepath.parts
    metadata = {"type": None, "domain": None, "status": "active"}

    # 1. 推断 Type (从文件夹命名或 TYPE_INFERENCE 字典中匹配)
    for path_part in parts:
        if path_part in TYPE_INFERENCE:
            metadata["type"] = TYPE_INFERENCE[path_part]
            break

    # 2. 推断 Domain 与特殊目录的架构兜底
    if "3-Resources" in parts:
        idx = parts.index("3-Resources")
        if len(parts) > idx + 1:
            metadata["domain"] = parts[idx + 1]
    elif "4-Runbooks" in parts:
        idx = parts.index("4-Runbooks")
        if len(parts) > idx + 1 and not parts[idx + 1].endswith(".md"):
            metadata["domain"] = parts[idx + 1]
    elif "5-ADR" in parts:
        metadata["domain"] = "architecture"
    elif "2-Areas" in parts:
        # === 针对 2-Areas 的推断 ===
        # Area 是长期的战略、准则与蓝图，因此默认类型设为 explanation
        if not metadata["type"]:
            metadata["type"] = "explanation"
        # 默认归属个人知识与精力管理领域 (pkm)，防腐拦截
        metadata["domain"] = "pkm"

    # 3. 针对笔记草稿的智能降级逻辑
    if metadata["type"] == "note":
        metadata["status"] = "draft"
        if not metadata["domain"]:
            metadata["domain"] = "uncategorized"

    # 4. 终态拦截：如果依然无法推断，交由人工处理
    if not metadata["type"] or not metadata["domain"]:
        return None

    return metadata


def fix_front_matter(
    target_dir: str,
    dry_run: bool = True,
    auto_tag: bool = False,
    model: str = "qwen2.5:14b",
    api_url: str = "",
):
    root_path = Path(target_dir)
    if not root_path.exists():
        print(f"❌ 错误: 目标知识库路径不存在 ({root_path})", file=sys.stderr)
        sys.exit(1)

    allowed_tags = []
    if auto_tag:
        allowed_tags = get_allowed_tags(root_path)
        print("🤖 AI 打标已激活:")
        print(f"   ↳ 目标接口: {api_url}")
        print(f"   ↳ 挂载标签: {len(allowed_tags)} 个 SSOT 字典项 | 模型: {model}")
        if not allowed_tags:
            print(
                "   [⚠️ 警告] 未在 9-Metadata/tags.yaml 发现合法标签，将降级为普通扫描。"
            )

    today = datetime.now().strftime("%Y-%m-%d")
    fixed_count = 0
    skipped_count = 0

    # 🚀 新增：定义两个追踪队列
    manual_queue = []  # 缺乏上下文，无法推断 type/domain 的队列
    tag_failed_queue = []  # AI 打标提取失败（返回为空）的队列

    print(f"\n🩺 启动 PEOS Doctor 诊断程序 (Dry-run: {dry_run}) | 目标: {root_path}\n")

    for root, _, files in os.walk(root_path):
        if "/." in root or root.startswith("."):
            continue

        for file in files:
            if not file.endswith(".md") or file in IGNORE_FILES:
                continue

            filepath = Path(root) / file
            if "6-Templates" in filepath.parts or "9-Metadata" in filepath.parts:
                continue

            try:
                content = filepath.read_text(encoding="utf-8")
            except Exception as e:
                print(f"❌ 无法读取文件 {filepath}: {e}")
                continue

            # ================= 场景一：已有 Front Matter =================
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    try:
                        metadata = yaml.safe_load(parts[1]) or {}
                        body_content = parts[2].strip()
                    except Exception:
                        skipped_count += 1
                        continue

                    # 检查 tags 是否缺失、为 None 或为空列表
                    current_tags = metadata.get("tags")
                    is_tags_empty = not current_tags or (
                        isinstance(current_tags, list) and len(current_tags) == 0
                    )

                    # 如果标签为空，且开启了自动打标
                    if is_tags_empty and auto_tag and allowed_tags:
                        predicted_tags = ask_llm_for_tags(
                            body_content, allowed_tags, model, api_url
                        )
                        if predicted_tags:
                            # 🚀 使用 FlowList 包装，强制触发单行输出规则
                            metadata["tags"] = FlowList(predicted_tags)

                            # 使用 yaml.dump 并显式指定 SafeDumper 重新生成 Front Matter
                            new_front_matter = yaml.dump(
                                metadata,
                                allow_unicode=True,
                                sort_keys=False,
                                Dumper=yaml.SafeDumper,
                            ).strip()
                            new_full_content = (
                                f"---\n{new_front_matter}\n---\n\n{body_content}\n"
                            )

                            print(
                                f"🔧 [补充标签 & 自动修复] {filepath.relative_to(root_path)}"
                            )
                            print(f"   ↳ 补充缺失的 tags: {predicted_tags}")

                            if not dry_run:
                                filepath.write_text(new_full_content, encoding="utf-8")
                            fixed_count += 1
                            continue
                        else:
                            # 🚀 新增：记录已有头部但打标失败的文件
                            tag_failed_queue.append(filepath)

                    skipped_count += 1
                    continue

            # ================= 场景二：完全没有 Front Matter =================
            # 触发推断逻辑
            inferred = infer_metadata(filepath)

            # 如果推断失败（例如 7-Notes 缺少 domain 子目录），拦截并放入人工队列
            if not inferred:
                manual_queue.append(filepath)
                continue

            title = extract_h1_title(content, filepath.stem)

            # AI 语义打标流水线
            final_tags_list = []
            if auto_tag and allowed_tags:
                predicted_tags = ask_llm_for_tags(content, allowed_tags, model, api_url)
                if predicted_tags:
                    # 格式化为 YAML 数组风格: [k3s, ansible]
                    final_tags_list = predicted_tags
                else:
                    # 🚀 新增：记录完全缺失头部，修复了头部但打标失败的文件
                    tag_failed_queue.append(filepath)

            metadata_dict = {
                "title": title,
                "type": inferred["type"],
                "domain": inferred["domain"],
                "status": inferred["status"],
                "created": today,
                "tags": FlowList(final_tags_list),
            }

            new_front_matter = yaml.dump(
                metadata_dict,
                allow_unicode=True,
                sort_keys=False,
                Dumper=yaml.SafeDumper,
            ).strip()
            yaml_header = f"---\n{new_front_matter}\n---\n\n"

            print(f"🔧 [发现缺失 & 自动修复] {filepath.relative_to(root_path)}")
            print(
                f"   ↳ 注入元数据: type={inferred['type']} | domain={inferred['domain']} | tags={final_tags_list}"
            )

            if not dry_run:
                filepath.write_text(yaml_header + content, encoding="utf-8")
            fixed_count += 1

    # 🚀 优化：增强版的最终诊断报告输出
    print("\n" + "=" * 50)
    print("✅ 诊断报告:")
    print(f"   - 状态正常/已跳过: {skipped_count} 篇")
    print(f"   - 成功推断并{'拟' if dry_run else ''}修复: {fixed_count} 篇")

    if tag_failed_queue:
        print(f"   - ⚠️ AI 打标失败/需复核: {len(tag_failed_queue)} 篇")

    if manual_queue:
        print(
            "\n⚠️ 以下文档因缺乏路径上下文无法自动归类，请手动介入 (Manual Intervention):"
        )
        for p in manual_queue:
            print(f"   - {p.relative_to(root_path)}")

    if tag_failed_queue:
        print("\n⚠️ 以下文档 AI 打标失败 (未生成有效 JSON 标签或触发防腐拦截):")
        for p in tag_failed_queue:
            print(f"   - {p.relative_to(root_path)}")

    if dry_run and fixed_count > 0:
        print("\n💡 提示: 当前为 --dry-run 模式。执行 `doctor --fix` 真实写入文件。")
    print("=" * 50)


def audit_tag_governance(
    target_dir: str, fix: bool = False, sync_new_tags: bool = False
):
    """知识库标签全局合规审计：支持别名归一化、严格净化（清除未注册标签）或演进同步（追加新标签至 tags.yaml）"""
    root_path = Path(target_dir)
    tags_file = root_path / "9-Metadata" / "tags.yaml"

    allowed_tags, tag_aliases = get_tag_governance_config(root_path)
    allowed_set = set(allowed_tags)
    alias_lower_map = {str(k).lower(): str(v) for k, v in tag_aliases.items()}

    print(
        f"\n🔍 启动知识库标签合规审计 (SSOT 规范池: {len(allowed_set)} 个 | 别名映射: {len(alias_lower_map)} 条) | Mode (Fix: {fix}, Sync: {sync_new_tags})\n"
    )

    file_drift_map = {}
    unregistered_found = set()

    for root, _, files in os.walk(root_path):
        if "/." in root or root.startswith("."):
            continue
        for file in files:
            if not file.endswith(".md") or file in IGNORE_FILES:
                continue
            filepath = Path(root) / file
            if "6-Templates" in filepath.parts or "9-Metadata" in filepath.parts:
                continue

            try:
                content = filepath.read_text(encoding="utf-8")
                if not content.startswith("---"):
                    continue
                parts = content.split("---", 2)
                if len(parts) < 3:
                    continue
                metadata = yaml.safe_load(parts[1]) or {}
                doc_tags = metadata.get("tags", [])
                if not isinstance(doc_tags, list):
                    continue
            except Exception:
                continue

            # 检查漂移：既不在规范池中，也不在别名映射中的标签
            invalid_tags = []
            for t in doc_tags:
                t_lower = str(t).lower()
                if t not in allowed_set and t_lower not in alias_lower_map:
                    invalid_tags.append(t)

            if invalid_tags:
                file_drift_map[filepath] = invalid_tags
                for t in invalid_tags:
                    unregistered_found.add(t)

    if not file_drift_map:
        print("✨ 标签合规审计通过：所有文档的 tags 均完全契合规范！")
        return

    print(f"⚠️ 发现 {len(file_drift_map)} 篇文档存在标签漂移或未注册标签：")
    for fp, bad_tags in file_drift_map.items():
        print(f"   - {fp.relative_to(root_path)}: {bad_tags}")

    if unregistered_found:
        print(
            f"\n📋 共检测到 {len(unregistered_found)} 个非规范/未注册标签: {list(unregistered_found)}"
        )

    if fix:
        print("\n" + "=" * 50)
        if sync_new_tags:
            print(
                "🚀 [模式 A：演进同步] 正在应用别名归一化，并将新发现的合法标签同步注册至 tags.yaml..."
            )
        else:
            print(
                "🧹 [模式 B：严格净化] 正在应用别名归一化，并从文档中清除未注册的非法标签..."
            )
        print("=" * 50)

        truly_new_tags = set()

        for filepath, bad_tags in file_drift_map.items():
            try:
                content = filepath.read_text(encoding="utf-8")
                parts = content.split("---", 2)
                metadata = yaml.safe_load(parts[1]) or {}
                body = parts[2].strip()

                doc_tags = metadata.get("tags", [])
                new_tags = []

                for t in doc_tags:
                    t_lower = str(t).lower()
                    if t in allowed_set:
                        # 1. 已经是规范标签，直接保留
                        new_tags.append(t)
                    elif t_lower in alias_lower_map:
                        # 2. 属于已知别名，安全归一化（如 k8s -> kubernetes）
                        canonical = alias_lower_map[t_lower]
                        new_tags.append(canonical)
                        print(
                            f"   🔄 [别名归一化] {filepath.name}: '{t}' ➡️ '{canonical}'"
                        )
                    else:
                        # 3. 完全未注册的野标签
                        if sync_new_tags:
                            # 演进同步模式：保留在文档中，准备收录入 SSOT 字典
                            new_tags.append(t)
                            truly_new_tags.add(t)
                            print(f"   ➕ [演进保留] {filepath.name}: 保留新标签 '{t}'")
                        else:
                            # 严格净化模式：直接从文档中清除
                            print(
                                f"   🗑️ [严格净化] {filepath.name}: 清除未注册标签 '{t}'"
                            )

                metadata["tags"] = FlowList(sorted(list(set(new_tags))))
                new_fm = yaml.dump(
                    metadata,
                    allow_unicode=True,
                    sort_keys=False,
                    Dumper=yaml.SafeDumper,
                ).strip()
                filepath.write_text(f"---\n{new_fm}\n---\n\n{body}\n", encoding="utf-8")
            except Exception as e:
                print(f"❌ 处理文件 {filepath} 失败: {e}", file=sys.stderr)

        # 如果开启了 sync_new_tags，将真正的新标签追加到 tags.yaml 中
        if sync_new_tags and tags_file.exists() and truly_new_tags:
            try:
                data = yaml.safe_load(tags_file.read_text(encoding="utf-8")) or {}
                current_tags_list = data.get("tags", [])
                updated_tags_list = sorted(
                    list(set(current_tags_list + list(truly_new_tags)))
                )
                data["tags"] = updated_tags_list

                tags_file.write_text(
                    yaml.dump(
                        data,
                        allow_unicode=True,
                        sort_keys=False,
                        Dumper=yaml.SafeDumper,
                    ),
                    encoding="utf-8",
                )
                print(
                    f"\n✅ [SSOT 演进成功] 已自动将 {len(truly_new_tags)} 个新标签追加注册到 {tags_file.relative_to(root_path)}: {list(truly_new_tags)}"
                )
            except Exception as e:
                print(f"❌ 写入 tags.yaml 失败: {e}", file=sys.stderr)

        print("\n✅ 审计修复执行完毕！")
    else:
        print("\n💡 提示:")
        print(
            "   - 执行 `doctor --audit --fix` ➡️ 进入【严格净化模式】（自动归一化别名，并从文档中清除所有未注册标签）。"
        )
        print(
            "   - 执行 `doctor --audit --fix --sync-tags` ➡️ 进入【演进同步模式】（自动归一化别名，并将新发现的优质标签收录进 tags.yaml）。"
        )


def main():
    parser = argparse.ArgumentParser(description="PEOS 知识库自动修复与智能治理工具")
    parser.add_argument(
        "--fix", action="store_true", help="关闭 dry-run 模式，实际修改文件"
    )
    parser.add_argument(
        "-d", "--dir", help="知识库根目录 (优先读取 PEOS_KNOWLEDGE_DIR)"
    )
    parser.add_argument(
        "--auto-tag", action="store_true", help="启用基于大模型的智能语义打标"
    )
    parser.add_argument(
        "-m", "--model", default="qwen2.5:14b", help="智能打标使用的 Ollama 模型名称"
    )
    parser.add_argument("--api-url", help="Ollama API 完整接口地址")
    parser.add_argument(
        "--audit",
        action="store_true",
        help="执行标签合规审计，检查是否存在未注册的孤儿标签",
    )
    parser.add_argument(
        "--sync-tags",
        action="store_true",
        help="配合 --audit --fix 使用，将新发现的标签自动同步注册到 tags.yaml",
    )

    args = parser.parse_args()

    target_dir = args.dir or os.getenv("PEOS_KNOWLEDGE_DIR") or "."
    api_url = (
        args.api_url
        or os.getenv("PEOS_OLLAMA_API_URL")
        or "http://127.0.0.1:11434/api/chat"
    )

    if args.audit:
        audit_tag_governance(target_dir, fix=args.fix, sync_new_tags=args.sync_tags)
    else:
        fix_front_matter(
            target_dir,
            dry_run=not args.fix,
            auto_tag=args.auto_tag,
            model=args.model,
            api_url=api_url,
        )


if __name__ == "__main__":
    main()
