---
name: ai-kit-architecture
version: 1.0.0
layer: contexts
description: personal-ai-kit 全栈架构拓扑、四大逻辑域与三引擎物理边界
---

# 架构上下文 (Context: AI-Kit Architecture)

本项目是一个融合了“Prompt-as-Code”资产管理与“PEOS 知识库治理”的复合型 AI 工具链。架构严格划分为四大逻辑域：

## 1. 业务逻辑层 (Execution Layer: `src/ai_kit/`)

遵循 Python `src-layout`，三大核心引擎互为独立 Controller，严禁直接跨域导包，所有依赖与虚拟环境必须通过 `uv` 托管，入口点统一注册在 `pyproject.toml` 的 `[project.scripts]` 中。

- `prompt_engine/` (CLI: `promptops`): **PromptOps 编译器**。负责对 `prompts/` 目录进行解析，加载 profiles 的 YAML 配置，利用 JSON Schema 进行强类型校验，并剥离组装 Markdown 资产后执行多端工具（Cursor/Cline 等）的规则分发。

- `rag_engine/` (CLI: `peos-ask`): **PEOS RAG 检索机**。负责外挂知识库检索与本地 LLM 对话联动。
- `governance/` (CLI: `peos-doctor`): **Doctor 治理机**。负责知识库元数据 (Front Matter) 的清洗、推断与 AI 智能打标。

## 2. 资产控制层 (Assets Layer: `prompts/`)

这是决定 AI 行为特征的“源代码”。高度模块化，分为五层：

- `system/`: 全局底线与格式约束。
- `roles/`: 角色设定与专业视角。
- `contexts/`: 特定领域的静态架构拓扑与客观环境知识。
- `workflows/`: 面向具体任务的执行流 SOP。
- `profiles/`: 组合剧本，通过 `aliases.yaml` 映射为快捷指令。

## 3. 约束与评估层 (Validation & Evals Layer)

- `schemas/`: 提供 `profile.schema.json` 等强类型校验，防止配置漂移。
- `evals/`: 模型效果基准测试场。任何针对 Prompt 或 RAG 逻辑的重大重构，需通过该目录下的用例验证输出的信噪比与指令遵循度。

## 4. 核心工程底线

- 修改或新增 `prompts/` 资产时，必须确保纯正的 Markdown 语法，且强制保留合规的 YAML Front Matter。
- 调用本地大语言模型（如 Ollama）执行治理任务时，必须在 API 请求中强制开启 `format: json` 并设立 Python 防腐拦截层。
