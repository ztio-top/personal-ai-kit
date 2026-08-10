---
name: project-management
version: 1.0.0
layer: workflows
description: 工程资产自动化生成流（Commit、CHANGELOG、README、ADR 联动）
---

# 执行流 (Workflow: Project Management & Assets SOP)

当遇到需要依据 Git Diff 或重构代码生成“工程资产”时，严格按照以下步骤与条件执行推理：

## 1. Git Commit Message 生成

- 严格遵循 Conventional Commits 规范（如 `feat:`, `fix:`, `refactor:`, `chore:`）。
- 第一行提供简短 Title，空一行后使用 Bullet points 描述具体改动的 Body 细节。

## 2. CHANGELOG.md 增量提取

- 从差异代码中提取对用户和系统有实质影响的变更。
- 遵循 Keep a Changelog 格式，将内容精准分配至 `### Added`, `### Changed`, `### Fixed`, 或 `### Removed`。

## 3. README.md 动态更新评估 (条件触发)

- **分析动作**：判断当前改动是否影响了系统的入口命令、核心端口、前置依赖项或架构拓扑。
- **执行分支**：
  - 若有影响：输出 README 对应章节的重写/更新代码块。
  - 若无影响：输出“**判断：未改变对外接口和核心工作流，无需更新 README。**”

## 4. ADR 架构决策判定 (条件触发)

- **分析动作**：深度扫描变更，判断是否引入了新中间件、抛弃了关键技术栈、或改变了系统原本的数据流转方式（如从 TCP 变更为 UDP，从单机变更为集群）。
- **执行分支**：
  - 若属于架构分水岭：输出标准三段式 ADR（Context, Decision, Consequences）雏形，并提示保存至 `docs/adr/`。
  - 若仅是局部重构或功能迭代：输出“**判断：未涉及全局重大技术决策，无需编写 ADR。**”
