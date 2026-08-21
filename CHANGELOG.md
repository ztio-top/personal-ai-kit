# Changelog

All notable changes to this project will be documented in this file.

## [0.3.6] - 2026-08-21

### Added

- **Contexts**: 新增 `mise_runtime_topology` 架构上下文，系统性确立了基于 `mise` 的开发环境与运行时隔离规范，并定义了底层防腐红线。

### Changed

- **Profiles**: 为 `ai-kit-maintainer` 和 `ansible-engineer` 角色追加挂载了 `mise_runtime_topology` 上下文。确保大模型智能体在参与工具链维护及生成 Ansible 自动化基线时，彻底抛弃传统的全局包管理命令（如 `npm -g`、`pip install`），转向严格的 `.mise.toml` 声明式生态。

## [0.3.5] - 2026-08-21

### Added

- **Governance Engine**: `peos-doctor` 脚本新增 `--migrate-cheatsheets` 第四梯队分类学重构指令。通过调用大语言模型进行二元分类，将历史存量的 `reference` 资产智能平移为轻量级的 `cheatsheet`。

### Changed

- **Contexts**: 更新 `peos-architecture.md` 提示词，使生成的 Front Matter 约束全面对齐最新版的分类学 (Taxonomy) 字典，包括软技能域与缓冲状态的声明。
- **Governance Engine**: 优化了 `cli.py` 中 `argparse` 的代码层结构，使得全局参数与不同梯队操作指令的物理边界更加清晰。

### Fixed

- **Governance Engine**: 修复了 `--migrate-cheatsheets` 命令重写 YAML 时，数组格式发生漂移的问题。通过在写入前应用 `FlowList` 拦截，确保 `tags` 始终保持单行括号格式 `[tag1, tag2]`。

## [0.3.4] - 2026-08-20

### Added

- **Profiles**: 新增 `ai-kit-maintainer` 提示词剧本，赋能大模型智能体（如 Cursor/Cline）对本项目自身进行符合架构规范的代码迭代 (Dogfooding)。
- **Contexts**: 新增 `ai-kit-architecture` 架构上下文，体系化界定了 PromptOps、RAG、Governance 三大引擎的 MVC 逻辑分离与物理防腐边界。
- **Roles**: 新增 `python-cli-architect` 角色面具，沉淀了 `argparse` 设计、JSON Schema 约束及 CLI 人机交互可观测性等最佳实践。
- **Workflows**: 新增 `cli-development` 标准执行流，为未来的跨引擎重构和新指令开发提供规范化指导。
- **Aliases**: 在 `aliases.yaml` 字典中追加注册了 `ai-kit` 别名。

## [0.3.3] - 2026-08-14

### Added

- `peos-doctor`: 正式落地第三梯队元数据治理命令 `--optimize-tags`，支持调用大模型对历史冗余标签进行基于全局语义的降噪与精简。
- `peos-doctor`: 引入细粒度的可观测性日志。在执行 LLM 推理前打印 `[AI 增量/全新打标] 正在推理分析: <file_name>`，并在 Debug 日志中透传文件上下文，大幅提升终端运行体验与排错效率。

### Changed

- `peos-doctor`: 重构打标引擎的提示词架构（Prompt Engineering）。全面弃用模糊的口语化指令，改用学术/工程化标准术语（如“全局主旨锚定”、“假阳性过滤”、“降维”），以更精准地映射模型的潜在语义空间。
- `peos-doctor`: 引入内部思维链（JSON-based CoT）机制。大模型在输出标签数组前，必须强制前置输出结构化的推理过程（主旨提炼与干扰项排除逻辑），大幅提高了 14B 级别模型在复杂上下文中的打标准确率。
- **Profiles**: Migrated `tech-lead` context dependency from `pkm-ecosystem` to `peos-architecture`.

### Fixed

- `peos-doctor`: 修复了大模型因“指令遗忘”导致输出包含非 JSON 废话而引发的正则提取失败问题。现已通过 Ollama API 层面的 `"format": "json"` 和强 System Prompt 将输出彻底锁死。
- `peos-doctor`: 修复了大模型在面对字典中不存在的具体工具（如 `head`, `grep`）时直接输出空数组的“错杀”问题，现通过本体映射（Ontology Mapping）规则引导模型自动向上抽象至通用领域（如 `cli`, `linux`）。

## [0.3.2] - 2026-08-13

### Added

- `peos-doctor`: 现已支持对已有 YAML Front Matter（但 `tags` 属性缺失或为空）的 Markdown 资产进行自动补全与无损回写。
- `peos-doctor`: 诊断报告现已集成 `⚠️ AI 打标失败/需复核` 计数与具体文件清单，提升治理过程中的可观测性。
- `peos-doctor`: 新增 `--audit` 合规审计子命令，可全局扫描并识别知识库中的标签漂移与未注册孤儿标签。
- `peos-doctor`: 新增 `--sync-tags` 演进同步参数，配合 `--audit --fix` 使用时可将新发现的优质标签自动追加注册到 `tags.yaml` 中。
- `peos-doctor`: 新增别名映射（Alias Normalization）机制，支持自动将常见简写或近义词（如 `k8s`）静默归一化为 SSOT 规范标签（如 `kubernetes`）。

### Changed

- `peos-doctor`: 优化 PyYAML 序列化行为，通过注册自定义 `FlowList` 确保所有 Front Matter 中的 `tags` 均强制以单行数组形式输出。
- `peos-doctor`: 重构 LLM 语义打标流水线，将约束规则置于 Prompt 末尾（近因效应），并采用 `re.search` 柔性提取 JSON，彻底解决大模型语法树死锁问题。
- `peos-doctor`: 升级防腐层机制，支持大小写不敏感的 SSOT 字典对齐，并自动过滤、审计大模型捏造的非注册标签。
- `peos-doctor`: 调优 LLM 通信配置，显式声明 `num_ctx: 4096`、`num_predict: -1` 且将 HTTP 请求超时时间放宽至 120 秒。
- `README.md`: 将示例命令中的推荐模型统一调整为经过验证的稳定小参数模型 `qwen2.5:14b`。
- `peos-doctor`: 深度重构语义打标 Prompt，引入“宁缺毋滥原则（Less is More）”与反泛化负向提示，杜绝大模型盲目凑数输出弱关联泛概念标签（如为命令行速查手册强行附加 `gpu` 或 `ai`）。
- `peos-doctor`: 扩展配置解析层，支持 `tags.yaml` 动态加载 `aliases` 映射字典。

## [0.3.1] - 2026-08-11

### Added

- **Governance Engine**: `peos-doctor` 现已完美支持对 PARA 架构中 `2-Areas`（长期维护领域）目录的自动化推断。默认将该目录下的演进蓝图、学习计划等资产识别为 `type: explanation` 与 `domain: pkm`，大幅降低了在非技术硬核域新建文档时的元数据维护心智负担。

## [0.3.0] - 2026-08-11

### Added

- **Governance Engine**: `peos-doctor` 脚本引入了颠覆性的 `--auto-tag` 可选参数。该功能通过调用本地大模型（默认：`qwen2.5:14b`）分析 Markdown 正文前 1000 个字符，结合 `9-Metadata/tags.yaml` 提供严格上下文约束，实现高度精确的自动化语义打标。

### Changed

- **Governance Engine**: 在执行自动推断与修复时，支持通过 `-m` 参数动态指定底层推理模型。大语言模型输出的所有标签，将被代码层的“硬拦截网”清洗，彻底终结了模型产生幻觉导致元数据污染的风险。
- **Governance Engine**: `peos-doctor` 脚本彻底移除了硬编码的 Ollama API 地址。现在支持通过全局环境变量 `PEOS_OLLAMA_API_URL` 实现地址的热重载，并提供 `--api-url` 参数以在执行时进行单次覆盖（优先于环境变量）。提高了网络拓扑改变或异地推理节点转移时的系统健壮性。

## [0.2.2] - 2026-08-11

### Changed

- **Governance Engine**: 重构了 `peos-doctor` 脚本的元数据推断逻辑。彻底废弃了会污染全局数据字典的 `general` 兜底领域。对于无法通过目录物理拓扑确定的文档，脚本将拒绝强行写入，转而高亮输出到“需手动处理队列 (Manual Intervention Queue)”。
- **Governance Engine**: 增强了特殊目录的智能推断能力。位于 `5-ADR/` 的文档将自动映射至 `architecture` 领域；位于 `7-Notes/` 下的独立笔记，其状态将被安全降级为 `draft`（防止草稿污染 RAG 生产级检索），且默认分配至 `uncategorized`（未分类）领域。

## [0.2.1] - 2026-08-11

### Changed

- **Dependencies**: 更新了 `uv.lock` 锁文件，正式锁定了 `requests` 及其传递依赖包，并将当前项目自身的安装状态从虚拟模式 (virtual) 修正为可编辑模式 (editable)。

### Fixed

- **Build System**: 修复了执行 `uv sync` 时由于 `hatchling` 默认的自动发现机制无法匹配项目名 (`personal-ai-kit`) 与源码目录 (`src/ai_kit`) 所导致的构建崩溃问题。通过显式声明 wheel 目标的 `packages` 路径彻底解决了此报错。

## [0.2.0] - 2026-08-11

### Added

- **RAG Engine**: 新增 `peos-ask` 问答引擎 (`src/ai_kit/rag_engine/cli.py`)，支持通过读取本地结构化元数据进行硬过滤（预处理），并与本地 Ollama (默认 `qwen2.5:14b`) 进行高优语境推理。
- **Governance Engine**: 新增 `peos-doctor` 治理引擎 (`src/ai_kit/governance/cli.py`)，支持基于物理目录拓扑智能推断 `type` 与 `domain`，自动修复缺失 YAML Front Matter 的遗留 Markdown 资产。
- **CLI Entrypoints**: 在 `pyproject.toml` 中注册了 `promptops`, `peos-ask`, `peos-doctor` 三大全局命令行入口。

### Changed

- **Architecture**: 项目全面迁移至 Python 官方推荐的 `src-layout` 规范，实现了业务逻辑的高度模块化。
- **Project Scope**: 项目名称由 `prompt-library` 正式更名为 `personal-ai-kit`，版本号跃迁至 `v0.2.0`。
- **Contexts**: 升级 `peos-architecture.md` 至 v2.1.0，同步了 9 个顶级物理目录的拓扑规范，并明确了 `draft | active | deprecated | superseded | archived` 五大生命周期状态的语义。
- **PromptOps**: `scripts/prompt.py` 迁移至 `src/ai_kit/prompt_engine/cli.py`，并更新了对根目录相对路径的解析逻辑。

### Removed

- 删除了根目录下无实际业务逻辑的 `main.py` 占位文件。
- 移除了扁平化的 `scripts/` 目录结构。

## [0.1.1] - 2026-08-10

### Added

- **AI Profiles**: 新增 `tech-lead` 角色配置，专用于技术负责人与架构基建管理。
- **Workflows**: 新增 `project-management` 执行流，支持基于 Git Diff 自动化生成符合规范的 Commit、Changelog、README 及 ADR 资产。
- **Contexts**: 新增 `pkm-ecosystem` 上下文，引入 Diátaxis 知识库目录规范与工程管理“黄金三角”定义。
- **Aliases**: 在 `aliases.yaml` 中新增 `pkm` 快捷别名，直接绑定至 `tech-lead` 角色。

### Changed

- **Git**: 更新 `.gitignore` 规则，忽略 `repomix-*` 相关的本地 Prompt 输出文件，保持工作区纯净。

## [0.1.0] - 2026-08-07

### Added

- **Core Engine**: `scripts/prompt.py` implemented to compile, validate, and export prompts.
- **Schema**: `profile.schema.json` to enforce strict validation on profile configurations.
- **Environment**: Integrated `uv` for lightning-fast, deterministic Python environments (Python 3.12).
- **System Policies**: Added base engineering rules, response formats, and safety rules.
- **Roles**: Created personas for `java-architect`, `devops-engineer`, `cloud-native-engineer`, and `security-expert`.
- **Contexts**: Added technical environment details for Homelab infra, K3s cluster, Network mesh, Java Spring ecosystem, and Proxmox VE.
- **Workflows**: Added SOPs for architecture design, code review, playbook generation, system migration, and troubleshooting.
- **Profiles**: Added 5 ready-to-use playbooks (`ansible-engineer`, `java-architect`, `k3s-admin`, `pve-infra-migration`, `security-audit`).
