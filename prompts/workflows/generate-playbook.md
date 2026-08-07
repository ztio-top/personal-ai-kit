---
name: generate-playbook
version: 1.0.0
layer: workflows
description: 自动化脚本生成流（严格按照 Ansible Role 最佳实践生成代码）
---

# 执行流 (Workflow: Ansible IaC Generation SOP)

当你被要求编写或修改 Ansible Playbook/Role 时，必须输出高度规范、直接可用于生产环境的代码：

## 1. 结构与变量设计

- 优先采用 `Role` 结构（拆分 `tasks/main.yml`, `defaults/main.yml`, `handlers/main.yml`），而不是将所有代码塞进一个庞大的 Playbook 中。
- 所有的变量定义必须带有明确的 Role 前缀（如 `k3s_agent_node_ip`），严防全局变量空间污染。

## 2. 严格遵循 ansible-lint 规范

- 强制使用 FQCN (Fully Qualified Collection Names)，例如使用 `ansible.builtin.template`，绝对禁止使用短名称 `template`。
- YAML 语法中字典与列表的缩进必须严格一致，布尔值使用 `true/false`。

## 3. 幂等性与状态控制

- 能用原生模块（如 `ansible.builtin.user`, `ansible.posix.sysctl`）解决的问题，**绝对禁止**使用 `ansible.builtin.shell` 或 `ansible.builtin.command`。
- 如果万不得已必须使用 `shell/command`，则必须附加 `creates`, `removes`, 或 `changed_when: false` 等条件来保证严格的幂等性。

## 4. 文件输出结构

按照文件系统层级，依次给出对应的 YAML 文件内容，并在每个代码块首行标注完整路径（如 `roles/singbox/tasks/main.yml`）。
