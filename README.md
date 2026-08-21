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

本项目完全由 `mise` 接管底层工具链，由 `uv` 托管 Python 依赖，推荐使用 `just` 任务运行器。

```bash
# 0. 基础设施就绪 (首次 Clone 仓库时必须执行)
mise trust
mise install

# 1. 环境初始化（自动执行 uv sync 与 pre-commit 钩子注册）
just setup

# 2. 全量代码格式化与合规检查
just lint

```

### 引擎 A: PromptOps 编译器 (指令: just promptops)

```bash
# 示例: 在终端直接运行/预览 profile
just promptops run k3s-admin

# 示例: 向当前工程极速注入自维护规则 (Dogfooding 专属)
just export-rules continue
# 或针对 Cursor: just export-rules cursor

```

### 引擎 B: PEOS RAG 问答机 (指令: just ask)

```bash
# 必须先设置外部知识库环境变量
export PEOS_KNOWLEDGE_DIR="$HOME/git/[github.com/ztio-top/knowledge](https://github.com/ztio-top/knowledge)"

# 默认仅查询 type=runbook 且 status=active 的高质量资产，并可附加参数
just ask "K3s 节点离线怎么恢复？" -k "WireGuard"

```

### 引擎 C: PEOS Doctor 治理机 (指令: just doctor)

通过 `just doctor` 直接透传参数至治理引擎：

```bash
# 1. 安全扫描 (Dry-run 模式)
just doctor

# 2. 实际修复 (写入推断出的 YAML Front Matter)
just doctor --fix

# 3. 标签合规审计与净化
just doctor --audit --fix

# 4. 存量分类学智能平移
just doctor --migrate-cheatsheets --fix -m "qwen2.5:14b"

```

## 🚀 快速开始 uv 方式

```bash
# 环境初始化
uv sync
```

### 引擎 A: PromptOps 编译器 (指令: promptops)

```bash
# 示例: 在终端直接运行/预览 profile
uv run promptops run k3s-admin

# 示例: 直接输出到终端并复制 (Gemini Web 对话前置) for macOS
uv run promptops run kit | pbcopy

# 示例: 直接输出到终端并复制 (Gemini Web 对话前置) for chezmoi copy function
uv run promptops run kit | c

# 示例: 向当前目录导出 Continue 规则
uv run promptops export continue kit -t .

# 示例: 向当前目录导出 Cursor MDC 规则
uv run promptops export cursor kit -t .

# 示例: 将特定的架构师灵魂注入到业务代码仓库 (生成 .prompts 配置文件，供 Cursor/Continue 使用)
uv run promptops export cursor java-architect -t ~/workspace/my-spring-app

```

### 引擎 B: PEOS RAG 问答机 (指令: peos-ask)

```bash
# 必须先设置外部知识库环境变量
export PEOS_KNOWLEDGE_DIR="$HOME/git/[github.com/ztio-top/knowledge](https://github.com/ztio-top/knowledge)"

# 默认仅查询 type=runbook 且 status=active 的高质量资产，并可根据核心标签执行精准召回
uv run peos-ask "K3s 节点离线怎么恢复？" -k "WireGuard"

```

### 引擎 C: PEOS Doctor 治理机 (指令: peos-doctor)

`peos-doctor` 提供了覆盖全生命周期的**三梯队元数据治理能力 (3-Tier Governance)**，确保个人知识库 Front Matter 的绝对纯净与高信噪比。

#### 第一梯队：基础推断与增量补全 (Base Fix & Auto-Tag)

用于解决新文章创建时缺失 `type`、`domain` 等核心元数据，或完全没有标签的问题。

```bash
# 1. 安全扫描 (Dry-run 模式，默认开启，仅推断并打印建议)
uv run peos-doctor

# 2. 实际修复 (真实写入推断出的 YAML Front Matter)
uv run peos-doctor --fix

# 3. 🤖 [AI 增量补全] 结合 Ollama 引擎，为无标签文章执行基于 CoT（思维链）的智能打标
# 默认请求本地 11434 端口。若 Ollama 部署在远端异构算力节点，可通过环境变量热加载配置：
export PEOS_OLLAMA_API_URL="[http://192.168.3.100:11434/api/chat](http://192.168.3.100:11434/api/chat)"

# 执行智能打标
uv run peos-doctor --fix --auto-tag -m "qwen2.5:14b"

# (可选) 在单次执行时使用 CLI 参数强制覆盖 API 接口：
uv run peos-doctor --fix --auto-tag -m "qwen2.5:14b" --api-url "[http://192.168.2.7:11434/api/chat](http://192.168.2.7:11434/api/chat)"

```

#### 第二梯队：标签合规审计与字典归一化 (Tag Compliance & Normalization)

为了维护 `9-Metadata/tags.yaml` 作为唯一真实数据源（SSOT）的纯净度，支持本体别名（Alias）与大小写自动归一化。

```bash
# 1. 观察与审计（只读模式，检查全库是否存在标签漂移或未注册的野标签）
uv run peos-doctor --audit

# 2. 严格净化模式（自动完成别名归一化，并从文档中清除所有未注册的非法标签）
uv run peos-doctor --audit --fix

# 3. 演进同步模式（自动完成别名归一化，并将新发现的高价值标签自动收录进 tags.yaml）
uv run peos-doctor --audit --fix --sync-tags

```

> **⚠️ 警告（关于演进同步模式）**：
> 请慎用 `--sync-tags` 参数。由于 PyYAML 底层的序列化机制限制，自动将新标签写入 `tags.yaml` 时会导致该文件原有的**人工分类节点和注释内容被擦除或打乱**。建议使用 `--audit` 发现新标签后，人工手动维护字典。

#### 第三梯队：语义质检与冗余降噪 (Semantic Optimization)

针对历史遗留的、分配了过多泛化标签（如 `ai`, `concept`）或受代码示例污染的文档，调用大模型执行深度语义审查。大刀阔斧地将标签收敛至最核心的 1~2 个技术栈。

```bash
# 语义质检与降噪 (Dry-run 模式，仅打印裁撤优化建议)
uv run peos-doctor --optimize-tags -m "qwen2.5:14b"

# 执行真实的标签清理与无损重写
uv run peos-doctor --optimize-tags --fix -m "qwen2.5:14b"

```

#### 第四梯队：分类学智能重构 (Taxonomy Migration)

针对知识库演进过程中的分类字典裂变（例如将大而全的参考手册与轻量的速查表物理分离），利用大模型作为二元分类器，对历史资产执行无损的静默平移。

```bash
# 智能扫描存量的 reference 资产，将判定为“快捷键/Snippet”的轻量文档提取为 cheatsheet (只读/Dry-run 模式)
uv run peos-doctor --migrate-cheatsheets -m "qwen2.5:14b"

# 执行真实的分类学平移与元数据回写
uv run peos-doctor --migrate-cheatsheets --fix -m "qwen2.5:14b"
```

---

## 🎭 角色别名映射 (Aliases)

系统已内置以下快捷调用别名，可直接通过 CLI 唤起特定架构师角色进行零缝隙切换：

| 别名 (Alias) | 对应 Profile            | 适用场景与能力                                                                                  |
| ------------ | ----------------------- | ----------------------------------------------------------------------------------------------- |
| `java`       | `java-architect`        | Java 后端架构设计、多 JDK 混编环境下的代码审查与性能调优。                                      |
| `k8s`        | `k3s-admin`             | 跨云 K3s 故障排查、CNI 网络诊断、高可用集群维护。                                               |
| `ansible`    | `ansible-engineer`      | 基础设施即代码 (IaC) 自动化部署、跨平台 Playbook 生成。                                         |
| `pve`        | `pve-infra-migration`   | Proxmox VE 底层运维、网络重构与硬件/GPU 直通调优。                                              |
| `sec`        | `security-audit`        | 全栈漏洞挖掘、并发安全审查与零信任架构设计。                                                    |
| `peos`       | `tech-lead`             | 技术负责人。执行工程资产自动化生成流（Commit/Changelog/ADR），并维护 Diátaxis 知识库架构规范。  |
| **`ai-kit`** | **`ai-kit-maintainer`** | **全栈架构师。辅助 personal-ai-kit 工具链自身的三大引擎迭代、CLI 开发规范及 uv 环境基建维护。** |
