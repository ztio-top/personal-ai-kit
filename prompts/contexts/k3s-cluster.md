---
name: k3s-cluster
version: 1.0.0
layer: contexts
description: K3s 集群拓扑、节点标签、CRD 配置与 GitOps 约定
---

# 架构上下文 (Context: K3s Cluster & Orchestration)

## 1. 集群拓扑与环境

- **底层引擎**：采用 K3s 构建轻量级高可用集群，适用于 Homelab 的有限资源隔离与服务网格部署。
- **状态存储**：优先采用外挂的持久化存储，核心有状态服务（如 DB/Redis）通过明确的 Node Affinity 绑定到具备高性能存储的特定节点。

## 2. 调度与标签基线

- 默认所有应用 Pod 都应当配置合理的 Requests 和 Limits，防止 OOM 蔓延。
- 异构硬件调度：对于依赖 GPU 的负载，必须严格检查 `nodeSelector` 和 Tolerations 的匹配，确保精确调度。

## 3. 常用 CRD 与网络暴露

- **网关与路由**：优先使用 Kubernetes 标准的 Ingress 资源控制外部流量。
- **证书管理**：依赖 Cert-Manager 与 Let's Encrypt 签发和自动续期内部 TLS 证书。
- 生成 YAML 资源清单时，必须剥离不必要的系统注入字段（如 `creationTimestamp`, `uid`, `resourceVersion`），保持纯净的声明式文件。
