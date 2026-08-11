# Prompt Library (个人 AI 提示词资产库)

这是一个基于 **PromptOps** 理念构建的个人 AI 提示词代码化资产库。通过将 Prompt 拆分为 `System`, `Roles`, `Contexts`, `Workflows` 四个维度，并利用 Python 编译器动态组装，实现 AI 上下文的高度复用与跨 IDE 精准分发。

同时本项目是 PEOS (个人工程操作系统) 的核心控制器 (Controller)，采用现代化的 `src-layout` 架构，由三大引擎驱动：

1. **PromptOps 引擎 (`promptops`)**：负责 Prompt as Code 的动态组装与 IDE 跨端分发。
2. **RAG 引擎 (`peos-ask`)**：结合元数据预过滤技术，提供零幻觉的本地知识库问答诊断。
3. **治理引擎 (`peos-doctor`)**：自动化扫描并修复知识库元数据，保障数据层 (Model) 的架构纯洁性。

## 🏗 目录架构

- `system/`：全局工程底线与输出格式约束。
- `roles/`：AI 角色面具（如 Java 架构师、云原生工程师）。
- `contexts/`：静态环境知识库（如 Homelab 拓扑、K3s 配置、异构网络）。
- `workflows/`：标准操作流 SOP（如 Code Review 流程、故障排查流）。
- `profiles/`：组合剧本（Playbook），将上述资产编排为特定场景的执行体。
- `schemas/`：提供 JSON Schema 强类型校验。
- `scripts/`：核心编译分发引擎。

## 🚀 快速开始

本项目完全由 `uv` 托管虚拟环境与依赖。

```bash
# 1. 环境初始化
uv sync

# ==========================================
# 引擎 A: PromptOps 编译器 (指令: promptops)
# ==========================================
uv run promptops run k3s-admin
uv run promptops export cursor java-architect -t ~/workspace/my-spring-app

# ==========================================
# 引擎 B: PEOS RAG 问答机 (指令: peos-ask)
# ==========================================
# 必须先设置外部知识库环境变量
export PEOS_KNOWLEDGE_DIR="$HOME/git/[github.com/ztio-top/knowledge](https://github.com/ztio-top/knowledge)"

# 默认仅查询 type=runbook 且 status=active 的高质量资产
uv run peos-ask "K3s 节点离线怎么恢复？" -k "WireGuard"

# ==========================================
# 引擎 C: PEOS Doctor 治理机 (指令: peos-doctor)
# ==========================================
# 安全扫描 (Dry-run 模式，默认开启，仅推断并打印建议)
uv run peos-doctor

# 实际修复 (真实写入推断出的 YAML Front Matter)
uv run peos-doctor --fix

# 🤖 [高级特性] 开启 AI 智能打标 (依赖 Ollama 引擎)
# 默认请求本地 11434 端口。若 Ollama 部署在远端异构算力节点，可通过环境变量热加载配置：
export PEOS_OLLAMA_API_URL="http://192.168.3.100:11434/api/chat"

# 执行打标 (系统将自动读取上述环境变量)
uv run peos-doctor --fix --auto-tag -m "qwen2.5:14b"

# 或者在单次执行时使用 CLI 参数强制覆盖：
uv run peos-doctor --fix --auto-tag --api-url "http://vps.mydomain.com:11434/api/chat"

### 角色别名映射 (Aliases)

系统已内置以下快捷调用别名，可直接通过 CLI 唤起特定架构师角色：

| 别名 (Alias) | 对应 Profile          | 适用场景与能力                                                                                                |
| :----------- | :-------------------- | :------------------------------------------------------------------------------------------------------------ |
| `java`       | `java-architect`      | Java 后端架构设计、多 JDK 混编代码审查                                                                        |
| `k8s`        | `k3s-admin`           | 跨云 K3s 故障排查、CNI 网络诊断                                                                               |
| `ansible`    | `ansible-engineer`    | IaC 自动化部署与跨平台 Playbook 生成                                                                          |
| `pve`        | `pve-infra-migration` | Proxmox VE 底层运维与硬件直通                                                                                 |
| `sec`        | `security-audit`      | 全栈漏洞挖掘与并发安全审查                                                                                    |
| **`peos`**    | **`tech-lead`**       | **[新增] 技术负责人角色。执行工程资产自动化生成流（Commit/Changelog/ADR），并维护 Diátaxis 知识库架构规范。** |
```
