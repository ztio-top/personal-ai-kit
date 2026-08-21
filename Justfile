set shell := ["bash", "-c"]

# 默认指令：列出所有可用任务
default:
    @just --list

# ==========================================
# 1. 环境初始化 (Environment Setup)
# ==========================================

# 初始化项目依赖并注册 pre-commit 钩子
setup:
    uv sync
    pre-commit install

# ==========================================
# 2. 代码质量治理 (Code Quality)
# ==========================================

# 执行全量代码检查与修复 (Ruff + YAML/JSON 校验)
lint:
    pre-commit run --all-files

# ==========================================
# 3. 三大核心引擎入口 (Core Engines)
# ==========================================

# 运行 PromptOps 编译器 (例: just promptops run kit)
promptops +args:
    uv run promptops {{ args }}

# 运行 PEOS Doctor 治理机 (例: just doctor --audit --fix)
doctor +args="":
    uv run peos-doctor {{ args }}

# 运行 PEOS RAG 问答机 (例: just ask "K3s网络排错")
ask query +args="":
    uv run peos-ask "{{ query }}" {{ args }}

# ==========================================
# 4. 项目自维护流 (Dogfooding)
# ==========================================

# 极速将自维护规则导出到当前目录 (支持传入 tool 参数，如 just export-rules cursor)
export-rules tool="continue":
    uv run promptops export {{ tool }} kit -t .
