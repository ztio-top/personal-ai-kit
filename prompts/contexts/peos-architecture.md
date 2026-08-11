---
name: peos-architecture
version: 2.0.0
layer: contexts
description: 个人工程操作系统 (PEOS) 架构与防腐规范、SRE 与工程黄金三角定义
---

# 架构上下文 (Context: PEOS & Engineering Standards)

你当前的交互对象正在维护一个名为 PEOS (Personal Engineering Operating System) 的高阶个人架构师知识与资产系统。在输出技术文档、代码或命令时，必须严格遵守以下目录层级与规范。

## 1. 知识库目录拓扑 (PEOS 框架)

整个系统按生命周期和场景分为 8 个顶级目录（结合 PARA + Diátaxis + SRE + Zettelkasten）：

- **`1-Projects/`**: (PARA) 活跃的工程任务与短期实验（如 12 个月异构 AI 算力集群）。
- **`2-Areas/`**: (PARA) 长期关注与维护的系统领域（如家庭网络、财务）。
- **`3-Resources/`**: (Diátaxis) 核心技术域资产库。其下按具体技术领域划分（如 `kubernetes/`, `ai-ecosystem/`, `automation/`）。每个子领域内严格遵循 Diátaxis 四象限物理隔离：
  - `tutorials/` (入门教程): 面向**学习 (Learning)**。用于从零接触新技术时，带领自己建立基础认知的向导式文档。注重过程体验。
  - `how-to/` (实战指南): 面向**任务 (Task)**。存放解决具体真实问题的步骤化指南（如“如何把 Ollama 接入 WebUI”）。允许探索和试错。
  - `reference/` (参考手册): 面向**速查 (Information)**。毫无废话，存放确定的配置字典、API 规范与极简命令速查表 (Cheat Sheet)，客观严谨，即查即用。
  - `explanation/` (原理剖析): 面向**理解 (Understanding)**。深入探究底层机制、概念对比与工程规范。只解答 Why 和原理，坚决不写操作命令。
- **`4-Runbooks/`**: (SRE 应急) 生产事故 SOP。与 how-to 严格区分，这是遇到节点离线、服务崩溃时执行的“救火手册”。要求极高确定性与零认知负荷（症状->检查->恢复->验证）。
- **`5-ADR/`**: (架构决策) 存放架构决策记录。不可变资产。
- **`6-Prompts/`**: (PromptOps) 系统级 AI 提示词沉淀。
- **`7-Notes/`**: (Zettelkasten) 双链网状思考、碎片灵感与未经验证的脚本草稿。
- **`8-Archives/`**: (PARA) 已完成项目与废弃技术的归档。

## 2. 工程管理“黄金三角” (The Golden Triangle)

- **README.md** (现在)：面向使用者。记录环境依赖、核心架构与启动命令。旧指令必须无情剔除。
- **CHANGELOG.md** (过去)：面向协作者。记录历史变更 (Added, Changed, Fixed, Removed)。
- **ADR** (决策/未来)：面向架构师。记录重大技术选型的背景 (Context)、决策 (Decision) 与影响 (Consequences)。写完即归档封存，被推翻时需建立新 ADR 并将旧文件标记为 Superseded。

## 3. 生成约束与生命周期防腐层

1. **自动生命周期注入**：在生成属于 `3-Resources/` 和 `4-Runbooks/` 的 Markdown 文件时，**必须**在文件顶部包含 YAML Front Matter 头信息以防止知识腐化：
   ```yaml
   ---
   title: <精准的标题>
   type: <cheat | how-to | runbook | explanation>
   status: <draft | active | deprecated | archived>
   created: YYYY-MM-DD
   tags: [tag1, tag2]
   ---
   ```
