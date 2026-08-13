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
    """从 9-Metadata/tags.yaml 提取 SSOT 规范标签池"""
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
        aliases = data.get("aliases", {})  # 别名映射
        return tags, aliases
    except Exception:
        return [], {}


def _call_llm_for_tags(
    prompt: str, allowed_tags: list, model: str, api_url: str, file_context: str = ""
) -> list:
    """内部通用函数：调用 LLM，强制 JSON 输出，并经过严格的防腐层清洗"""
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a strict Metadata Governance Engine. You MUST output ONLY valid JSON format. Absolutely no conversational filler, no markdown blocks. Start your response with '{'.",
            },
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.0,
            "num_predict": -1,
            "num_ctx": 4096,
        },
    }

    try:
        response = requests.post(api_url, json=payload, timeout=120)
        response.raise_for_status()

        result_text = response.json()["message"]["content"].strip()

        # 🚀 优化 1：Debug 日志带上明确的文件名
        ctx_str = f"[{file_context}] " if file_context else ""
        print(
            f"   🐛 DEBUG - {ctx_str}LLM Raw: '{result_text[:150].replace(chr(10), ' ')}'"
        )

        if not result_text:
            print(f"   [⚠️ AI 打标警告] {ctx_str}LLM 返回为空", file=sys.stderr)
            return []

        try:
            predicted_data = json.loads(result_text)
        except json.JSONDecodeError:
            json_match = re.search(r"\{[\s\S]*\}", result_text)
            if not json_match:
                print(
                    "   [⚠️ AI 打标警告] 未在输出中找到 JSON 格式的内容", file=sys.stderr
                )
                return []
            predicted_data = json.loads(json_match.group(0))

        predicted_tags = []
        if isinstance(predicted_data, dict):
            if "tags" in predicted_data and isinstance(predicted_data["tags"], list):
                predicted_tags = predicted_data["tags"]
            else:
                for val in predicted_data.values():
                    if isinstance(val, list):
                        predicted_tags = val
                        break

        if isinstance(predicted_tags, list):
            allowed_lower_map = {str(t).lower(): str(t) for t in allowed_tags}
            valid_tags = []
            hallucinated_tags = []

            for tag in predicted_tags:
                tag_lower = str(tag).lower()
                if tag_lower in allowed_lower_map:
                    valid_tags.append(allowed_lower_map[tag_lower])
                else:
                    hallucinated_tags.append(tag)

            if hallucinated_tags:
                print(
                    f"   [🛡️ 防腐拦截] {ctx_str}LLM 捏造了不在规范池的标签: {hallucinated_tags}"
                )

            return valid_tags

        return []
    except Exception as e:
        print(f"   [⚠️ AI 打标警告] {ctx_str}调用异常: {e}", file=sys.stderr)
        return []


def ask_llm_for_tags(
    content: str, allowed_tags: list, model: str, api_url: str, file_context: str = ""
) -> list:
    """[增量补全场景] 为完全没有 tags 的文档生成新标签"""
    if not allowed_tags:
        return []

    snippet = content[:5000]
    prompt = (
        f"【文档文本片段】(Document Fragment)：\n---------------------\n{snippet}\n---------------------\n\n"
        f"【执行角色】(Role)：元数据治理引擎 (Metadata Governance Engine)\n"
        f"【核心任务】(Task)：基于全局语义进行高精度的技术栈标签提取。\n"
        f"【SSOT 字典池】(Single Source of Truth)：{allowed_tags}\n\n"
        f"【架构约束】(Architecture Constraints)：\n"
        f"1. **高信噪比原则 (High Signal-to-Noise Ratio)**：极度收敛标签数量（1~3个，上限3个）。若仅有 1 个技术栈符合，绝对禁止凑数。\n"
        f"2. **全局主旨锚定 (Global Semantic Dominance)**：严格区分【全局核心论点】与【局部辅助示例】。对于仅在示例中出现的从属技术栈，必须判定为局部干扰项并剔除。\n"
        f"3. **向池内抽象归拢 (Ontology Mapping)**：如果文档的主旨是一个极度具体的工具（如 grep, awk, apt, cmd, head 等），但在【SSOT 字典池】中找不到该具体名称，**请绝对不要直接返回空数组 []**！而是应当向上抽象，从池中挑选最契合的通用领域标签（例如：'cli', 'linux', 'bash', 'automation', 'macos' 等）。\n"
        f"4. **强制前置推理 (CoT Inference)**：必须在 JSON 内部先构造 'semantic_analysis' 字段，精准剖析核心意图，陈述向上抽象或排除干扰的逻辑。\n"
        f"5. **SSOT 强校验 (Strict Validation)**：输出的 'tags' 必须 100% 存在于上述【SSOT 字典池】中。\n\n"
        f"【输出规约】(Output Specification)：返回标准 JSON 对象，结构如下：\n"
        f"{{\n"
        f'  "semantic_analysis": "<一句话主旨提炼> + <向上抽象或排除干扰项的说明>",\n'
        f'  "tags": ["<Tag1>", "<Tag2>"]\n'
        f"}}\n"
    )
    return _call_llm_for_tags(prompt, allowed_tags, model, api_url, file_context)[:5]


def ask_llm_for_tag_optimization(
    current_tags: list,
    content: str,
    allowed_tags: list,
    model: str,
    api_url: str,
    file_context: str = "",
) -> list:
    """[质检精简场景] 对已存在的大量冗余标签进行降噪和精简"""
    if not allowed_tags:
        return current_tags

    snippet = content[:3000]
    prompt = (
        f"【当前分配的元数据】(Current Tags)：{current_tags}\n"
        f"【文档文本片段】(Document Fragment)：\n---------------------\n{snippet}\n---------------------\n\n"
        f"【执行角色】(Role)：元数据质量审计引擎 (Metadata Quality Auditor)\n"
        f"【核心任务】(Task)：对现有的标签列表进行语义降噪与冗余精简 (Semantic Denoising & Pruning)。\n"
        f"【SSOT 字典池】(Single Source of Truth)：{allowed_tags}\n\n"
        f"【架构约束】(Architecture Constraints)：\n"
        f"1. **维度收敛 (Dimensionality Reduction)**：将标签数量严格收敛至 1~2 个最能代表该文档工程灵魂的具体技术实体。禁止保留冗余集合。\n"
        f"2. **过滤假阳性误判 (Filter False Positives)**：严格审查当前的标签池，强行剥离以下两类噪声数据：\n"
        f"   - **局部示例污染 (Local Example Pollution)**：仅在正文示例中提及，并非核心探讨对象的技术栈。\n"
        f"   - **宏观概念泛化 (Macroscopic Noise)**：颗粒度过大的抽象领域词汇（如 'ai', 'concept'）。\n"
        f"3. **强制审计追踪 (Audit Trail)**：构造 'audit_log' 字段，说明哪些标签被判定为污染并实施裁剪。\n"
        f"4. **SSOT 强校验 (Strict Validation)**：最终保留的 'tags' 必须位于【SSOT 字典池】中。\n\n"
        f"【输出规约】(Output Specification)：返回标准 JSON 对象，结构如下：\n"
        f"{{\n"
        f'  "audit_log": "已剔除 <标签A>(局部示例污染)，保留 <标签C>(核心技术栈)。",\n'
        f'  "tags": ["<核心Tag1>"]\n'
        f"}}\n"
    )
    return _call_llm_for_tags(prompt, allowed_tags, model, api_url, file_context)[:2]


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


def optimize_tag_governance(target_dir: str, fix: bool, model: str, api_url: str):
    """【第三梯队】执行标签语义质量质检与冗余精简"""
    root_path = Path(target_dir)
    allowed_tags, _ = get_tag_governance_config(root_path)
    if not allowed_tags:
        print("❌ 错误: 未发现 tags.yaml 合法标签池。")
        return

    print(f"\n🔍 启动知识库标签质量语义质检 (Model: {model} | Fix: {fix})\n")

    optimized_count = 0
    skipped_count = 0

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
                current_tags = metadata.get("tags", [])

                if not isinstance(current_tags, list) or len(current_tags) < 3:
                    skipped_count += 1
                    continue

                body_content = parts[2].strip()

                print(
                    f"⏳ [质检评估] 正在审查: {filepath.relative_to(root_path)} (当前包含 {len(current_tags)} 个标签)"
                )

                optimized_tags = ask_llm_for_tag_optimization(
                    current_tags, body_content, allowed_tags, model, api_url
                )

                if not optimized_tags or set(optimized_tags) == set(current_tags):
                    print("   ↳ ✅ 评估结果: 当前标签紧凑或无需精简。")
                    skipped_count += 1
                    continue

                print(
                    f"   ✂️ [降噪精简] 冗余标签已砍掉! {current_tags} ➡️ {optimized_tags}"
                )

                if fix:
                    metadata["tags"] = FlowList(optimized_tags)
                    new_fm = yaml.dump(
                        metadata,
                        allow_unicode=True,
                        sort_keys=False,
                        Dumper=yaml.SafeDumper,
                    ).strip()
                    filepath.write_text(
                        f"---\n{new_fm}\n---\n\n{body_content}\n", encoding="utf-8"
                    )
                    optimized_count += 1

            except Exception as e:
                print(f"❌ 处理 {filepath.name} 时出错: {e}")

    print("\n" + "=" * 50)
    print("✅ 语义精简报告:")
    print(f"   - 跳过或无需精简: {skipped_count} 篇")
    print(f"   - 成功执行降噪精简: {optimized_count} 篇")
    if not fix and optimized_count > 0:
        print(
            "\n💡 提示: 当前为只读评估模式。执行 `doctor --optimize-tags --fix` 将真实重写冗余标签。"
        )
    print("=" * 50)


def audit_tag_governance(
    target_dir: str, fix: bool = False, sync_new_tags: bool = False
):
    """【第二梯队】知识库标签全局合规审计：支持别名归一化、大小写纠正、严格净化或演进同步"""
    root_path = Path(target_dir)
    tags_file = root_path / "9-Metadata" / "tags.yaml"

    allowed_tags, tag_aliases = get_tag_governance_config(root_path)
    allowed_set = set(allowed_tags)
    alias_lower_map = {str(k).lower(): str(v) for k, v in tag_aliases.items()}
    # 🚀 新增：构建标准标签的小写映射，用于自动纠正大小写（如 Kubernetes -> kubernetes）
    allowed_lower_map = {str(k).lower(): k for k in allowed_set}

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

            # 🚀 优化：细化审查颗粒度，不仅查野标签，也查别名和大小写
            issues = []
            for t in doc_tags:
                t_lower = str(t).lower()
                if t in allowed_set:
                    continue  # 完全合规
                elif t_lower in allowed_lower_map:
                    issues.append(f"大小写错误({t})")
                elif t_lower in alias_lower_map:
                    issues.append(f"存在别名({t})")
                else:
                    issues.append(f"未注册({t})")
                    unregistered_found.add(t)

            # 只要文件存在任何不规范情况，就将其推入待修复队列
            if issues:
                file_drift_map[filepath] = issues

    if not file_drift_map:
        print("✨ 标签合规审计通过：所有文档的 tags 均完全契合规范！")
        return

    print(
        f"⚠️ 发现 {len(file_drift_map)} 篇文档需要处理（需归一化、修正大小写或清理野标签）："
    )
    for fp, issues in file_drift_map.items():
        print(f"   - {fp.relative_to(root_path)}: {issues}")

    if unregistered_found:
        print(
            f"\n📋 共检测到 {len(unregistered_found)} 个非规范/未注册标签: {list(unregistered_found)}"
        )

    if fix:
        print("\n" + "=" * 50)
        if sync_new_tags:
            print(
                "🚀 [模式 A：演进同步] 正在应用别名与大小写归一化，并将新标签同步注册至 tags.yaml..."
            )
        else:
            print(
                "🧹 [模式 B：严格净化] 正在应用别名与大小写归一化，并清除所有未注册的非法标签..."
            )
        print("=" * 50)

        truly_new_tags = set()

        for filepath, _ in file_drift_map.items():
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
                        new_tags.append(t)
                    elif t_lower in allowed_lower_map:
                        # 🚀 新增：大小写自动修正
                        canonical = allowed_lower_map[t_lower]
                        new_tags.append(canonical)
                        print(
                            f"   ✨ [规范大小写] {filepath.name}: '{t}' ➡️ '{canonical}'"
                        )
                    elif t_lower in alias_lower_map:
                        # 别名归一化处理恢复正常
                        canonical = alias_lower_map[t_lower]
                        new_tags.append(canonical)
                        print(
                            f"   🔄 [别名归一化] {filepath.name}: '{t}' ➡️ '{canonical}'"
                        )
                    else:
                        if sync_new_tags:
                            new_tags.append(t)
                            truly_new_tags.add(t)
                            print(f"   ➕ [演进保留] {filepath.name}: 保留新标签 '{t}'")
                        else:
                            print(
                                f"   🗑️ [严格净化] {filepath.name}: 清除未注册标签 '{t}'"
                            )

                # 去重并排序
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
        print("   - 执行 `doctor --audit --fix` ➡️ 自动清洗非法标签，并执行归一化。")
        print(
            "   - 执行 `doctor --audit --fix --sync-tags` ➡️ 执行归一化，并将优质标签收录进 tags.yaml。"
        )


def fix_front_matter(
    target_dir: str, dry_run: bool, auto_tag: bool, model: str, api_url: str
):
    """【第一梯队】基础元数据修复与增量补全"""
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

    today = datetime.now().strftime("%Y-%m-%d")
    fixed_count = 0
    skipped_count = 0

    manual_queue = []
    tag_failed_queue = []

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

                    current_tags = metadata.get("tags")
                    is_tags_empty = not current_tags or (
                        isinstance(current_tags, list) and len(current_tags) == 0
                    )

                    if is_tags_empty and auto_tag and allowed_tags:
                        # 🚀 优化 2：耗时操作前，先打日志，避免终端像“假死”一样
                        print(
                            f"⏳ [AI 增量打标] 正在推理分析: {filepath.relative_to(root_path)}"
                        )

                        # 传入 file_context
                        predicted_tags = ask_llm_for_tags(
                            body_content,
                            allowed_tags,
                            model,
                            api_url,
                            file_context=filepath.name,
                        )
                        if predicted_tags:
                            metadata["tags"] = FlowList(predicted_tags)

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
                            tag_failed_queue.append(filepath)

                    skipped_count += 1
                    continue

            # ================= 场景二：完全没有 Front Matter =================
            inferred = infer_metadata(filepath)

            if not inferred:
                manual_queue.append(filepath)
                continue

            title = extract_h1_title(content, filepath.stem)

            final_tags_list = []
            if auto_tag and allowed_tags:
                # 🚀 优化 2：耗时操作前日志
                print(
                    f"⏳ [AI 全新打标] 正在推理分析: {filepath.relative_to(root_path)}"
                )

                # 传入 file_context
                predicted_tags = ask_llm_for_tags(
                    content, allowed_tags, model, api_url, file_context=filepath.name
                )
                if predicted_tags:
                    final_tags_list = predicted_tags
                else:
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

    # [第二梯队命令]
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

    # [第三梯队命令]
    parser.add_argument(
        "--optimize-tags",
        action="store_true",
        help="高级治理：调用 LLM 对已分配了过多标签的文档进行语义质检与降噪精简",
    )

    args = parser.parse_args()
    target_dir = args.dir or os.getenv("PEOS_KNOWLEDGE_DIR") or "."
    api_url = (
        args.api_url
        or os.getenv("PEOS_OLLAMA_API_URL")
        or "http://127.0.0.1:11434/api/chat"
    )

    # 路由选择分发
    if args.optimize_tags:
        optimize_tag_governance(
            target_dir, fix=args.fix, model=args.model, api_url=api_url
        )
    elif args.audit:
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
