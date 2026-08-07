---
name: homelab-infra
version: 1.0.0
layer: contexts
description: 整体 Homelab 架构、全局变量、跨平台 IaC 与挂载路径约定
---

# 架构上下文 (Context: Homelab Infrastructure & IaC)

## 1. 异构资产清单

当前 Homelab 是一个跨平台、异构算力的混合环境：

- **Apple Silicon 节点**：M1 Max Mac Studio (运行按年份命名的现代系统，如 macOS 2026)。
- **x86 AI/虚拟化节点**：搭载 RTX 3090 的强劲桌面级宿主机，运行本地大语言模型 (Ollama / vLLM 架构)。
- **公网边界节点**：基于 Debian 13 的云端 VPS。

## 2. 基础设施即代码 (IaC) 与自动化基线

- **配置管理**：所有节点的基线均通过高度模块化的 Ansible Roles 声明式部署。
- **跨平台包管理映射**：
  - macOS 节点严格使用 Homebrew 进行依赖管理。
  - Windows 节点 (若存在) 依赖 Scoop 进行包管理。
  - Linux 节点依赖 APT，并已配置局域网或优化的镜像源。
- **终端与 Dotfiles**：高度定制化的现代终端环境，采用 Zsh, Chezmoi, Starship, uv, Mise, Atuin, 以及集成 OSC 52 剪贴板的 tmux。macOS 的窗口路由由 AeroSpace 与 Hammerspoon 联合管控。

## 3. 路径与挂载约定

<!-- - 配置脚本与自动化清单应默认放置于 `~/workspace/` 或 `~/.config/` 体系下。 -->

- 配置脚本与自动化清单应默认放置于 `~/git/` 或 `~/.config/` 体系下。
- 提供脚本时，应保证其在异构终端环境下的跨平台兼容性。
