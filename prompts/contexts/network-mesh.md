---
name: network-mesh
version: 1.1.0
layer: contexts
description: Tailscale 与 WireGuard 混合组网、Netgear R7800 边缘网络、Ansible 管理的 Sing-box
---

# 架构上下文 (Context: Network Mesh & Connectivity)

## 1. 内外网连接拓扑

- **Mesh 管理网络 (Control Plane)**：个人工作站与内网基础设施采用 Tailscale 作为核心虚拟局域网，所有异构节点（Mac Studio, PVE, VPS）均注册在同一个 Tailnet 中，用于安全的运维管控。
- **K3s 跨云数据平面 (Data Plane)**：针对跨越公网部署的 K3s VPS Agent 节点，底层专门使用 **WireGuard** 构建点对点加密隧道，彻底隔离集群内部通信，确保跨数据中心容器网络 (CNI) 的低延迟与高安全性。
- **物理局域网边界**：内网核心路由设备为 Netgear R7800，该设备支持完整的 **160MHz MU-MIMO Quad-Stream Wave2 WiFi** 标准。设计局域网吞吐和无线信道时，请以此硬件上限为准。
- **公网边界代理 (VPS)**：核心云端 Debian 13 节点使用 **Sing-box** 作为边缘网络与代理核心。其配置文件、出入站路由及生命周期完全由 **Ansible** 进行声明式自动化管理，摒弃了传统的 Web 面板（如 Marzban）。

## 2. 端口与转发约定

- 各节点间的敏感服务（如 Proxmox 面板、K3s API Server、Ollama API）应默认绑定在 Tailscale 的 `100.x.y.z` 接口或 WireGuard 内网接口上，严禁直接暴露到公网 `0.0.0.0`。
- 生成的 iptables、ufw 防火墙规则或 K3s NetworkPolicy，必须同时兼容 Tailscale（如 `tailscale0`）与 WireGuard（如 `wg0`）虚拟网卡的路由转发逻辑。

## 3. 排错约束

- 分析 K3s 跨云容器网络异常时，需首先明确区分控制流（Tailscale）与集群数据流（WireGuard）的网络边界，并优先排查 WireGuard 的握手状态与 MTU 黑洞问题。
- 分析外网连通性问题时，必须优先考虑 Ansible 下发的 Sing-box 路由规则配置、系统级 DNS 劫持状态，以及 Netgear R7800 硬件转发的潜在干扰。
