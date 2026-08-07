---
name: architecture-design
version: 1.0.0
layer: workflows
description: 架构设计流（方案比对、组件选型、数据流向解析）
---

# 执行流 (Workflow: Architecture Design SOP)

面对需求分析或系统设计请求，请严格按以下步骤展开推演：

## 1. 核心瓶颈与约束分析

首先明确系统面临的最大挑战是什么（是高并发写入、海量数据存储，还是强一致性要求？），明确物理环境限制（如 Homelab 的单节点显存上限、公网 VPS 的带宽延迟）。

## 2. 选型对比 (Trade-off Matrix)

必须提供至少两个备选方案，并使用 **Markdown 表格**进行对比。
对比维度必须包含：吞吐量、数据一致性 (CAP)、运维复杂度、资源开销。

> **强制要求**：明确指出每个方案的**致命缺点或局限性**。

## 3. 架构拓扑与数据流向 (Data Flow)

用清晰的文本流（或 ASCII 伪代码图）描述核心请求的流转过程：
`Client -> [Sing-box 代理] -> [WireGuard 隧道] -> [K3s Ingress] -> [Service] -> [Pod]`

## 4. 单点故障排查 (SPOF Analysis)

说明所选方案在哪个环节最容易崩溃，以及对应的容灾降级策略。
