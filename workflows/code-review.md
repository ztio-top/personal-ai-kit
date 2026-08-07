---
name: code-review
version: 1.0.0
layer: workflows
description: 代码审查流（寻找 N+1、线程安全、内存泄漏，输出优化代码）
---

# 执行流 (Workflow: Code Review SOP)

请严格按照以下 SOP 对输入的代码或配置进行审查：

## 1. 深度静态诊断

跳过简单的变量命名和缩进问题，直接扫描以下致命缺陷：

- **性能杀手**：数据库查询的 N+1 问题、全表扫描风险、大对象频繁反序列化。
- **并发与竞态**：`HashMap` 在并发下的死链、`ThreadLocal` 未清理导致的内存泄漏、锁粒度过粗、跨模块分布式锁的死锁风险。
- **架构违规**：多模块 Maven 项目中的双向依赖、打破接口隔离原则的紧耦合。

## 2. 结构化输出规范

你的输出必须严格遵循以下三段式结构：

### 🎯 核心问题 (Vulnerabilities & Bad Smells)

用一句话点透代码最核心的逻辑缺陷及触发场景。

### 🛠️ 优化机制 (Refactoring Logic)

说明修改的底层逻辑（如：“将同步的远程调用改为基于 CompletableFuture 的异步非阻塞模型，并缩小 synchronized 锁的作用域”）。

### 💻 重构后代码 (Optimized Code)

- 必须包含完整的文件路径。
- 给出优化后的代码，并加上详尽的关键逻辑注释。
