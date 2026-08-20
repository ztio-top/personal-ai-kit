---
name: cli-development
version: 1.0.0
layer: workflows
description: CLI 工具新增功能与跨引擎重构 SOP
---

# 执行流 (Workflow: CLI Feature Development SOP)

当需要新增 CLI 子命令或进行模块重构时，严格遵循以下步骤：

## 1. 引擎归属与边界确认

明确需求归属于 PromptOps、RAG 还是 Governance 引擎。若涉及跨引擎通用能力，优先考虑抽象为公共模块，杜绝模块间互相污染。

## 2. 契约定义与参数设计

使用标准 `argparse` 设计子命令与可选参数，确保参数命名在全工具链保持一致（例如：统一使用 `--fix` 控制只读/写入，`--dir` 控制目标路径）。

## 3. 异常处理与退出码

必须捕获可能的文件读写、网络请求及 YAML/JSON 解析异常，通过 `file=sys.stderr` 打印友好提示并以非零状态码退出。
