---
name: pkm-ecosystem
version: 1.0.0
layer: contexts
description: 个人知识库 (PKM) 架构与 Diátaxis 目录规范、工程黄金三角定义
---

# 架构上下文 (Context: PKM & Engineering Standards)

## 1. 知识库目录拓扑 (Diátaxis 框架)

当前知识库 (PKM) 遵循严格的物理隔离与场景分类。在输出技术资产时，必须自动将其归类到正确的目录下：

- **`handbook/` (手册/白皮书)**：对应 Explanation。存放深度原理剖析、全局架构设计。属于体系化的长文 (Long-form)。
- **`cheat/` (速查字典)**：对应 Reference。存放极简命令、高频参数速查表。要求毫无废话，即查即用。
- **`cookbooks/` (实战菜谱)**：对应 How-to Guides。存放基于具体任务或场景的步骤化指南（如“如何无宕机升级 K3s”）。
- **`notes/` (碎片笔记)**：对应 Tutorials。存放日常学习记录、每日碎片随笔。
- **`docs/` (工程基建)**：仅用于存放管理项目/知识库本身的架构体系文件（如 `adr/` 架构决策记录、`project-sop.md` 项目规范）。绝不存放具体的技术教程。

## 2. 工程管理“黄金三角” (The Golden Triangle)

- **README.md**：面向使用者。记录环境依赖、核心架构与启动命令。要求永远保持最新状态，旧指令必须无情剔除。
- **CHANGELOG.md**：面向协作者。记录历史变更 (Added, Changed, Fixed, Removed)。呈线性增长。
- **ADR (Architecture Decision Records)**：面向架构师。记录重大技术选型的背景 (Context)、决策 (Decision) 与影响 (Consequences)。其具备**不可变性 (Immutable)**，写完即归档封存。

## 3. 生成约束

- 当收到零散的代码命令请求时，默认以 `cheat/` 风格输出（极简）。
- 当收到系统化理论解释时，默认以 `handbook/` 风格输出（长文、多维度、带拓扑图）。
