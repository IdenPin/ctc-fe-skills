# Migration Reference

## 老项目"就近闭环"策略

当项目充满全局 `src/api/`、`src/store/` 大仓库时，切忌追求"一步到位"而发起毁灭性大重构。应当采用**局部闭环演进**：

- **第一步：原地重组** 在原页面目录（如 `src/views/system/post/`）下就地新建 `api.ts`、`types.ts`、`components/`，将散落在全局的当前模块代码集中收拢。

- **第二步：保留外壳兼容** 原全局大仓库中的历史文件不要删除，将其内容清空，改为 `re-export`，确保未改造的老代码、第三方动态菜单路由扫描不发生崩塌：

```ts
// src/api/system/post/index.ts (历史老文件位置)
export * from '#/views/system/post/api';
export type * from '#/views/system/post/types';
```

## 大小写敏感重命名专项迁移流程

在 macOS 环境下将组件从 `dict-tag.vue` 改为大驼峰 `DictTag.vue` 时，因为系统默认对大小写不敏感，必须独立成专项 PR 演进，严禁夹带业务逻辑：

1. 先冻结当前模块的业务代码合并。
2. 使用 Git 两步重命名法，强制 Git 追踪变更：

```bash
git mv dict-tag.vue dict-tag.tmp.vue
git mv dict-tag.tmp.vue DictTag.vue
```

3. 批量更新模块内部及外部的 import 语句、index.ts 以及文档示例。
4. 跑通本地验证命令。

## 验证命令与优先级

改动目录结构后，至少执行并跑通本地校验（按项目实际命令替换）：

```bash
pnpm typecheck
pnpm build
```

涉及路由、请求、局部 store 核心改造时，必须启动浏览器进行页面关键全流程手工验证。

## 迁移优先级顺序

- **优先迁移**：标准单表 CRUD 模块、文件数少、无交叉外部依赖的叶子业务模块、权限简单的模块。
- **后置迁移**：多弹窗/多路由/多状态联动模块、多业务共享 API 模块、表单复杂子组件极多的模块、框架底层基础设施（router 核心总线、request 核心适配器）。

## 架构合规度检查清单 (Checklist)

在代码评审 (Code Review) 或 AI 交付合规审计时，必须逐条勾选：

- [ ] 业务资产（页面、API、组件、hooks、store）是否已在单一模块线下闭环？
- [ ] app/ 基础设施是否足够纯净，未被任何具体业务逻辑污染？
- [ ] services/ 目录内是否只包含通用请求骨架，未混入具体业务接口定义？
- [ ] 业务接口与业务类型是否没有在全局 api/ 或 types/index.ts 中堆放？
- [ ] 全局 shared/components 中是否成功杜绝了业务组件（如 UserForm）的混入？
- [ ] 模块间是否存在直接穿透私有文件的越界引用行为？
- [ ] shared 和 services 底层基础设施是否存在反向依赖业务层代码的现象？
- [ ] 模块公开出口 (index.ts) 是否做到了精准按需导出，未滥用 export \*？
- [ ] 路由 path (kebab-case)、route name (PascalCase) 与权限码规范是否完全对齐并常量化？
- [ ] 权限码是否靠近模块记录或常量化？
- [ ] 模块私有图片、多语言文案和测试文件是否完成了就近存放？
- [ ] 环境变量是否全部收拢至配置模块，移除了散落在业务组件中的原生读取语句？
- [ ] 测试、Mock 是否跟随被测模块或业务场景？
- [ ] 文件名是否有清晰业务语义？
- [ ] 老项目是否保留兼容路径，避免一次性大爆炸？
- [ ] 路由和菜单扫描机制是否仍可工作？
- [ ] 改造完成后，pnpm typecheck 与 pnpm build 是否无 error 通过？
