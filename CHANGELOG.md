# Changelog

All notable changes to this project will be documented in this file.

## [0.2.1] - 2026-08-11

### Changed

- **Dependencies**: 更新了 `uv.lock` 锁文件，正式锁定了 `requests` 及其传递依赖包，并将当前项目自身的安装状态从虚拟模式 (virtual) 修正为可编辑模式 (editable)。

### Fixed

- **Build System**: 修复了执行 `uv sync` 时由于 `hatchling` 默认的自动发现机制无法匹配项目名 (`personal-ai-kit`) 与源码目录 (`src/ai_kit`) 所导致的构建崩溃问题。通过显式声明 wheel 目标的 `packages` 路径彻底解决了此报错。

## [0.2.0] - 2026-08-11

### Added

- **RAG Engine**: 新增 `peos-ask` 问答引擎 (`src/ai_kit/rag_engine/cli.py`)，支持通过读取本地结构化元数据进行硬过滤（预处理），并与本地 Ollama (默认 `qwen2.5:14b`) 进行高优语境推理。
- **Governance Engine**: 新增 `peos-doctor` 治理引擎 (`src/ai_kit/governance/cli.py`)，支持基于物理目录拓扑智能推断 `type` 与 `domain`，自动修复缺失 YAML Front Matter 的遗留 Markdown 资产。
- **CLI Entrypoints**: 在 `pyproject.toml` 中注册了 `promptops`, `peos-ask`, `peos-doctor` 三大全局命令行入口。

### Changed

- **Architecture**: 项目全面迁移至 Python 官方推荐的 `src-layout` 规范，实现了业务逻辑的高度模块化。
- **Project Scope**: 项目名称由 `prompt-library` 正式更名为 `personal-ai-kit`，版本号跃迁至 `v0.2.0`。
- **Contexts**: 升级 `peos-architecture.md` 至 v2.1.0，同步了 9 个顶级物理目录的拓扑规范，并明确了 `draft | active | deprecated | superseded | archived` 五大生命周期状态的语义。
- **PromptOps**: `scripts/prompt.py` 迁移至 `src/ai_kit/prompt_engine/cli.py`，并更新了对根目录相对路径的解析逻辑。

### Removed

- 删除了根目录下无实际业务逻辑的 `main.py` 占位文件。
- 移除了扁平化的 `scripts/` 目录结构。

## [0.1.1] - 2026-08-10

### Added

- **AI Profiles**: 新增 `tech-lead` 角色配置，专用于技术负责人与架构基建管理。
- **Workflows**: 新增 `project-management` 执行流，支持基于 Git Diff 自动化生成符合规范的 Commit、Changelog、README 及 ADR 资产。
- **Contexts**: 新增 `pkm-ecosystem` 上下文，引入 Diátaxis 知识库目录规范与工程管理“黄金三角”定义。
- **Aliases**: 在 `aliases.yaml` 中新增 `pkm` 快捷别名，直接绑定至 `tech-lead` 角色。

### Changed

- **Git**: 更新 `.gitignore` 规则，忽略 `repomix-*` 相关的本地 Prompt 输出文件，保持工作区纯净。

## [0.1.0] - 2026-08-07

### Added

- **Core Engine**: `scripts/prompt.py` implemented to compile, validate, and export prompts.
- **Schema**: `profile.schema.json` to enforce strict validation on profile configurations.
- **Environment**: Integrated `uv` for lightning-fast, deterministic Python environments (Python 3.12).
- **System Policies**: Added base engineering rules, response formats, and safety rules.
- **Roles**: Created personas for `java-architect`, `devops-engineer`, `cloud-native-engineer`, and `security-expert`.
- **Contexts**: Added technical environment details for Homelab infra, K3s cluster, Network mesh, Java Spring ecosystem, and Proxmox VE.
- **Workflows**: Added SOPs for architecture design, code review, playbook generation, system migration, and troubleshooting.
- **Profiles**: Added 5 ready-to-use playbooks (`ansible-engineer`, `java-architect`, `k3s-admin`, `pve-infra-migration`, `security-audit`).
