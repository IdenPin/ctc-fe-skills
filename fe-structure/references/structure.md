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

无业务耦合的共享能力。

- 放：基础 UI 组件（Button、Input、Dialog wrapper）、通用高复用业务组件（`UserSelector`、`DictTag`）、通用 hooks（`useDebounce`）、原子 utils（`storage`、`tree`）。
- 不放：特定业务表单（`UserForm`）、特定业务表格（`OrderTable`）。

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
- 跨越多个一级模块大范围共用 → 放入全局 `src/shared/business-api/` 或 `src/services/platform/`。
