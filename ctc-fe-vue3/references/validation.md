# Vue 规范检查与验收

## 检查能力的边界

| 约束 | 检查方式 |
| --- | --- |
| SFC 区块、宏顺序、样式属性、列表基础规则、显式 any | 项目已配置的 ESLint 规则。 |
| props、emits、注入契约、公开函数的类型 | TypeScript 与 vue-tsc；类型检查不能替代运行时输入校验。 |
| 文件行数、同级源码文件数 | `ctc-fe-structure` 提供的只读扫描器，或项目等价检查。 |
| 职责是否清晰、是否过度拆分、状态所有权 | Review。 |
| 响应式更新、用户操作、事件、异步恢复与资源清理 | 与改动风险匹配的行为测试；布局、焦点和样式需实际页面检查。 |

只执行 lint、类型检查和构建不能证明所有约束已满足。尚未配置的规则、未执行的检查以及已知失败必须分别说明，不能把建议配置描述为已落地的 CI 能力。

## ESLint 配置增量

先读取项目既有配置，确认 parser、plugins、Vue 和 ESLint 插件版本支持相关宏与选项；以下仅为规则增量，不替换整份项目配置，不自动升级依赖。

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
      'vue/enforce-style-attribute': ['error', { allow: ['scoped', 'module'] }],
      'vue/multi-word-component-names': ['error', { ignores: ['index', 'page', 'layout'] }],
      'vue/no-mutating-props': 'error',
      'vue/require-v-for-key': 'error',
      'vue/no-use-v-if-with-v-for': 'error'
    }
  },
  {
    files: ['**/*.{ts,tsx,vue}'],
    rules: {
      '@typescript-eslint/no-explicit-any': 'error',
      '@typescript-eslint/no-non-null-assertion': 'error',
      '@typescript-eslint/consistent-type-imports': 'error'
    }
  }
]
```

迁移期 any 豁免限于明确的历史范围或带原因的行级例外；新代码不能沿用全局 warn 作为放行方式。保留 warning 的项目应建立按位置和规则识别的历史基线或明确的禁止新增机制；只限制 warning 总数不能防止用消除旧 warning 抵消新增问题。

规则只提供对应语法检查；例如 props 深层对象经外部函数被修改、跨实例串状态或依赖方向错误，仍需类型设计与 Review 验证。

## 组件与 composable 行为验证

根据本次改变的公开契约选择必要用例：

- props 或输入变化后，展示、派生值与请求是否按约定更新。
- 用户操作后，是否发出正确事件或调用正确动作；双向绑定是否符合契约。
- 首次加载、空结果、失败及重试是否可区分；取消和迟到响应是否正确处理。
- 提交期间是否阻止重复动作，失败后是否保留输入；实例销毁后副作用是否清理。
- 包装组件是否保留实际支持的 attrs、事件和 slots；拆分后是否保持交互与样式。

测试优先断言用户可观察的展示、事件和状态变化，避免断言私有变量名、内部函数调用顺序或文件文本。需要检查真实组件协作时保留真实交互，不要把所有子组件都 stub 成空标签；纯文案、配置或低影响改动不机械新增一套组件测试。

## 执行与交付

1. 读取项目实际脚本，记录相关检查的已有失败；不要假定脚本一定叫 `typecheck` 或测试默认单次运行。
2. 新增或拆分文件前定位实际安装的 `ctc-fe-structure`，按其规则规划容量；已有模块先扫描基线，新模块创建后扫描。交付前再次检查并报告超限及遗留债务。
3. 执行与改动相关的 lint、类型检查、已有测试及必要构建；交互、布局或弹层行为改变时执行相应页面验收。所需用例缺失时补充有价值的行为覆盖。
4. 交付说明职责如何变化、公开接口是否变化、检查结果和剩余限制。只变更 Vue 规范时验证规范与通用示例，不夹带具体业务模块的修复或迁移计划。

结构扫描器的调用方式以已安装的结构 Skill 为准。该 Skill 不可用时先查项目既有结构规范和等价检查；无法取得时说明哪些结构约束未验证，不自行复制一套阈值。

官方参考：[ESLint 宏顺序](https://eslint.vuejs.org/rules/define-macros-order.html)、[TypeScript any 检查](https://typescript-eslint.io/rules/no-explicit-any/)、[Vue 组件测试](https://vuejs.org/guide/scaling-up/testing.html)。
