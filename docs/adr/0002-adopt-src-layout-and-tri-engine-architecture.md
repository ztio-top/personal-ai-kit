# ADR 0002: 采用 src-layout 与三引擎模块化架构

## 状态

已接受 (Accepted)

## 背景

随着 PEOS 理念的成熟，原先仅用于生成 Prompt 的 `prompt-library` 脚本体系已无法满足需求。我们需要引入 RAG 检索（调用 HTTP LLM 接口）与元数据治理（知识库大批量扫描）能力。如果继续在根目录堆砌脚本，将引发严重的 Python 导包路径混乱 (sys.path 污染) 与依赖冲突。

## 决策

1. **源码隔离**：全面拥抱 Python 标准的 `src-layout`，建立 `src/ai_kit/` 命名空间，从物理上隔离业务代码与配置基建。
2. **引擎解耦**：将系统垂直拆分为 `prompt_engine`, `rag_engine`, `governance` 三个子模块，互不干扰。
3. **数据与逻辑分离 (MVC 模式)**：AI Kit 仅作为 Controller 层运行，坚决不存储任何业务知识。RAG 与 Doctor 引擎**必须**通过外部环境变量 `PEOS_KNOWLEDGE_DIR` 动态挂载数据层 (Model)。
4. **统一入口管理**：废弃直接执行 `.py` 文件的习惯，通过 `pyproject.toml` 中的 `[project.scripts]` 配置，交由 `uv` 统一注册 `promptops`, `peos-ask`, `peos-doctor` 三个命令行入口。

## 影响 (Consequences)

- **正面**：工程规范达到现代 Python CLI 工具标准；代码结构高度内聚；解耦后的 RAG 引擎可以随时与本地的 `knowledge` 仓库甚至其他目录无缝对接。借助 `uv run`，宿主机的全局环境得到了 100% 保护。
- **负面**：系统抽象层级增加，用户无法直接通过基础的 `python xxx.py` 运行程序，必须依赖 `uv` 的虚拟环境机制，或借助终端包装器 (如 Chezmoi 托管的 alias 函数) 来屏蔽长命令调用的复杂性。
