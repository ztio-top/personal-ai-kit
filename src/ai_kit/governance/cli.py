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


def ask_llm_for_tags(
    content: str, allowed_tags: list, model: str, api_url: str
) -> list:
    """调用本地 LLM 进行语义打标，实施双重防腐拦截"""
    if not allowed_tags:
        return []

    # 截取前 N 个字符用于语义分析
    snippet = content[:5000]

    system_prompt = (
        "你是一个极其严谨的技术知识库管理员。你的任务是为文本打标签。\n"
        f"请从以下合法标签池中挑选 1 到 3 个最相关的标签：{allowed_tags}\n"
        '返回合法的 JSON 数组，例如: ["k3s", "ansible"]'
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"文本片段如下:\n{snippet}"},
        ],
        "stream": False,
        "temperature": 0.0,
        "format": "json",
    }

    try:
        response = requests.post(api_url, json=payload, timeout=15)
        response.raise_for_status()
        result_text = response.json()["message"]["content"]
        print(f"DEBUG - LLM Raw Output: {result_text}")

        predicted_tags = json.loads(result_text)

        # 🚀 柔性兼容：如果 LLM 不听话返回了 {"tags": ["a", "b"]}，提取其中的列表
        if isinstance(predicted_tags, dict):
            # 尝试提取字典里第一个是列表的值，或者直接找 "tags" 键
            if "tags" in predicted_tags and isinstance(predicted_tags["tags"], list):
                predicted_tags = predicted_tags["tags"]
            else:
                for val in predicted_tags.values():
                    if isinstance(val, list):
                        predicted_tags = val
                        break

        # 物理防腐层：严格清洗不在字典中的幻觉标签
        if isinstance(predicted_tags, list):
            valid_tags = [tag for tag in predicted_tags if tag in allowed_tags]
            # 🚀 强制架构约束：不管 LLM 返回多少个，代码层死守只取前 3 个相关度最高的
            return valid_tags[:3]

        return []
    except Exception as e:
        print(
            f"   [⚠️ AI 打标警告] LLM 调用失败或解析异常: {e}",
            file=sys.stderr,
        )
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
    manual_queue = []

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

            if content.startswith("---"):
                skipped_count += 1
                continue

            # 触发推断逻辑
            inferred = infer_metadata(filepath)

            # 如果推断失败（例如 7-Notes 缺少 domain 子目录），拦截并放入人工队列
            if not inferred:
                manual_queue.append(filepath)
                continue

            title = extract_h1_title(content, filepath.stem)

            # AI 语义打标流水线
            final_tags_str = "[]"
            if auto_tag and allowed_tags:
                predicted_tags = ask_llm_for_tags(content, allowed_tags, model, api_url)
                if predicted_tags:
                    # 格式化为 YAML 数组风格: [k3s, ansible]
                    final_tags_str = f"[{', '.join(predicted_tags)}]"

            yaml_header = (
                "---\n"
                f"title: {title}\n"
                f"type: {inferred['type']}\n"
                f"domain: {inferred['domain']}\n"
                f"status: {inferred['status']}\n"
                f"created: {today}\n"
                f"tags: {final_tags_str}\n"
                "---\n\n"
            )

            print(f"🔧 [发现缺失 & 自动修复] {filepath.relative_to(root_path)}")
            print(
                f"   ↳ 注入元数据: type={inferred['type']} | domain={inferred['domain']} | tags={final_tags_str}"
            )

            if not dry_run:
                filepath.write_text(yaml_header + content, encoding="utf-8")
            fixed_count += 1

    print("\n" + "=" * 50)
    print("✅ 诊断报告:")
    print(f"   - 状态正常/已跳过: {skipped_count} 篇")
    print(f"   - 成功推断并{'拟' if dry_run else ''}修复: {fixed_count} 篇")

    if manual_queue:
        print("\n⚠️ 以下文档因缺乏上下文无法自动归类，请手动处理 (Manual Intervention):")
        for p in manual_queue:
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
    parser.add_argument(
        "--api-url",
        help="Ollama API 完整接口地址 (优先读取 PEOS_OLLAMA_API_URL 环境变量)",
    )

    args = parser.parse_args()

    # 路径解析优先级: CLI 参数 > 环境变量 > 默认兜底值
    target_dir = args.dir or os.getenv("PEOS_KNOWLEDGE_DIR") or "."
    api_url = (
        args.api_url
        or os.getenv("PEOS_OLLAMA_API_URL")
        or "http://127.0.0.1:11434/api/chat"
    )

    fix_front_matter(
        target_dir,
        dry_run=not args.fix,
        auto_tag=args.auto_tag,
        model=args.model,
        api_url=api_url,
    )


if __name__ == "__main__":
    main()
