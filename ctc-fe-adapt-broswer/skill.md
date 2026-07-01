---
name: ctc-fe-adapt-broswer
description: 为 Vite + Vue 3 + Tailwind CSS 4 项目适配老旧浏览器（奇安信信创浏览器、低版本 Chrome/Edge 等），覆盖 JS 语法降级与 CSS 现代特性兼容。适用于需要支持政企信创环境、国产浏览器、低版本 Chromium 内核浏览器的前端项目。
---

# CTC 前端浏览器兼容性适配

## When to use

- 项目需要支持奇安信可信浏览器、360安全浏览器等国产信创浏览器
- 目标用户可能使用低版本 Chrome（< 80）、Edge（< 80）、Safari（< 14）
- 构建后在老浏览器上出现 `SyntaxError: Unexpected token` 等语法错误
- 构建后页面样式丢失（Tailwind CSS 4 的 `@layer`/`@property`/`:where()` 不支持）
- 需要将 Vue 3 + Vite 项目部署到政企信创环境

## 问题背景

现代前端工具链默认构建目标为现代浏览器，产出的代码包含两层兼容性问题：

### JS 层面

Vite + ESBuild 默认产出 ES Module、可选链 `?.`、空值合并 `??`、顶层 await 等 ES2020+ 语法。老旧浏览器（Chromium < 80）无法解析，导致页面白屏、`SyntaxError`。

### CSS 层面

Tailwind CSS 4 生成大量现代 CSS 特性，Chromium 63~104 内核不支持：

| CSS 特性 | 最低支持版本 | 影响 |
|---|---|---|
| `@layer` | Chrome 99+ | `@layer base/utilities {}` 块内**所有样式被忽略** → Tailwind reset + 全部工具类丢失 |
| `@property` | Chrome 85+ | `--tw-border-style` 等自定义属性丢失初始值 → `.border`、`.shadow`、`.transform` 等失效 |
| `:where()` | Chrome 88+ | 包含该伪类的**整条规则被丢弃** → preflight reset 丢失 |
| `gap` (flex) | Chrome 84+ | flex 容器间距失效 |
| `gap` (grid) | Chrome 66+ | grid 容器间距失效 |

## 解决方案

### Part 1: JS 兼容 — @vitejs/plugin-legacy

#### 1.1 安装依赖

```bash
pnpm add -D @vitejs/plugin-legacy
# plugin-legacy 依赖 terser 进行压缩，如未安装需一并添加
pnpm add -D terser
```

#### 1.2 配置 vite.config.ts

```ts
import legacy from '@vitejs/plugin-legacy'

export default defineConfig({
  plugins: [
    // ...其他插件
    legacy({
      targets: ['Chrome >= 63', 'Edge >= 79', 'Firefox >= 67', 'Safari >= 12', 'iOS >= 12'],
      modernPolyfills: true,
    }),
  ],
  build: {
    minify: 'terser',
    terserOptions: {
      compress: { drop_console: true, drop_debugger: true },
    },
  },
})
```

#### 1.3 Targets 配置参考

| 场景 | Targets 配置 |
|---|---|
| 奇安信信创浏览器 | `['Chrome >= 63']` |
| 360安全浏览器 | `['Chrome >= 69']` |
| 通用政企环境 | `['Chrome >= 63', 'Edge >= 79', 'Firefox >= 67', 'Safari >= 12']` |

#### 1.4 产物机制

构建后自动生成双份 JS 产物：

```
index-9DWKgVv_.js          ← 现代浏览器加载（原生 ESM）
index-legacy-k4kdRLX6.js   ← 老浏览器降级加载（SystemJS + ES5 转译）
polyfills-legacy-BIhKnpPM.js  ← 按需 polyfill
```

`index.html` 通过 `<script type="module">` / `<script nomodule>` 自动分流。

### Part 2: CSS 兼容 — legacyCss.ts Vite 插件

`@vitejs/plugin-legacy` 只处理 JS，不处理 CSS。Tailwind CSS 4 生成的现代 CSS 语法需要用 PostCSS 在构建产物阶段降级。

#### 2.1 安装依赖

```bash
pnpm add -D postcss
```

#### 2.2 创建 legacyCss.ts 插件

在项目中创建 Vite 插件文件（如 `src/app/config/legacyCss.ts`），在 `generateBundle` 阶段用 PostCSS 处理所有 CSS 产物：

```ts
import type { Plugin } from 'vite'
import postcss from 'postcss'
import type { AtRule, Container, Declaration, Root, Rule } from 'postcss'

/**
 * 将 :where(X) 替换为 X，处理嵌套括号
 */
function stripWherePseudo(selector: string): string {
  let result = ''
  let i = 0
  while (i < selector.length) {
    if (selector.startsWith(':where(', i)) {
      let depth = 1
      const start = i + 7
      let j = start
      while (j < selector.length && depth > 0) {
        if (selector[j] === '(') depth++
        else if (selector[j] === ')') depth--
        if (depth > 0) j++
      }
      result += selector.slice(start, j)
      i = j + 1
    } else {
      result += selector[i]
      i++
    }
  }
  return result
}

/**
 * Vite 插件：为信创低版本浏览器处理 CSS 兼容性
 *
 * 在 generateBundle 阶段处理所有 CSS 产物，确保 Tailwind CSS 4 生成的现代 CSS 语法
 * 在 Chromium 63+ 内核浏览器上正常工作。
 *
 * 1. strip @layer: Chromium < 99 不支持 CSS @layer，整个 @layer 块内样式会被忽略
 * 2. strip @property: Chromium < 85 不支持 @property，导致 --tw-* 自定义属性丢失初始值
 * 3. strip :where(): Chromium < 88 不支持 :where()，导致包含该伪类的整条规则被丢弃
 * 4. gap fallback: Chromium < 66 (grid) / < 84 (flex) 不支持 gap 属性
 */
export function legacyCssCompat(): Plugin {
  return {
    name: 'legacy-css-compat',
    enforce: 'post',
    async generateBundle(_options, bundle) {
      for (const chunk of Object.values(bundle)) {
        if (chunk.type !== 'asset' || !chunk.fileName.endsWith('.css')) continue

        const source =
          typeof chunk.source === 'string' ? chunk.source : new TextDecoder().decode(chunk.source)

        const result = await postcss([
          // 1. strip @layer: 将 @layer name { ... } 平铺为普通规则，移除 @layer 声明
          {
            postcssPlugin: 'strip-css-layer',
            AtRule: {
              layer(node: AtRule) {
                if (node.nodes?.length) {
                  node.replaceWith(...node.nodes)
                } else {
                  node.remove()
                }
              },
            },
          },
          // 2. strip @property: 将 @property --x { initial-value: y } 转为 :root { --x: y }
          //    Chromium < 85 不支持 @property，自定义属性丢失初始值导致 .border/.shadow 等失效
          {
            postcssPlugin: 'strip-at-property',
            Once(root: Root) {
              const initialValues: Array<{ name: string; value: string }> = []
              root.walkAtRules('property', (node: AtRule) => {
                const name = node.params.trim()
                const initialDecl = node.nodes?.find(
                  (n): n is Declaration => n.type === 'decl' && n.prop === 'initial-value',
                )
                if (initialDecl) {
                  initialValues.push({ name, value: initialDecl.value })
                }
                node.remove()
              })
              if (initialValues.length === 0) return
              let rootRule = (root as Container).nodes?.find(
                (n): n is Rule => n.type === 'rule' && (n as Rule).selector === ':root',
              )
              if (!rootRule) {
                rootRule = postcss.rule({ selector: ':root' })
                root.prepend(rootRule)
              }
              for (const { name, value } of initialValues) {
                rootRule.append(postcss.decl({ prop: name, value }))
              }
            },
          },
          // 3. strip :where(): Chromium < 88 不支持 :where()，整条规则会被丢弃
          //    替换 :where(X) 为 X，恢复 preflight reset 规则
          {
            postcssPlugin: 'strip-where',
            Rule(rule: Rule) {
              if (!rule.selector.includes(':where(')) return
              rule.selector = stripWherePseudo(rule.selector)
            },
          },
          // 4. gap fallback: grid-gap 降级 + flex owl 选择器降级
          {
            postcssPlugin: 'gap-fallback',
            Rule(rule: Rule) {
              const gapDecl = rule.nodes?.find(
                (n): n is Declaration => n.type === 'decl' && n.prop === 'gap',
              )
              if (!gapDecl) return

              // grid-gap: grid 布局旧版属性名 (Chrome 57+), gap 覆盖它 (Chrome 66+)
              const hasGridGap = rule.nodes?.some(
                (n) => n.type === 'decl' && (n as Declaration).prop === 'grid-gap',
              )
              if (!hasGridGap) {
                gapDecl.cloneBefore({ prop: 'grid-gap', value: gapDecl.value })
              }

              // flex 上下文: owl 选择器降级，仅在浏览器不支持 gap 时生效
              const displayDecl = rule.nodes?.find(
                (n): n is Declaration => n.type === 'decl' && n.prop === 'display',
              )
              if (!displayDecl || !['flex', 'inline-flex'].includes(displayDecl.value)) return

              const dirDecl = rule.nodes?.find(
                (n): n is Declaration => n.type === 'decl' && n.prop === 'flex-direction',
              )
              const isColumn = dirDecl?.value.includes('column') ?? false

              // gap: <row-gap> <column-gap>?
              const values = gapDecl.value.split(/\s+/)
              const fallbackValue = isColumn ? values[0] : values[1] || values[0]

              const fallbackRule = postcss.rule({ selector: `${rule.selector} > * + *` }).append(
                postcss.decl({
                  prop: isColumn ? 'margin-top' : 'margin-left',
                  value: fallbackValue,
                }),
              )

              // 用 @supports 包裹，避免现代浏览器出现双重间距
              const atSupports = postcss.atRule({
                name: 'supports',
                params: 'not (gap: 1px)',
              })
              atSupports.append(fallbackRule)

              rule.parent?.insertAfter(rule, atSupports)
            },
          },
        ]).process(source, { from: chunk.fileName })

        chunk.source = result.css
      }
    },
  }
}
```

#### 2.3 四个 PostCSS 插件的工作原理

**① strip-css-layer** — 平铺 `@layer` 块

```
输入:                              输出:
@layer base {                      *,:after,:before { box-sizing: border-box }
  *,:after,:before { ... }        (无 @layer 包裹，规则直接暴露)
}
@layer theme, base;                (声明语句被移除)
```

**② strip-at-property** — 转换 `@property` 为 `:root` 声明

```
输入:                              输出:
@property --tw-border-style {      :root {
  syntax: "*";                       --tw-border-style: solid;
  inherits: false;                   --tw-shadow: 0 0 transparent;
  initial-value: solid;              ...
}                                  }
                                   (@property 被移除)
```

这样 `.border { border-style: var(--tw-border-style) }` 就能正确解析为 `solid`。

**③ strip-where** — 去除 `:where()` 包装

```
输入:                              输出:
:where([type=button]) {            [type=button] {
  appearance: button;                appearance: button;
}                                  }
```

`:where()` 零特性被丢弃，但对 reset 规则影响可接受。

**④ gap-fallback** — gap 双重降级

```
输入:                              输出:
.role-page {                       .role-page {
  display: flex;                     display: flex;
  flex-direction: column;            flex-direction: column;
  gap: 16px;                         grid-gap: 16px;    /* grid 降级 */
}                                    gap: 16px;
                                   }
                                   @supports not (gap: 1px) {
                                     .role-page > * + * {
                                       margin-top: 16px;  /* flex 降级 */
                                     }
                                   }
```

- `grid-gap`：grid 布局旧版属性名（Chrome 57+），`gap` 覆盖它（Chrome 66+）
- `@supports not (gap: 1px)` + owl 选择器 `> * + *`：仅在浏览器不支持 `gap` 时生效，避免现代浏览器双重间距

#### 2.4 在 vite.config.ts 中引入

```ts
import { legacyCssCompat } from './src/app/config/legacyCss'

export default defineConfig({
  plugins: [
    // ...其他插件 (vue, tailwindcss, legacy 等)
    legacyCssCompat(),  // 必须放在最后，enforce: 'post' 确保在所有插件之后执行
  ],
})
```

> **关键**：`enforce: 'post'` 确保在 Tailwind 等所有插件生成 CSS 之后，才对最终产物执行 PostCSS 转换。

### Part 3: 浏览器兼容性测试页面

建议添加一个免登录的测试页面，用于在目标浏览器中快速验证兼容性：

```vue
<!-- src/views/browser-test/index.vue -->
<script setup lang="ts">
import { ref, onMounted } from 'vue'

defineOptions({ name: 'BrowserTestView' })

const sections = ref<Section[]>([])

// 检测项：UA、存储、CSS特性、JS API、网络、图形等
// 完整实现参考项目中的 index.vue
</script>
```

在路由中注册为公开页面（无需登录）：

```ts
// src/app/router/index.ts
{
  path: '/browser-test',
  name: 'BrowserTest',
  component: () => import('@/views/browser-test/index.vue'),
  meta: { public: true, title: '浏览器兼容性测试' },
}
```

测试页面应覆盖：User Agent、localStorage/sessionStorage、CSS Grid/Flexbox/变量、Promise/fetch、WebSocket、Canvas/WebGL 等。

## 验证方式

```bash
# 1. 构建生产版本
pnpm run build

# 2. 启动 preview 服务
pnpm run preview -- --host

# 3. 用目标浏览器访问测试
# 浏览器兼容性测试页：http://<IP>:4173/browser-test
# 应用首页：http://<IP>:4173/
```

### 验证 CSS 产物

```bash
# 检查 @layer 是否已消除（应为 0）
grep -c '@layer' dist/*/assets/index-*.css

# 检查 @property 是否已消除（应为 0）
grep -c '@property' dist/*/assets/index-*.css

# 检查 :where( 是否已消除（应为 0）
grep -c ':where(' dist/*/assets/index-*.css

# 检查 grid-gap 降级是否注入
grep -o 'grid-gap' dist/*/assets/index-*.css | wc -l

# 检查 @supports gap 降级是否注入
grep -o '@supports not (gap' dist/*/assets/index-*.css | wc -l
```

## 关键要点

| 要点 | 说明 |
|---|---|
| **Dev server 不兼容** | `vite dev` 强制要求浏览器支持原生 ESM，plugin-legacy 和 legacyCss 对其无效 |
| **必须用 build 测试** | 老浏览器只能验证 `vite build` + `vite preview` 的产物 |
| **JS 双份产物** | 现代浏览器加载 `*.js`，老浏览器自动降级加载 `*-legacy.js` |
| **CSS 产物处理时机** | 必须在 `generateBundle` 阶段（`enforce: 'post'`），确保 Tailwind 等插件已生成 CSS |
| **Tailwind CSS 4 特殊性** | `@layer`/`@property`/`:where()` 是 Tailwind 4 架构核心，必须全部处理 |
| **@supports 防双重间距** | flex gap 降级用 `@supports not (gap: 1px)` 包裹，现代浏览器自动跳过 |

## 常见问题

### 信创浏览器控制台出现 `import.meta.resolve not supported` 报错？

这是 `@vitejs/plugin-legacy` 的**正常检测机制**。插件注入一段检测脚本，测试浏览器是否支持 `import.meta.resolve`（Chrome 105+）：

```js
// 检测脚本（简化）
import 'data:text/javascript,if(!import.meta.resolve)throw Error("not supported")'
window.__vite_is_modern_browser = true  // 报错后不执行
```

- 报错 → `__vite_is_modern_browser` 未设置 → 自动降级加载 legacy 产物
- **不影响功能**，应用正常运行，只是控制台有报错信息
- 插件甚至贴心地打了 `console.warn("...syntax error above...should be ignored")`

如需彻底消除报错，可设置 `renderModernChunks: false`（所有浏览器统一使用 legacy 产物，不再注入检测脚本），代价是现代浏览器也加载降级产物。

### `renderModernChunks` 是什么？

| | `true`（默认） | `false` |
|---|---|---|
| 产物 | 双份（现代 ESM + legacy） | 单份（仅 legacy） |
| 检测脚本 | 有 `import.meta.resolve` 检测 | 无 |
| 现代浏览器 | 加载原生 ESM（最优性能） | 加载 SystemJS 降级版 |
| 信创浏览器 | 降级加载（控制台有报错） | 降级加载（无报错） |
| 适用 | 用户大多为现代浏览器 | 用户大多为信创/低版本浏览器 |

### Dev 环境无法在老浏览器调试？

这是 Vite 的架构限制。开发时使用现代浏览器（Chrome 最新版），功能完成后用 `vite build` + `vite preview` 在目标浏览器验证。

### 构建后仍有语法错误？

检查：
1. 是否所有代码都经过 Vite 构建（排除外部 CDN 引入的库）
2. `targets` 配置是否覆盖了目标浏览器版本
3. 第三方库是否支持降级（部分库已放弃老浏览器）

### 构建后样式丢失？

检查 CSS 产物是否包含未处理的现代特性：
```bash
grep '@layer\|@property\|:where(' dist/*/assets/index-*.css
```
如有残留，确认 `legacyCssCompat()` 插件已正确引入且 `enforce: 'post'`。

## 相关资源

- [@vitejs/plugin-legacy 文档](https://github.com/vitejs/vite/tree/main/packages/plugin-legacy)
- [Browserslist 配置语法](https://github.com/browserslist/browserslist)
- [Can I Use](https://caniuse.com/) - 查询特性兼容性
- [PostCSS API](https://postcss.org/api/) - PostCSS 插件开发参考
