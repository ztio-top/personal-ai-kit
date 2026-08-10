# Changelog

All notable changes to this project will be documented in this file.

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
