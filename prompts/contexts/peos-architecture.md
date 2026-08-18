---
name: peos-architecture
version: 2.1.0
layer: contexts
description: 个人工程操作系统 (PEOS) 架构与防腐规范、SRE 与工程黄金三角定义
---

# 架构上下文 (Context: PEOS & Engineering Standards)

你当前的交互对象正在维护一个名为 PEOS (Personal Engineering Operating System) 的高阶个人架构师知识与资产系统。

## 1. 知识库目录拓扑 (PEOS 框架)

整个系统按生命周期和场景分为 8 个顶级目录（结合 PARA + Diátaxis + SRE + Zettelkasten）：

- **`1-Projects/`**: (PARA) 活跃的工程任务。
- **`2-Areas/`**: (PARA) 长期关注领域。
- **`3-Resources/`**: (Diátaxis) 核心技术域资产。每个子领域严格区分为 `tutorials/` (学习), `how-to/` (任务), `reference/` (速查), `explanation/` (原理)。若新内容无法划分到现有子领域，请创建一个范围不能太局限的子领域。
  - 已有子领域：
    - ai-ecosystem
    - automation
    - containers
    - databases
    - editors
    - engineering-standards
    - java-ecosystem
    - kubernetes
    - middleware
    - modern-cli
    - os-network
    - package-managers
    - proxy
    - terminals
    - web-dev
  - 每个子领域内严格遵循 Diátaxis 四象限物理隔离：
    - `tutorials/` (入门教程): 面向**学习 (Learning)**。用于从零接触新技术时，带领自己建立基础认知的向导式文档。注重过程体验。
    - `how-to/` (实战指南): 面向**任务 (Task)**。存放解决具体真实问题的步骤化指南（如“如何把 Ollama 接入 WebUI”）。允许探索和试错。
    - `reference/` (参考手册): 面向**速查 (Information)**。毫无废话，存放确定的配置字典、API 规范与极简命令速查表 (Cheat Sheet)，客观严谨，即查即用。
    - `explanation/` (原理剖析): 面向**理解 (Understanding)**。深入探究底层机制、概念对比与工程规范。只解答 Why 和原理，坚决不写操作命令。
- **`4-Runbooks/`**: (SRE 应急) 生产事故 SOP，要求极高确定性与零认知负荷。
- **`5-ADR/`**: (架构决策) 架构决策记录，不可变资产。
- **`6-Templates/`**: (标准模板) 存放各类 Markdown SOP 模板及 Front Matter 规范。
- **`7-Notes/`**: (Zettelkasten) 双链网状思考草稿。
- **`8-Archives/`**: (PARA) 废弃技术的归档。
- **`9-Metadata/`**: (元数据) 存放 Taxonomy 分类学字典与全局标签，用于大模型 RAG 预过滤约束。

## 2. 生成约束与生命周期防腐层

生成的 Markdown 文件**必须**在顶部包含 YAML Front Matter 头信息以防止知识腐化。必须严格使用以下枚举值：

```yaml
---
title: <精准的标题>
type: <runbook | adr | how-to | reference | explanation | tutorial | note>
# 状态枚举与语义：
# draft: 构思中草稿 / active: 生产可用 / deprecated: 运行中但不推荐 / superseded: 被新方案取代的旧方案 / archived: 彻底废弃
status: <draft | active | deprecated | superseded | archived>
created: YYYY-MM-DD
tags: [tag1, tag2]
---
```
