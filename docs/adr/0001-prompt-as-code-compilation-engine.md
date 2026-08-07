# ADR 0001: 采用 Prompt-as-Code 与动态编译分发架构

## 状态

已接受 (Accepted)

## 背景

随着 AI 在研发与运维工作流中的深度渗透，传统的“记事本复制粘贴”式 Prompt 管理面临严重问题：

1. **上下文碎片化**：难以维护复杂的 Homelab 与多版本 Java 混合工程背景。
2. **组合爆炸**：不同的任务（如排查 K3s 网络、编写 Ansible）需要不同的角色与底线约束组合。
3. **分发困难**：无法高效注入到 VSCode (Continue/Copilot)、Cursor、Claude Code 等多端 AI 工具中。

## 决策

我们将 Prompt 彻底作为工程化代码（Prompt-as-Code）进行管理：

1. **分层抽象**：参考 Agent 与 IaC 架构，将 Prompt 拆分为 `system`, `roles`, `contexts`, `workflows` 四层，并通过 `profiles` 进行类似 Ansible Playbook 的组合编排。
2. **强类型约束**：引入 JSON Schema (`profile.schema.json`) 在编译前对配置进行严格验证，防止配置漂移。
3. **单一事实来源引擎**：开发 Python CLI (`scripts/prompt.py`) 并在底座引入 `uv` 确保环境的一致性。引擎负责读取 Markdown、校验 YAML、组装并直接导出适配目标 IDE 的文件格式（如 `.prompts`, `.cursor/rules`, `CLAUDE.md`）。

## 结果

- **优势**：实现了一处修改、多端同步。极大提高了日常 AI 交互的信噪比，模型输出将严格对齐个人的工程底线和安全红线。
- **劣势/妥协**：增加了一定的学习成本和维护工作量，所有新增的 Prompt 必须符合 Markdown Front Matter 和 Schema 规范，不能再随意存放杂乱的文本片段。
