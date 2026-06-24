---
name: ctc-fe-structure
description: >
  现代前端目录结构与架构演进规范。讨论或改造 Vue、React、Vite、TypeScript、中后台、业务系统、AI 友好目录、FSD、features/shared/app/services、views/api/store/components 拆分、老项目渐进重构、新项目脚手架目录设计时必须使用。适用于判断文件该放哪里、如何划分业务模块、路由和 store 如何组织、如何让目录既方便人工开发又方便 AI 检索。
metadata:
  author: pdeng
  version: "1.0.0"
---

# FE Structure Specification
## 核心目标

建立一套通用、可渐进、AI 友好、人工开发也顺手的现代前端目录规范。

1. **业务边界清楚**：一个业务域能独立理解和修改。
2. **基础设施稳定**：router、store、request、plugins 不被业务代码污染。
3. **共享能力克制**：只有真正跨业务复用的内容进入 shared。
4. **适合 AI 检索**：一次业务修改尽量只读取一个业务目录，降低上下文污染。
5. **适合老项目迁移**：支持从 `views/api/store/components` 技术分层渐进演进。

## 先判断项目类型

- **小项目**：页面少、业务少、团队小。使用 `pages/components/services/utils` 即可。
- **中后台或业务系统**：菜单驱动、CRUD 多、后端权限/菜单可能依赖页面路径。优先使用 `views` 内业务闭环。
- **大型产品或新项目**：业务域多、长期维护、模块可能独立拆分。优先使用 `app/features/shared/services`。
- **微前端或可拆分业务**：优先把业务域放进 `features/*`。

## 推荐总结构

**新项目/大型产品：**

```text
src/
├── app/                  # 应用启动与全局配置中心
├── features/             # 高内聚业务域
├── shared/               # 纯净的、无业务耦合的共享能力
├── services/             # 外部基础设施（网络请求、第三方服务客户端）
├── layouts/              # 纯页面骨架
└── main.ts               # 应用启动入口
```

**中后台老项目渐进闭环：**

```text
src/views/<domain>/<module>/
├── index.vue             # 页面入口
├── api.ts                # 模块专属接口
├── types.ts              # 模块专属类型
├── data.ts               # 表格列、表单 Schema 配置
├── components/           # 模块私有组件
├── hooks/                # 模块局部逻辑抽象
├── store.ts              # 模块局部状态管理
└── README.md             # 模块边界文档
```

## 核心决策规则速查

| 问题 | 答案 |
| --- | --- |
| 文件该放哪里？ | 有业务语义放业务模块内，无业务语义且跨模块复用放 shared，纯请求基础设施放 services，应用级核心初始化放 app。 |
| 接口与类型如何共享？ | 遵循"最近共同业务边界"原则，严禁跨模块乱引或无脑堆入全局大仓库。 |

## 规范分册索引（按需调阅）

人工开发或 AI 检索时，请根据具体问题读取对应的 Reference 分册：

- 📌 目录拓扑、业务子模块、共享接口边界 → 读 `references/structure.md`
- 📌 文件命名、组件命名、测试与大小写敏感处理 → 读 `references/naming.md`
- 📌 单向依赖边界、公开出口、Router/Store 局部组织 → 读 `references/boundaries.md`
- 📌 老项目就近闭环策略、专项迁移流程、合规检查清单 → 读 `references/migration.md`
- 📌 资源作用域归属、i18n 就近、配置封装、模块 README 规范 → 读 `references/governance.md`

## 输出建议

当使用本 Skill 回答或规划方案时，优先给出：

1. 推荐结构
2. 为什么适合当前项目
3. 哪些目录保留，哪些目录迁移
4. 渐进迁移顺序
5. 风险点与防越界措施
6. 验证方式（Typecheck/Build）
