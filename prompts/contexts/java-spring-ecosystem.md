---
name: java-spring-ecosystem
version: 1.0.0
layer: contexts
description: Java/Maven 多模块结构、Spring Boot 规范与 JDK 混编策略
---

# 架构上下文 (Context: Java & Spring Ecosystem)

## 1. 核心工程拓扑 (Maven Multi-Module)

当前后端系统采用高度定制化的 Maven 多模块项目拓扑结构：

- **统一构建**：通过一个 Top-level (顶层) `pom.xml` 统一管理和拉起整个项目的生命周期。
- **异构 JDK 混编**：子模块按需运行在不同的 Java 环境下，项目中混合使用了 **JDK 8, JDK 17, 和 JDK 21**。
- **依赖隔离**：严禁下层基础设施模块反向依赖上层业务模块，强制通过接口层或 SPI (Service Provider Interface) 机制解耦。

## 2. Spring Boot 规范

- 默认采用最新的 Spring Boot 3.x 分支（针对 JDK 17/21 模块）。
- 优先使用 Constructor Injection（构造器注入），禁止使用 `@Autowired` 字段注入。
- 配置文件强制使用 `application.yml` 或 `application.yaml`，优先考虑按 Profile 隔离环境级配置。

## 3. 审查与修改约束

- 遇到涉及构建流的问题时，必须考虑到 Maven-Compiler-Plugin 中针对不同子模块的 `source` / `target` / `release` 参数的正确匹配，确保 JDK 8 模块不会被 JDK 21 的语法污染。
