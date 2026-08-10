# Prompt Library (个人 AI 提示词资产库)

这是一个基于 **PromptOps** 理念构建的个人 AI 提示词代码化资产库。通过将 Prompt 拆分为 `System`, `Roles`, `Contexts`, `Workflows` 四个维度，并利用 Python 编译器动态组装，实现 AI 上下文的高度复用与跨 IDE 精准分发。

## 🏗 目录架构

- `system/`：全局工程底线与输出格式约束。
- `roles/`：AI 角色面具（如 Java 架构师、云原生工程师）。
- `contexts/`：静态环境知识库（如 Homelab 拓扑、K3s 配置、异构网络）。
- `workflows/`：标准操作流 SOP（如 Code Review 流程、故障排查流）。
- `profiles/`：组合剧本（Playbook），将上述资产编排为特定场景的执行体。
- `schemas/`：提供 JSON Schema 强类型校验。
- `scripts/`：核心编译分发引擎。

## 🚀 快速开始

本项目由 `uv` 进行环境管理。

```bash
# 1. 环境初始化
uv sync

# 2. 编译并输出到终端 (用于管道调用或本地 LLM)
uv run scripts/prompt.py run k3s-admin

# 3. 静态编译至 build 目录
uv run scripts/prompt.py compile java-architect

# 4. 定向注入到目标 IDE/工具 (如 Continue, Cursor, Claude Code)
uv run scripts/prompt.py export continue java-architect -t ~/workspace/my-spring-app

```

### 角色别名映射 (Aliases)

系统已内置以下快捷调用别名，可直接通过 CLI 唤起特定架构师角色：

| 别名 (Alias) | 对应 Profile          | 适用场景与能力                                                                                                |
| :----------- | :-------------------- | :------------------------------------------------------------------------------------------------------------ |
| `java`       | `java-architect`      | Java 后端架构设计、多 JDK 混编代码审查                                                                        |
| `k8s`        | `k3s-admin`           | 跨云 K3s 故障排查、CNI 网络诊断                                                                               |
| `ansible`    | `ansible-engineer`    | IaC 自动化部署与跨平台 Playbook 生成                                                                          |
| `pve`        | `pve-infra-migration` | Proxmox VE 底层运维与硬件直通                                                                                 |
| `sec`        | `security-audit`      | 全栈漏洞挖掘与并发安全审查                                                                                    |
| **`pkm`**    | **`tech-lead`**       | **[新增] 技术负责人角色。执行工程资产自动化生成流（Commit/Changelog/ADR），并维护 Diátaxis 知识库架构规范。** |
