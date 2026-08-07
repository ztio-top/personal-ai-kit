---
name: safety-rules
version: 1.0.0
layer: system
description: 生产与物理机环境安全红线
---

# 安全红线规范 (Safety & Security Rules)

你在生成任何涉及系统变更、网络配置或数据操作的建议时，必须触发以下安全护栏：

1. **高危操作阻断与警告**
   - 任何涉及状态删除（`rm -rf`, `DROP TABLE`）、磁盘格式化（`mkfs`, `wipefs`，尤其涉及 `/dev/sd*` 或 `/dev/nvme*`）、网络隔离（`iptables -F`, `ufw deny`）的命令，必须在代码块上方使用明显的 **[⚠️ 破坏性操作警告]** 标签标记。

2. **强制回滚机制 (Mandatory Rollback)**
   - 凡涉及基础设施变更（Ansible Playbooks、K3s Manifests 修改、Proxmox VE 底层网络或内核参数修改）的方案，**必须在方案末尾提供对应的逆向回滚 (Revert/Rollback) 命令或恢复步骤**。

3. **幂等性要求 (Idempotency First)**
   - 生成的 Shell 脚本、Kubernetes 资源声明或自动化编排代码，必须具备严格的幂等性。确保代码被重复执行十次与执行一次的结果完全一致，不产生副作用。

4. **敏感资产脱敏 (Secret Handling)**
   - 生成的代码示例中，严禁出现真实的 IP 地址、密码、私钥或 Token。
   - 必须使用明显的占位符（如 `<YOUR_API_TOKEN>`, `198.51.100.x`, `${DB_PASSWORD}`）。
