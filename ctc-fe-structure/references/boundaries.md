# Boundaries Reference

## 层级依赖单向边界

目录分层必须配合严格的依赖架构治理，否则极易演变为"披着分层外衣的乱引大杂烩"。

**标准单向依赖关系：**

```text
app ───────────────→ features / views
                         ├──→ shared/biz ──→ shared/ui | shared/lib
                         │          └──────→ services
                         ├──→ shared/ui | shared/lib
                         └──→ services
```

- **禁止反向依赖**：`shared` 和 `services` 处于底层，禁止反向引用业务模块（`features` 或 `views`）中的组件、页面、路由或状态。
- **biz 单向依赖**：`shared/biz` 可以依赖 `shared/ui`、`shared/lib` 和 `services`，但 `shared/ui|lib` 不得反向理解或引用 `shared/biz`。
- **禁止深层穿透**：业务模块之间禁止相互直接引透入对方的私有深层路径。不推荐：`import { useOrderGrid } from '@/features/order/hooks/useOrderGrid'`。
- **纠正措施**：跨业务复用能力，优先走"最近共同边界"或上移至 `shared`。

## 依赖越界工具化校验与逃生通道

为了防止依赖规范成为一纸空文，我们采用静态分析工具在开发和提交阶段进行强制性（Hard Constraint）硬拦截。

### 1. 工具链约束
我们集成 `eslint-plugin-import-x` 插件，并使用 `import-x/no-restricted-paths` 规则在 `eslint.config.ts` 中声明。一旦开发人员在编辑器中写出违背架构单向依赖的代码，IDE 将实时标红并阻止保存与提交。

### 2. 跨业务域引用的三级逃生机制
如果在实际开发中，确实面临需要引用另一个业务模块内容的情况，严禁直接删改 ESLint 拦截规则。团队成员必须且仅能按照以下三个梯度依次权衡处理：

* **【第一级：走安全沙箱正门】**
  * **场景**：逻辑仅在该两个业务域之间有耦合，无需对全站公开。
  * **做法**：在被引用模块的根入口（如 `views/login/index.ts`）显式 `export` 出来；引用模块必须直接引用对方的根路径 `import { XXX } from '../login'`，绝对禁止穿透引用其私有深层路径（如 `../login/components/Avatar.vue`）。
* **【第二级：下沉全局公共库】**
  * **场景**：该能力被多个独立业务域长期使用，API 已稳定，并且有明确维护方。
  * **做法**：无业务语义能力下沉至 `shared/ui|lib`；稳定业务公共能力下沉至 `shared/biz/<domain>`。具体业务接口跟随 `shared/biz` 子域，`services` 只提供请求基础设施。
* **【第三级：临时行级豁免通道】**
  * **场景**：紧急发版上线、或者由于复杂的历史债务重构难度极大，需快速放行。
  * **做法**：使用行级忽略注释对特定的越界依赖进行显式局部标记，保留有案可查的豁免：
    ```typescript
    // eslint-disable-next-line import-x/no-restricted-paths
    import LegacyAvatar from '../login/components/Avatar.vue'
    ```

## 模块公开出口规范 (`index.ts`)

一个业务域（Feature）可以通过根目录的 `index.ts` 建立"安全沙箱边界"，对外暴露**极其克制**的公开能力。

- **严禁无脑使用通配符**：禁止 `export * from './components'`，这会导致沙箱内部私有弹窗和组件全部泄露。
- **必须精准导出**：

```ts
export { useUserStore } from './store';
export { getUserPage } from './api/userApi';
export type { User, UserQuery } from './types/model';
```

### 模块内引用原则

模块内部各文件之间协同，优先使用相对路径相对引用，绝对不允许绕出模块到自己的 index.ts 门口再绕引回来，这会引发严重的循环依赖（Circular Dependencies）。

`shared/biz/<domain>` 同样遵循公开出口规则。业务模块只能从其 `index.ts` 使用稳定能力，不得穿透其内部 API、store 或组件实现。

## Router & Store 组织边界

### Router

`app/router` 是路由总线和入口，不是手写长城。各个业务模块在自己内部维护独立的 `routes.ts`，总线通过手动显式聚合或利用 Vite 的 `import.meta.glob` 自动动态扫描装配。

- 路由 path 使用 `kebab-case`（如 `/system/user-profile`）；route name 使用 `PascalCase`（如 `SystemUserProfile`）。
- 权限码使用 `业务域:资源:动作`（如 `system:user:create`）。
- 权限码集中写在模块 `permissions.ts` 或 README 中说明。

### Store

`app/store` 仅负责 Pinia/Redux 实例化和全局级状态。业务状态（如表格筛选参数、向导步骤缓存）必须作为局部状态随业务域闭环（如 `features/user/store.ts`），Pinia Setup Store 无需全局注册，就近随用随引。
