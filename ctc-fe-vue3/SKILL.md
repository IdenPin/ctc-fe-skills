---
name: ctc-fe-vue3
description: >
  现代 Vue 3、TypeScript 与 CSS 编写风格与代码规范。规范了 <script setup> 声明顺序、TypeScript 强类型边界、就近样式、防循环依赖以及静态工具链（ESLint/Prettier）校验规则。适用于日常开发、架构评审 and AI 代码生成时的风格约束。
---

# FE Vue 3 Style & Best Practices

## 核心目标

建立一套高可读性、高健壮性、且对 AI 极度友好的 Vue 3 代码编写风格规范。

1. **结构一致性**：统一组件内部代码组织顺序，降低跨模块理解难度。
2. **TS 类型安全**：拒绝 `any` 与非安全断言，发挥静态类型系统的最大价值。
3. **就近样式隔离**：杜绝全局污染与死代码，实现组件样式的物理隔离。
4. **零循环依赖**：规范内部导入路径，从编码阶段根绝打包循环依赖问题。

---

## 1. 适用场景 (When to Use)

- 编写、重构或评审 Vue 3 + TypeScript 业务组件或公共组件时。
- 需要规范团队代码格式、TS 类型安全、样式域隔离、消除循环依赖时。
- 引导 AI 助手生成符合项目最高标准的 Vue 3 组件代码时。

---

## 2. `<script setup>` 组件内部声明顺序

为了保持组件代码结构的清晰可预测，所有单文件组件（SFC）的 `<script setup>` 必须严格遵循以下 **8 段式声明顺序**。各段落之间使用空行分隔：

```vue
<script setup lang="ts">
// ----------------------------------------------------
// 1. Imports (依赖导入)
// 先外部依赖库，再 shared 全局基础设施，最后本地局部文件
// ----------------------------------------------------
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { CommonButton } from '@/shared/components'
import { useUserStore } from '../store'
import { getUserDetailApi } from '../api'
import type { UserDetail } from '../types'

// ----------------------------------------------------
// 2. Component Macros (组件宏定义)
// 必须且仅允许使用编译时宏定义 Props, Emits 等，统一使用 TS 类型定义
// ----------------------------------------------------
interface Props {
  userId: string
  theme?: 'dark' | 'light'
}
const props = withDefaults(defineProps<Props>(), {
  theme: 'light'
})

const emit = defineEmits<{
  (e: 'success', data: UserDetail): void
  (e: 'error', error: Error): void
}>()

defineOptions({
  name: 'UserCardDetail'
})

// ----------------------------------------------------
// 3. Reactive State (响应式状态声明)
// ref, reactive 声明，变量名采用驼峰，布尔值推荐 is/has 前缀
// ----------------------------------------------------
const userDetail = ref<UserDetail | null>(null)
const isLoading = ref(false)

// ----------------------------------------------------
// 4. Computed & Watchers (计算属性与侦听器)
// 先 Computed 后 Watchers，保证副作用逻辑就近
// ----------------------------------------------------
const displayName = computed(() => {
  return userDetail.value ? `${userDetail.value.firstName} ${userDetail.value.lastName}` : ''
})

// ----------------------------------------------------
// 5. Stores & Routes (全局/局部基础设施初始化)
// 统一就近获取 store 和 route，避免与业务状态混淆
// ----------------------------------------------------
const route = useRoute()
const userStore = useUserStore()

// ----------------------------------------------------
// 6. Methods & Event Handlers (业务逻辑与事件处理器)
// 函数命名具有清晰的动作语义，采用小驼峰
// ----------------------------------------------------
async function fetchUserDetail(id: string) {
  isLoading.value = true
  try {
    const res = await getUserDetailApi(id)
    userDetail.value = res.data
    emit('success', res.data)
  } catch (error) {
    emit('error', error as Error)
  } finally {
    isLoading.value = false
  }
}

function handleRefresh() {
  fetchUserDetail(props.userId)
}

// ----------------------------------------------------
// 7. Lifecycle Hooks (生命周期钩子)
// 按执行顺序从上到下排列
// ----------------------------------------------------
onMounted(() => {
  if (props.userId) {
    fetchUserDetail(props.userId)
  }
})

// ----------------------------------------------------
// 8. Expose (对外暴露)
// 必须精确限定外部父组件能够通过 ref 访问的属性或方法
// ----------------------------------------------------
defineExpose({
  refresh: handleRefresh,
  isLoading
})
</script>
```

---

## 3. TypeScript 编码规范

### 3.1 妥善处理 `any` 与非安全类型（新人友好过渡）
- **软限制 `any`**：在日常业务开发中，允许使用 `any` 快速跑通逻辑，但 ESLint 会以 **Warn**（黄色警告）在 IDE 中提示。建议在熟悉类型后逐步用具体类型或 `unknown`（配合类型收窄）代替。
- **局部逃生通道**：在确实无法取得 TS 定义或复杂的第三方库场景下，如必须使用 `any`，**必须**使用单行注释进行局部豁免，避免全局规则失效：
  ```typescript
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const rawData: any = await getLegacyApi()
  ```
- **避免非空断言 `!`**：禁止随意使用 `data!.name`，优先使用可选链 `data?.name` 与空值合并 `data?.name ?? 'Default'`。
- **强制使用 `as` 替代 `<Type>` 进行断言**：避免在 TSX / JSX 中产生标签解析冲突。

### 3.2 Type 与 Interface 的职责划分
- **使用 `interface`**：
  - 定义组件 Props、Emits。
  - 定义后端 API 返回的数据实体结构。
  - 定义具有可扩展性、需要被继承或声明合并（Declaration Merging）的公共对象结构。
- **使用 `type`**：
  - 定义联合类型（如 `type Theme = 'light' | 'dark'`）。
  - 定义交叉类型、元组、函数签名。
  - 定义只读或临时泛型别名。

---

## 4. 局部样式与作用域治理

### 4.1 样式作用域物理隔离
- **强制 scoped**：除全局主题（`src/shared/styles`）外，所有组件的 `<style>` 标签必须声明 `scoped`：
  ```vue
  <style scoped>
  .user-card-container {
    padding: 16px;
  }
  </style>
  ```
- **禁止在局部组件修改全局样式**：禁止在局部组件中使用不加 scoped 的全局 `<style>` 来覆写第三方组件库（如 Element Plus、Ant Design Vue），如需覆盖必须使用 `:deep()` 伪类：
  ```css
  /* 推荐写法 */
  .user-card-container :deep(.el-button) {
    border-radius: 8px;
  }
  ```

### 4.2 消除硬编码颜色与尺寸
- **禁止硬编码颜色**：禁止在 CSS 中写死特定十六进制颜色值（如 `#333333`、`#409eff`），必须使用全局 CSS 变量或 Tailwind 语义化 Token（如 `var(--color-text-primary)`）。
- **尺寸弹性**：避免写死容器的高度，优先使用 Flexbox / Grid 自适应或 `min-height` / `max-height`。

---

## 5. 引入规范与零循环依赖

### 5.1 模块内部就近相对引入
- **禁止向外绕行**：在同一个模块（如 `features/user/`）内部，文件之间的引用**必须优先使用相对路径**（如 `./components/Avatar.vue`），绝对禁止绕行至模块大门口的 `index.ts` 导出层再引回来（如 `@/features/user`），这会引发打包时的**循环依赖**。
- **跨模块规范引用**：若需使用其他模块的能力，必须且仅能通过对方模块的 `index.ts` 安全沙箱接口引入，禁止穿透对方的私有深层目录。

---

## 6. 自动化工具链配置推荐

为了让以上规范强制生效，建议在项目中集成以下配置规则：

### 6.1 ESLint 关键配置规则 (`eslint.config.js`)
```javascript
module.exports = {
  rules: {
    // 强制 Vue 3 单文件组件的宏和生命周期声明顺序
    'vue/define-macros-order': ['error', {
      order: ['defineProps', 'defineEmits', 'defineOptions', 'defineSlots']
    }],
    // 强制组件内部的 script, template, style 标签排序（已更新为最新 block-order 规则）
    'vue/block-order': ['error', {
      order: ['script', 'template', 'style']
    }],
    // 限制 any 滥用（降级为 warn 以免阻断新人编译，保留 IDE 警告提示）
    '@typescript-eslint/no-explicit-any': 'warn',
    // 限制 non-null 断言
    '@typescript-eslint/no-non-null-assertion': 'warn',
    // 强限制组件名必须为大驼峰且为多单词（页面入口除外）
    'vue/multi-word-component-names': ['error', {
      ignores: ['index', 'page', 'layout']
    }]
  }
}
```

### 6.2 Prettier 基础配置 (`.prettierrc`)
```json
{
  "semi": false,
  "singleQuote": true,
  "tabWidth": 2,
  "useTabs": false,
  "printWidth": 100,
  "trailingComma": "none",
  "bracketSpacing": true,
  "arrowParens": "avoid"
}
```
