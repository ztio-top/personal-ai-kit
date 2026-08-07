---
name: proxmox-ve
version: 1.0.0
layer: contexts
description: 宿主机 PVE 8.4 状态、RTX 3090 GPU 直通与 IOMMU 配置细节
---

# 架构上下文 (Context: Proxmox VE & Hardware Passthrough)

## 1. 宿主机环境

- **OS/版本**：Proxmox VE (PVE) 8.4。
- **核心硬件**：主力桌面/虚拟化宿主机搭载 **RTX 3090** 显卡。

## 2. GPU 直通 (PCIe Passthrough) 拓扑

- **目标虚拟机**：RTX 3090 核心算力完全直通给下游的 Ubuntu VM（主要用于异构 AI 基础设施映射）。
- **内核参数 (IOMMU)**：GRUB/systemd-boot 已配置 `intel_iommu=on iommu=pt` 开启 IOMMU 分组。
- **隔离机制**：为解决设备枚举挂起问题，宿主机的 Nouveau/Nvidia 图形驱动已被列入黑名单 (Blacklisted)，且 GPU 的 Vendor/Device ID 已被绑定至 `vfio-pci` 驱动，确保 PVE 宿主机不会占用该设备。

## 3. 运维约束

- 任何涉及 PVE 内核、PCIe 隔离或驱动黑名单的变更方案，必须提供 `update-grub` 及 `update-initramfs -u -k all` 等刷新命令。
