# ADR 0007: 采用 pre-commit 与 Ruff 构建极速代码质量网关

## 状态

已接受 (Accepted)

## 背景 (Context)

在 Prompt-as-Code 架构下，项目包含大量高密度的 YAML/JSON 配置文件和 Python 核心引擎代码。依赖人类开发者的自觉性或滞后的 CI/CD 流水线来发现 YAML 缩进错误、JSON 格式异常或 Python 语法坏味道，会导致修复成本直线上升。我们需要在代码进入 Git 历史树之前进行物理拦截。

## 决策 (Decision)

1. **引入 Git Hooks 拦截机制**：采用 `pre-commit` 框架，在开发者执行 `git commit` 时强制拉起本地沙箱进行全量/增量代码扫描。
2. **统一 Python 静态分析工具栈**：彻底抛弃 `flake8`、`black`、`isort` 等碎片化工具，全面拥抱 Astral 生态的 `ruff` (Rust 编写) 作为唯一的 Linter 和 Formatter，实现毫秒级验证。
3. **配置文件基线约束**：强制要求所有的 `.yaml`, `.yml`, `.json` 文件通过语法树校验，确保向 AI 智能体分发的规则资产结构绝对正确。

## 影响 (Consequences)

- **正面影响**：
  - 实现了代码质量控制的绝对左移，不合规的废代码无法污染本地 Git 历史。
  - 基于 Ruff 的超高执行性能保证了预提交卡点几乎不会造成终端开发者的等待摩擦感。
- **负面影响**：
  - 新设备初次克隆代码执行 `commit` 时，需要额外耗时拉取并构建 `pre-commit` 的隔离环境镜像。
