# Structure Reference

## 目录职责深度定义

### app

放应用级基础设施，不允许混入任何具体业务代码：

- router 实例和全局路由装配、全局路由守卫
- 全局状态（Pinia/Redux）实例初始化以及全局通用 store（如 `auth`、`theme`、`locale`、`layout`）
- 全局插件注册、引导启动逻辑 (`bootstrap.ts`)

### features

业务域闭环目录。适合长期演进的大型项目。一个业务域应该能够独立被理解、修改和迁移。

### shared

跨模块共享能力必须按语义分区，禁止把所有公共代码堆进一个 `components/` 或 `utils/`：

- `shared/ui`：Button、Input、Dialog、ValueTag 等不理解用户、订单、字典等业务概念的基础 UI。
- `shared/lib`：`useDebounce`、storage、tree 等无业务语义的 hooks 和工具。
- `shared/styles`：全局主题、Reset 和设计 Token。
- `shared/biz`：理解公司稳定业务概念、被多个独立模块长期复用的公共能力，例如用户选择和平台字典展示。

`shared/biz` 不是第二个全局大仓库。能力进入该目录必须同时满足：

1. 被多个独立业务模块长期使用，或明确属于平台级公共业务能力。
2. 对外 API 和核心交互已相对稳定，有明确维护方。
3. 不依赖 `features`、`views`、页面路由或某个模块的私有状态。
4. 不承载审批、订单、营销等具体页面流程；调用方特有规则由调用方包装。
5. 通过业务子域根目录的 `index.ts` 精确暴露公共 API。

```text
src/shared/
├── ui/
│   ├── Select/
│   └── ValueTag/
├── lib/
└── biz/
    ├── user/
    │   ├── UserSelector.vue
    │   ├── types.ts
    │   └── index.ts
    └── dictionary/
        ├── DictTag.vue
        ├── types.ts
        └── index.ts
```

例如订单审批只能选择本部门人员时，限制条件和包装组件应留在订单模块：

```text
features/order/components/ApproverSelector.vue
                         ↓
shared/biz/user/UserSelector.vue
                         ↓
shared/ui/Select.vue
```

若组件只负责根据传入的 `value + options` 显示文本和颜色，它没有字典业务语义，应命名为 `ValueTag` 并放入 `shared/ui`；只有读取公司字典编码、缓存或接口的组件才放入 `shared/biz/dictionary`。

### services

网络请求与外部服务基础设施。

- 放：request client（Axios/Fetch 实例）、Token 刷新拦截器、WebSocket/SSE 核心客户端。
- **绝对不允许放置具体业务接口定义。**

## 业务子模块治理

当一个业务模块（如 `post` 帖子、`order` 订单）规模扩大，下面包含多个稳定子业务时，**严禁使用含糊的 `modules/` 承载一切**，应按业务语义拆分二级目录：

```text
src/features/post/
├── pages/                # 父模块页面
├── api/                  # 父模块 API
├── components/           # 跨子模块复用的公共组件
├── categories/           # 二级子模块：分类管理
│   ├── pages/
│   ├── api/
│   └── components/
└── audit/                # 二级子模块：审核管理
    ├── pages/
    └── api/
```

### 子模块协同规则

1. **叫什么**：按具体业务名命名（如 category、audit），严禁使用 modules、children、sub 等泛化词汇。
2. **边界**：子模块拥有独立的页面、接口、状态时，才独立成二级目录。只服务于父模块的小表单，老老实实放在父模块 components/ 下。
3. **通信**：子模块之间禁止直接穿透交叉引用。若子模块 A 需要子模块 B 的能力，该能力必须上移至父模块公共层或 shared。

## 共享接口与共享类型边界

接口和类型应放在 "最近的共同业务边界"：

- 只给一个二级模块用 → 放入当前二级模块内部 `api.ts` / `types.ts`。
- 给同属一个一级模块的多个二级模块共用 → 放入一级模块的 `shared/api/` 或 `shared/types/` 中（例如 system 下共用部门、角色、岗位下拉接口）。
- 跨越多个一级模块且业务语义稳定 → 放入对应的 `src/shared/biz/<domain>/`。
- 仅负责 HTTP、WebSocket、鉴权头等传输机制 → 放入 `src/services/`；具体业务接口不进入 services。
