---
name: system-migration
version: 1.0.0
layer: workflows
description: 迁移与升级流（数据备份、平滑替换步骤、验证方案、回滚）
---

# 执行流 (Workflow: System Migration & Upgrade SOP)

无论是要进行 JDK 升级、Proxmox VE 跨版本更新，还是 K3s 节点迁移，必须严格按照以下军规生成执行步骤：

## 1. 迁移前置检查 (Pre-flight Checks)

列出执行升级前必须确认的系统状态与依赖树（如：确认旧节点的挂载卷是否彻底解绑、目标机器内核模块是否加载）。

## 2. 数据备份策略 (Backup Strategy)

明确指示需要备份哪些核心目录、数据库 Dump 方式，或者 PVE 虚拟机/LXC 容器的快照命令。

## 3. 核心迁移步骤 (Execution Steps)

提供按顺序编号的 Shell 命令序列。
如果是高可用服务，说明如何做到 Zero-Downtime（如：K8s 的滚动更新策略配置、蓝绿部署流量切换）。

## 4. 状态校验 (Verification)

升级后，如何通过 CLI 命令（如 `systemctl status`, `kubectl get nodes -o wide`）或测试脚本验证迁移成功。

## 5. 🚑 强制回滚方案 (Rollback Plan)

**（最高优先级）** 明确写出如果迁移失败，如何通过命令行将系统状态一键还原到步骤 2 的备份点。
