#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
    from jsonschema import ValidationError, validate
except ImportError:
    print("[Error] 缺少依赖。请执行: uv pip install PyYAML jsonschema", file=sys.stderr)
    sys.exit(1)

# 修改为：
# 推断项目根目录 (personal-ai-kit)
REPO_ROOT = Path(__file__).resolve().parents[3]

# 所有的 Prompt 资产文件现在都位于 prompts/ 目录下
BASE_DIR = REPO_ROOT / "prompts"


def strip_front_matter(text: str) -> str:
    """剥离 Markdown 文件的 YAML Front Matter，避免浪费 Token"""
    return re.sub(r"^---\s*\n.*?\n---\s*\n", "", text, flags=re.DOTALL).strip()


def read_component(category: str, filename: str) -> str:
    """按类别读取 Markdown 组件"""
    if not filename.endswith(".md"):
        filename += ".md"

    filepath = BASE_DIR / category / filename
    if not filepath.exists():
        print(f"[Warning] 缺少依赖文件: {filepath}", file=sys.stderr)
        return ""

    with open(filepath, "r", encoding="utf-8") as f:
        return strip_front_matter(f.read())


def validate_profile(profile_data: dict) -> None:
    """根据 JSON Schema 校验 Profile 格式"""
    schema_path = REPO_ROOT / "schemas" / "profile.schema.json"
    if not schema_path.exists():
        print(f"[Error] 找不到 Schema 校验文件: {schema_path}", file=sys.stderr)
        sys.exit(1)

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    try:
        validate(instance=profile_data, schema=schema)
    except ValidationError as e:
        print(f"[ValidationError] Profile 格式错误: {e.message}", file=sys.stderr)
        print(f"出错字段路径: {list(e.path)}", file=sys.stderr)
        sys.exit(1)


def compile_profile(profile_name: str) -> str:
    """核心编译引擎：组装并渲染完整的 Prompt"""
    if not profile_name.endswith(".yaml"):
        profile_name += ".yaml"

    profile_path = BASE_DIR / "profiles" / profile_name
    if not profile_path.exists():
        print(f"[Error] 找不到 Profile: {profile_path}", file=sys.stderr)
        sys.exit(1)

    with open(profile_path, "r", encoding="utf-8") as f:
        profile_data = yaml.safe_load(f)

    validate_profile(profile_data)

    sections = [
        ("⚙️ SYSTEM POLICY", profile_data.get("system", []), "system"),
        ("🎭 ROLE PERSONA", profile_data.get("roles", []), "roles"),
        ("📚 CONTEXT & KNOWLEDGE", profile_data.get("contexts", []), "contexts"),
        ("🚀 WORKFLOW SOP", profile_data.get("workflows", []), "workflows"),
    ]

    compiled_blocks = [
        f"# {profile_data.get('name')} Profile\n> {profile_data.get('description', '')}\n"
    ]

    for title, items, category in sections:
        if not items:
            continue
        compiled_blocks.append(f"## {title}")
        for item in items:
            content = read_component(category, item)
            if content:
                compiled_blocks.append(content)

    # 使用 Markdown 分隔符组装
    return "\n\n---\n\n".join(compiled_blocks)


def write_to_file(content: str, target_path: Path) -> None:
    """安全的写入操作，自动创建父级目录"""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[Success] 已导出: {target_path}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="PromptOps 编译器引擎")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 子命令 1: run (输出到 stdout，用于 Neovim 或管道配合 Ollama)
    run_parser = subparsers.add_parser("run", help="编译并输出到标准输出")
    run_parser.add_argument("profile", help="Profile 名称 (例如: k3s-admin)")

    # 子命令 2: compile (静态化到 build 目录，供离线查看或基础文件引用)
    compile_parser = subparsers.add_parser("compile", help="编译并输出到 build 目录")
    compile_parser.add_argument("profile", help="Profile 名称")

    # 子命令 3: export (定向分发到业务代码仓库)
    # 修改 1：扩展 choices 支持的工具范围
    export_parser = subparsers.add_parser("export", help="定向分发到特定工具的规则目录")
    export_parser.add_argument(
        "tool",
        choices=["claude", "cursor", "copilot", "cline", "continue"],
        help="目标工具 (claude / cursor / copilot / cline / continue)",
    )
    export_parser.add_argument("profile", help="Profile 名称")
    export_parser.add_argument(
        "-t", "--target", required=True, help="业务代码仓库的绝对路径"
    )

    args = parser.parse_args()

    # ================= 新增：解析 aliases.yaml 逻辑 =================
    raw_profile = args.profile
    alias_path = BASE_DIR / "aliases.yaml"

    if alias_path.exists():
        with open(alias_path, "r", encoding="utf-8") as f:
            try:
                aliases = yaml.safe_load(f) or {}
                # 如果传入的名字在别名表里，就替换成真正的 profile 名称
                if raw_profile in aliases:
                    raw_profile = aliases[raw_profile]
            except Exception as e:
                print(f"[Warning] 无法解析 aliases.yaml: {e}", file=sys.stderr)
    # =================================================================

    # 传入解析后的真实名称进行编译
    compiled_text = compile_profile(raw_profile)
    profile_name = raw_profile.replace(".yaml", "")

    if args.command == "run":
        # 仅输出干净的文本，确保可以安全传递给 pbcopy 或 llm
        print(compiled_text)

    elif args.command == "compile":
        build_dir = REPO_ROOT / "build"
        target_path = build_dir / f"{profile_name}.md"
        write_to_file(compiled_text, target_path)

    elif args.command == "export":
        target_repo = Path(args.target).expanduser().resolve()

        # 修改 2：增加分发路由逻辑
        if args.tool == "claude":
            # Claude Code 约定根目录的 CLAUDE.md
            target_path = target_repo / "CLAUDE.md"
            # 覆写或生成，保证状态一致
            write_to_file(compiled_text, target_path)

        elif args.tool == "cursor":
            # Cursor 约定在 .cursor/rules/ 目录下
            target_path = (
                target_repo / ".cursor" / "rules" / f"generated_{profile_name}.mdc"
            )
            # 在 MDC 文件头部追加 glob 规则 (可选但推荐，帮助 Cursor 自动触发)
            mdc_header = f"---\ndescription: Auto-generated profile for {profile_name}\nglobs: *\n---\n\n"
            write_to_file(mdc_header + compiled_text, target_path)
        elif args.tool == "copilot":
            # GitHub Copilot Chat 官方约定的工作区规则路径
            target_path = target_repo / ".github" / "copilot-instructions.md"
            write_to_file(compiled_text, target_path)

        elif args.tool == "cline":
            # Cline (Claude Dev) 或 RooCode 约定的全自动 Agent 规则路径
            target_path = target_repo / ".clinerules"
            write_to_file(compiled_text, target_path)
        elif args.tool == "continue":
            # Continue 原生支持 .prompts 目录
            target_path = target_repo / ".prompts" / f"{profile_name}.prompt"

            # Continue 的模板语法，增加 system 前缀标识
            continue_header = f"---\nname: {profile_name}\ndescription: Auto-generated profile for {profile_name}\n---\n\n"

            # 强制包裹为 Continue 可识别的 System 级别指令
            # 【修复点】：使用普通字符串拼接代替 f-string，避免 Python 把大括号当成变量解析
            continue_body = (
                "{{{ system }}}\n"
                + compiled_text
                + "\n{{{ /system }}}\n\n{{{ input }}}"
            )

            write_to_file(continue_header + continue_body, target_path)


if __name__ == "__main__":
    main()
