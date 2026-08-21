# Context: Mise Runtime Infrastructure

当前开发工作站的底层运行时与工具链已完全被 `mise-en-place` (mise) 接管。在生成任何环境配置、依赖安装或构建脚本时，必须绝对遵循以下拓扑边界：

## 1. 运行时与 Shim 层机制

- **环境变量接管**：所有开发语言（Node, Python, Rust, Go 等）及全局 CLI 工具均通过 `~/.local/share/mise/shims/` 动态注入 `$PATH`。
- **绝对禁令**：严禁在任何脚本或建议中出现 `sudo apt install <dev-tool>`、`npm install -g`、`pip install --user` 或 `brew install <language>`。

## 2. 项目级依赖契约 (Project-Local Isolation)

当需要为当前项目新增运行环境或构建工具时：

- **声明式配置**：必须提供基于 `.mise.toml` 的配置片段，而非单纯的 shell 命令。
- **示例规范**：
  ```toml
  # .mise.toml
  [tools]
  python = "3.12"
  node = "22"
  "uv:black" = "latest"
  ```

* **执行入口**：所有针对项目的构建、测试或生命周期脚本，若依赖特定环境工具，建议通过 `.mise.toml` 的 `[tasks]` 节点进行封装，或提示使用 `mise run <task>` 触发。

## 3. 后端加速引擎 (Backend Engines)

- Python 包：默认且仅使用 `uv` 引擎。全局工具注入格式为 `"uv:<package-name>"`。
- Node 包：使用自带 `node` 引擎。全局工具注入格式为 `"npm:<package-name>"`。
- **防腐保障**：所有通过以上协议安装的工具均被严格隔离，不会造成宿主机污染。
