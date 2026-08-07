---
name: troubleshooting
version: 1.0.0
layer: workflows
description: 故障排查流（从 Error Log 倒推根因，提供排查命令清单）
---

# 执行流 (Workflow: Troubleshooting & Root Cause Analysis SOP)

当提供给你错误日志（Error Log）、崩溃堆栈或网络不通的现象时，执行以下排错流：

## 1. 堆栈解析与降噪

剥离无用的中间件代理层异常，直接指出堆栈最底层的 Root Cause（如：某一行引发的 `NullPointerException`，或底层 `Connection reset by peer`）。

## 2. 根因假设 (Hypothesis)

列出引发该问题的 1-3 个最有可能的原因。如果是网络问题，必须结合 Tailscale/WireGuard 覆盖网、K3s CNI 路由栈进行多维度推测。

## 3. 诊断命令矩阵 (Diagnostic Commands)

**不要直接猜结论，先给出排查手段。** 提供可以直接在终端执行的诊断命令清单，并注明每条命令的预期输出。
_示例：_

- 查网络：`tcpdump -i wg0 port 6443 -n`
- 查集群：`kubectl describe pod <pod-name> -n <namespace>`
- 查宿主机：`journalctl -u k3s --no-pager -n 50`

## 4. 修复与恢复动作 (Mitigation & Fix)

给出临时止血方案（如重启挂载、封锁流量）和长期修复代码/配置。
