#!/usr/bin/env python3
import os
import re
import argparse
import sys
from datetime import datetime
from pathlib import Path

TYPE_INFERENCE = {
    'how-to': 'how-to',
    'reference': 'reference',
    'explanation': 'explanation',
    'tutorials': 'tutorial',
    '4-Runbooks': 'runbook',
    '5-ADR': 'adr',
    '7-Notes': 'note'
}

IGNORE_FILES = {'README.md', 'CHANGELOG.md', 'glossary.md'}

def extract_h1_title(content: str, fallback_name: str) -> str:
    match = re.search(r'^#\s+(.+)$', content, flags=re.MULTILINE)
    if match:
        return match.group(1).replace(':', ' -').replace('"', "'").strip()
    return fallback_name.replace('-', ' ').replace('_', ' ').title()

def infer_metadata(filepath: Path) -> dict:
    parts = filepath.parts
    metadata = {'type': 'note', 'domain': 'general', 'status': 'active', 'tags': '[]'}

    if '3-Resources' in parts:
        idx = parts.index('3-Resources')
        if len(parts) > idx + 1:
            metadata['domain'] = parts[idx + 1]

    for path_part in parts:
        if path_part in TYPE_INFERENCE:
            metadata['type'] = TYPE_INFERENCE[path_part]
            break

    return metadata

def fix_front_matter(target_dir: str, dry_run: bool = True):
    root_path = Path(target_dir)
    if not root_path.exists():
        print(f"❌ 错误: 目标知识库路径不存在 ({root_path})", file=sys.stderr)
        sys.exit(1)

    today = datetime.now().strftime("%Y-%m-%d")
    fixed_count = 0
    skipped_count = 0

    print(f"🩺 启动 PEOS Doctor 诊断程序 (Dry-run: {dry_run}) | 目标: {root_path}\n")

    for root, _, files in os.walk(root_path):
        if '/.' in root or root.startswith('.'):
            continue

        for file in files:
            if not file.endswith('.md') or file in IGNORE_FILES:
                continue

            filepath = Path(root) / file
            if '6-Templates' in filepath.parts or '9-Metadata' in filepath.parts:
                continue

            try:
                content = filepath.read_text(encoding='utf-8')
            except Exception as e:
                print(f"❌ 无法读取文件 {filepath}: {e}")
                continue

            if content.startswith('---'):
                skipped_count += 1
                continue

            inferred = infer_metadata(filepath)
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

            print(f"🔧 [发现缺失] {filepath.relative_to(root_path)}")
            print(f"   ↳ 推断元数据: type={inferred['type']} | domain={inferred['domain']}")

            if not dry_run:
                filepath.write_text(yaml_header + content, encoding='utf-8')
            fixed_count += 1

    print("\n" + "="*40)
    print("✅ 诊断报告:")
    print(f"   - 状态正常的文档: {skipped_count} 篇")
    print(f"   - {'模拟' if dry_run else '实际'}修复文档: {fixed_count} 篇")
    if dry_run and fixed_count > 0:
        print("💡 提示: 当前为 --dry-run 模式。执行时追加 `--fix` 参数来真实写入文件。")
    print("="*40)

def main():
    parser = argparse.ArgumentParser(description="PEOS 知识库自动修复与治理工具")
    parser.add_argument("--fix", action="store_true", help="关闭 dry-run 模式，实际修改文件")
    parser.add_argument("-d", "--dir", help="知识库根目录 (优先读取 PEOS_KNOWLEDGE_DIR 环境变量)")

    args = parser.parse_args()

    # 路径解析优先级: CLI 参数 > 环境变量 > 当前目录
    target_dir = args.dir or os.getenv("PEOS_KNOWLEDGE_DIR") or "."

    fix_front_matter(target_dir, dry_run=not args.fix)

if __name__ == "__main__":
    main()
