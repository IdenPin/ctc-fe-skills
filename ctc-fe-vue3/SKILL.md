---
name: ctc-fe-vue3
description: Use when writing, refactoring, reviewing, or generating Vue 3 components and TypeScript composables, including responsibility boundaries, component contracts, template rendering, reactive state, async interactions, styles and component validation.
---

# CTC Vue 3 与 TypeScript 规范

## 核心原则

优先保证组件 API 清晰、类型边界安全、副作用可追踪和规则可执行。代码排列服务于理解，不以形式一致性替代正确性。

## 职责与执行入口

本 Skill 定义组件承担什么职责、何时拆子组件或抽 composable，以及拆分后的数据流和行为契约。目录容量、文件行数、命名、文件归属和跨模块依赖统一由 `ctc-fe-structure` 定义，本 Skill 不另设数值或目录模板。

开始前读取项目规则、Vue 与工具版本、已有组件和实际验证脚本。新增文件或调整拆分时，读取项目实际安装的 `ctc-fe-structure`；单独安装本 Skill 时先定位项目现有的结构规范，缺少可读取的规范须说明结构检查未完成，不能自行编造阈值。

涉及职责拆分时，先用简短说明列出组件职责、状态所有者和 props/emits，再按下方分册执行；小改动直接按相关规则检查，无需额外生成规划文档。具体项目的组件名单、接口字段和迁移方案留在项目文档。

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
5. derived state 与 effects：`computed` 表达派生值，`watch`、`watchEffect` 处理副作用。
6. methods：业务方法和事件处理器。
7. lifecycle：按组件生命周期排列。
8. public surface：仅在父组件确需命令式调用时使用 `defineExpose`。

项目启用对应 ESLint 规则后检查宏顺序和 `defineExpose` 位置；其余段落顺序属于 SHOULD，不宣称能够由 ESLint 完整强制。宏与工具配置须匹配项目实际支持版本。

## 组件职责与拆分条件

- MUST 让组件拥有一个清晰的主要职责。多个可独立变化的交互区块混在一起时，按职责拆为私有子组件，并明确输入和事件；不要求子组件必须跨页面复用。
- SHOULD 让路由页面与入口组件承担数据协调和组件装配；有独立交互边界的区块提取为子组件，简单页面可以保持单文件。
- SHOULD 在状态流程可独立描述、跨组件复用或副作用复杂时抽取 composable；少量局部状态可以留在组件内。纯数据转换保持普通函数。
- MUST 按结构规范同时检查拆分后的文件体积、目录容量和归属；本次修改不得使原本合规的文件或目录变为超限，已有超限不得继续膨胀。存量债务按本次涉及的职责渐进处理并如实列出。
- MUST 避免机械拆分：不为每个组件配齐 `useXxx`、`types`、`data` 文件，不把整个脚本原样搬进一个巨型 composable，不通过压缩代码或随意切段规避上限。

拆分和组件封装时读取 [references/component-design.md](references/component-design.md)。

## 组件 API

- MUST 对实际使用的 props 和 emits 使用类型声明；事件名表达已经发生的事实或明确动作，无需创建空声明。
- MUST 保持 props 只读，禁止修改传入对象来隐式通知父组件。
- SHOULD 优先使用 props、emits 和 slots；只有确需双向绑定时使用 `defineModel`。
- SHOULD 避免无意义的 `defineExpose`。需要暴露时只公开稳定方法，不直接暴露可随意修改的内部状态。
- MUST 为每份状态明确所有者。跨层依赖使用有类型的注入契约，由所有者提供修改动作；包装组件明确 attrs、事件和 slots 的透传目标。

## Composable 契约

- MUST 明确输入是初始快照还是持续响应的依赖；后者通过 ref、getter 或明确的响应式对象读取，不能因传入初始值或解构而失去后续更新。
- MUST 保持默认实例隔离，返回有类型、可解释的状态与动作；返回结构应支持预期的响应式使用方式，不暴露整份内部状态供任意修改。
- MUST 管理请求、监听器和定时器的生命周期；输入变化和卸载后，旧任务不得覆盖新状态。抽取后的错误与加载状态仍应能由调用方处理。

新增或修改 composable 时读取 [references/composables.md](references/composables.md)。

## TypeScript 边界

- MUST 将外部输入视为不可信边界：原始接口响应、JSON、路由参数、storage 和 `catch` 变量使用 `unknown` 后收窄；已在边界校验的数据以明确类型传递，不在每个组件重复降回 `unknown`。
- MUST 禁止无说明的 `any`。第三方类型缺失时仅允许单行豁免，并写明原因或债务编号。
- MUST 禁止用 `as Error`、双重断言或非空断言掩盖不确定性。
- SHOULD 让 TypeScript 推导局部实现类型，在组件 API、共享函数和接口边界显式声明类型。
- MAY 对对象结构使用 `interface` 或 `type`，同一模块保持一致；联合、元组和映射类型使用 `type`。不要为二者制造无业务价值的 Review 争议。

错误处理沿用项目既有入口；未知异常的兜底转换不得再次抛错。不得在 catch 中无保护地序列化未知对象，具体规则见交互分册。

## 响应式状态与副作用

- MUST 使用 `computed` 表达可推导状态，禁止通过 `watch` 手工同步一份重复状态。
- MUST 清理定时器、事件监听器和可取消请求，避免组件卸载后的副作用。
- MUST 处理异步竞态：搜索、分页和路由切换不得让旧请求覆盖新状态。
- SHOULD 使用 `isLoading`、`hasPermission` 等状态语义命名；事件处理器使用 `handleXxx`，异步动作使用明确动词。
- SHOULD 避免深度 watch 大对象；优先监听最小依赖或调整状态模型。

## 模板与异步交互

- MUST 为有状态或可增删、重排的列表使用稳定唯一的 key，避免索引复用错误状态；同一元素不混用 `v-if` 与 `v-for`。
- MUST 保持渲染过程无请求、写存储或修改状态等副作用；复杂筛选和计算移到脚本侧，不可信 HTML 不直接交给 `v-html`。
- MUST 区分首次加载、成功空结果和失败；提供适当的恢复入口。提交期间阻止重复触发，失败后保留可重试的用户输入。
- MUST 让 loading、错误和成功反馈对应当前有效操作；取消或过期请求不能更新结果，也不能提前结束新请求的加载状态。

涉及列表、表单、请求、弹层或异步组件时读取 [references/template-interaction.md](references/template-interaction.md)。

## 样式

- MUST 将组件局部样式隔离为 `scoped` 或 CSS Modules；第三方组件覆盖限制在当前组件作用域，scoped 样式可使用 `:deep()`，CSS Modules 使用对应的局部作用域与显式全局选择器机制。
- MUST 将全局主题、Reset、字体和设计 Token 放在专用全局样式入口，不在业务 SFC 中创建隐式全局样式。
- SHOULD 使用语义化 Token 表达颜色、间距和层级。品牌图形、数据可视化或一次性计算值可使用局部值，但需避免散落复制。
- SHOULD 优先使用自然布局、Flex 或 Grid；只有需求明确固定尺寸时才写死高度。

## 导入与工具检查

- MUST 遵循 `ctc-fe-structure` 定义的路径、公开出口和依赖边界。
- MUST 使用 `import type` 标记纯类型依赖；循环依赖由项目静态分析和 Review 检查，不能仅凭使用相对路径认定不存在循环。
- 新代码的显式 `any` 默认按错误检查；迁移期豁免限定到已确认的范围，并记录原因。使用 warn 不代表 CI 会自动阻止新增债务。

调整 ESLint 或执行交付验证时读取 [references/validation.md](references/validation.md)，保留项目既有 parser、plugins 和脚本。

## 验证清单

先确认项目实际脚本，执行与改动相关的 lint、类型检查、已有测试和必要构建；新增或拆分文件时执行结构规范指定的数量与体积检查，并报告具体结果。结构扫描器的位置从实际安装的 `ctc-fe-structure` 定位，不假定工作目录。

交付前检查组件职责、状态所有权、响应式更新、异步恢复、属性透传、样式作用域和必要的键盘交互。验证输入、用户操作、渲染及事件等公开行为；测试范围随行为风险确定，不为纯配置或文案改动机械补组件测试。未执行的检查或已有失败必须如实说明。
