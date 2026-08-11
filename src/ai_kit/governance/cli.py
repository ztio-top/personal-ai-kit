#!/usr/bin/env python3
import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

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


def extract_h1_title(content: str, fallback_name: str) -> str:
    match = re.search(r"^#\s+(.+)$", content, flags=re.MULTILINE)
    if match:
        return match.group(1).replace(":", " -").replace('"', "'").strip()
    return fallback_name.replace("-", " ").replace("_", " ").title()


def infer_metadata(filepath: Path) -> dict:
    parts = filepath.parts
    metadata = {"type": None, "domain": None, "status": "active", "tags": "[]"}

    # 1. 推断 Type
    for path_part in parts:
        if path_part in TYPE_INFERENCE:
            metadata["type"] = TYPE_INFERENCE[path_part]
            break

    # 2. 推断 Domain
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

    # === 针对 7-Notes 的智能降级逻辑 ===
    if metadata["type"] == "note":
        metadata["status"] = "draft"  # 笔记默认降级为草稿
        if not metadata["domain"]:
            # 如果笔记没有放在特定领域的子目录下，合法分配给 uncategorized
            metadata["domain"] = "uncategorized"

    # 3. 终态拦截：如果依然无法推断出明确的 Type 或 Domain，交由人工处理
    if not metadata["type"] or not metadata["domain"]:
        return None

    return metadata


def fix_front_matter(target_dir: str, dry_run: bool = True):
    root_path = Path(target_dir)
    if not root_path.exists():
        print(f"❌ 错误: 目标知识库路径不存在 ({root_path})", file=sys.stderr)
        sys.exit(1)

    today = datetime.now().strftime("%Y-%m-%d")
    fixed_count = 0
    skipped_count = 0
    manual_queue = []

    print(f"🩺 启动 PEOS Doctor 诊断程序 (Dry-run: {dry_run}) | 目标: {root_path}\n")

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

            yaml_header = (
                "---\n"
                f"title: {title}\n"
                f"type: {inferred['type']}\n"
                f"domain: {inferred['domain']}\n"
                f"status: {inferred['status']}\n"
                f"created: {today}\n"
                f"tags: {inferred['tags']}\n"
                "---\n\n"
            )

            print(f"🔧 [发现缺失 & 自动修复] {filepath.relative_to(root_path)}")
            print(
                f"   ↳ 注入元数据: type={inferred['type']} | domain={inferred['domain']} | status={inferred['status']}"
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
    parser = argparse.ArgumentParser(description="PEOS 知识库自动修复与治理工具")
    parser.add_argument(
        "--fix", action="store_true", help="关闭 dry-run 模式，实际修改文件"
    )
    parser.add_argument(
        "-d", "--dir", help="知识库根目录 (优先读取 PEOS_KNOWLEDGE_DIR 环境变量)"
    )

    args = parser.parse_args()
    target_dir = args.dir or os.getenv("PEOS_KNOWLEDGE_DIR") or "."
    fix_front_matter(target_dir, dry_run=not args.fix)


if __name__ == "__main__":
    main()
