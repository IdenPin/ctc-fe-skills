---
name: ctc-fe-vue3
description: Use when writing, refactoring, reviewing, or generating Vue 3 single-file components with TypeScript, including component APIs, Composition API state, imports, styles, error handling, and ESLint or Prettier configuration.
---

# CTC Vue 3 与 TypeScript 规范

## 核心原则

优先保证组件 API 清晰、类型边界安全、副作用可追踪和规则可执行。代码排列服务于理解，不以形式一致性替代正确性。

## 规范等级

| 等级 | 含义 | 执行方式 |
| --- | --- | --- |
| MUST | 违反后可能造成缺陷、越界或长期维护风险 | ESLint、TypeScript、测试或明确 Review 门禁 |
| SHOULD | 团队默认做法，特定场景可说明理由后偏离 | Review |
| MAY | 可选建议 | 开发者判断 |

## SFC 组织

使用 `<script setup lang="ts">`。SFC block 默认按 `script → template → style` 排列；组件样式使用 `scoped` 或 CSS Modules，全局主题与 Reset 放在 `shared/styles`。

`script setup` 推荐按以下顺序组织，但不要为了顺序拆散强相关逻辑：

1. imports：第三方、跨层公共能力、当前模块相对路径、type-only imports。
2. component macros：`defineOptions`、`defineModel`、`defineProps`、`defineEmits`、`defineSlots`。
3. infrastructure：router、store、inject 和 composable 初始化。
4. local state：`ref`、`reactive`。
5. derived state：`computed`、`watch`、`watchEffect`。
6. methods：业务方法和事件处理器。
7. lifecycle：按组件生命周期排列。
8. public surface：仅在父组件确需命令式调用时使用 `defineExpose`。

宏顺序和 `defineExpose` 位置由 ESLint 检查；其余段落顺序属于 SHOULD，不宣称能够由现有 ESLint 规则完整强制。

## 组件 API

- MUST 使用类型声明定义 props 和 emits；事件名表达已经发生的事实或明确动作。
- MUST 保持 props 只读，禁止修改传入对象来隐式通知父组件。
- SHOULD 优先使用 props、emits 和 slots；只有确需双向绑定时使用 `defineModel`。
- SHOULD 避免无意义的 `defineExpose`。需要暴露时只公开稳定方法，不直接暴露可随意修改的内部状态。
- SHOULD 将超过一个组件复用且拥有独立状态或副作用的逻辑提取为 composable。

## TypeScript 边界

- MUST 将外部输入视为不可信边界：接口响应、JSON、路由参数、storage 和 `catch` 变量使用 `unknown` 后收窄。
- MUST 禁止无说明的 `any`。第三方类型缺失时仅允许单行豁免，并写明原因或债务编号。
- MUST 禁止用 `as Error`、双重断言或非空断言掩盖不确定性。
- SHOULD 让 TypeScript 推导局部实现类型，在组件 API、共享函数和接口边界显式声明类型。
- MAY 对对象结构使用 `interface` 或 `type`，同一模块保持一致；联合、元组和映射类型使用 `type`。不要为二者制造无业务价值的 Review 争议。

```ts
function toError(value: unknown): Error {
  return value instanceof Error ? value : new Error(String(value))
}

try {
  await saveUser()
} catch (error: unknown) {
  emit('error', toError(error))
}
```

## 响应式状态与副作用

- MUST 使用 `computed` 表达可推导状态，禁止通过 `watch` 手工同步一份重复状态。
- MUST 清理定时器、事件监听器和可取消请求，避免组件卸载后的副作用。
- MUST 处理异步竞态：搜索、分页和路由切换不得让旧请求覆盖新状态。
- SHOULD 使用 `isLoading`、`hasPermission` 等状态语义命名；事件处理器使用 `handleXxx`，异步动作使用明确动词。
- SHOULD 避免深度 watch 大对象；优先监听最小依赖或调整状态模型。

## 样式

- MUST 将组件局部样式隔离为 `scoped` 或 CSS Modules；第三方组件覆盖限制在组件根节点下并使用 `:deep()`。
- MUST 将全局主题、Reset、字体和设计 Token 放在专用全局样式入口，不在业务 SFC 中创建隐式全局样式。
- SHOULD 使用语义化 Token 表达颜色、间距和层级。品牌图形、数据可视化或一次性计算值可使用局部值，但需避免散落复制。
- SHOULD 优先使用自然布局、Flex 或 Grid；只有需求明确固定尺寸时才写死高度。

## 模块导入

- MUST 遵循 `ctc-fe-structure` 的模块边界。
- MUST 在模块内部使用相对路径，禁止通过本模块 `index.ts` 绕回内部实现。
- MUST 通过其他模块或 `shared/biz` 子域的公开 `index.ts` 跨边界使用能力，禁止深层穿透。
- SHOULD 使用 `import type` 标记纯类型依赖，并通过静态分析检测循环依赖；相对导入本身不能保证零循环依赖。

## ESLint flat config 规则片段

将以下片段合并进项目现有 `eslint.config.js` 或 `eslint.config.ts`。启用 `vue/enforce-style-attribute` 需要 `eslint-plugin-vue >= 9.20.0`。

```ts
export default [
  {
    files: ['**/*.vue'],
    rules: {
      'vue/block-order': ['error', { order: ['script', 'template', 'style'] }],
      'vue/define-macros-order': [
        'error',
        {
          order: ['defineOptions', 'defineModel', 'defineProps', 'defineEmits', 'defineSlots'],
          defineExposeLast: true
        }
      ],
      'vue/enforce-style-attribute': [
        'error',
        { allow: ['scoped', 'module'] }
      ],
      'vue/multi-word-component-names': [
        'error',
        { ignores: ['index', 'page', 'layout'] }
      ]
    }
  },
  {
    files: ['**/*.{ts,tsx,vue}'],
    rules: {
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/no-non-null-assertion': 'error',
      '@typescript-eslint/consistent-type-imports': 'error'
    }
  }
]
```

`no-explicit-any` 在迁移期使用 warn，但 CI 必须将新增 warning 视为不可增长债务；新代码只能通过带原因的局部豁免使用 `any`。

## 验证清单

按项目实际脚本执行：

```bash
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

Review 额外检查无法自动化的部分：异步竞态、错误反馈、组件 API、业务边界、可访问性和关键交互测试。
