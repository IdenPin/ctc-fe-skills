# legacyCss.ts 兼容插件源码与原理解析

### 1. legacyCss.ts 完整源码

在前端项目中创建 Vite 插件文件（如 `src/app/config/legacyCss.ts`），在 `generateBundle` 阶段用 PostCSS 处理所有 CSS 产物：

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
 * 4. gap fallback: 基于 CSS 变量继承的通用 Flex Gap Polyfill (针对 Chromium < 84 不支持 flex gap)
 */
export function legacyCssCompat(): Plugin {
  return {
    name: 'legacy-css-compat',
    enforce: 'post',
    transformIndexHtml(html) {
      const detectScript = `
<script>
(function(){
  try {
    var flex = document.createElement('div');
    flex.style.display = 'flex';
    flex.style.flexDirection = 'column';
    flex.style.rowGap = '1px';
    flex.style.height = 'auto';
    flex.style.padding = '0px';
    flex.style.margin = '0px';
    flex.style.border = 'none';

    var child1 = document.createElement('div');
    child1.style.height = '0px';
    child1.style.padding = '0px';
    child1.style.margin = '0px';
    child1.style.border = 'none';

    var child2 = document.createElement('div');
    child2.style.height = '0px';
    child2.style.padding = '0px';
    child2.style.margin = '0px';
    child2.style.border = 'none';

    flex.appendChild(child1);
    flex.appendChild(child2);
    document.documentElement.appendChild(flex);
    var isSupported = flex.scrollHeight === 1;
    document.documentElement.removeChild(flex);
    if (!isSupported) {
      document.documentElement.classList.add('no-flex-gap');
    }
  } catch (e) {
    console.warn('Failed to detect flex gap compatibility', e);
  }
})();
</script>
      `
      return html.replace('<head>', '<head>\\n' + detectScript.trim())
    },
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
          // 4. gap fallback: 升级为基于 CSS 变量继承的通用 Flex Gap Polyfill (针对低版本信创浏览器)
          {
            postcssPlugin: 'gap-fallback',
            OnceExit(root: Root) {
              // 全局注入通用的 owl 降级样式规则
              const globalRules = [
                postcss.rule({ selector: '.no-flex-gap .flex > * + *, .no-flex-gap .inline-flex > * + *' }).append(
                  postcss.decl({ prop: 'margin-left', value: 'var(--flex-gap-x, 0px)' }),
                  postcss.decl({ prop: 'margin-top', value: '0px' }),
                  postcss.decl({ prop: 'margin-right', value: '0px' }),
                  postcss.decl({ prop: 'margin-bottom', value: '0px' })
                ),
                postcss.rule({ selector: '.no-flex-gap .flex-row-reverse > * + *' }).append(
                  postcss.decl({ prop: 'margin-right', value: 'var(--flex-gap-x, 0px)' }),
                  postcss.decl({ prop: 'margin-left', value: '0px' }),
                  postcss.decl({ prop: 'margin-top', value: '0px' }),
                  postcss.decl({ prop: 'margin-bottom', value: '0px' })
                ),
                postcss.rule({ selector: '.no-flex-gap .flex-col > * + *' }).append(
                  postcss.decl({ prop: 'margin-top', value: 'var(--flex-gap-y, 0px)' }),
                  postcss.decl({ prop: 'margin-left', value: '0px' }),
                  postcss.decl({ prop: 'margin-right', value: '0px' }),
                  postcss.decl({ prop: 'margin-bottom', value: '0px' })
                ),
                postcss.rule({ selector: '.no-flex-gap .flex-col-reverse > * + *' }).append(
                  postcss.decl({ prop: 'margin-bottom', value: 'var(--flex-gap-y, 0px)' }),
                  postcss.decl({ prop: 'margin-left', value: '0px' }),
                  postcss.decl({ prop: 'margin-right', value: '0px' }),
                  postcss.decl({ prop: 'margin-top', value: '0px' })
                )
              ]
              root.append(...globalRules)
            },
            Rule(rule: Rule) {
              const gapDecl = rule.nodes?.find(
                (n): n is Declaration => n.type === 'decl' && n.prop === 'gap',
              )
              const rowGapDecl = rule.nodes?.find(
                (n): n is Declaration => n.type === 'decl' && n.prop === 'row-gap',
              )
              const colGapDecl = rule.nodes?.find(
                (n): n is Declaration => n.type === 'decl' && n.prop === 'column-gap',
              )

              if (!gapDecl && !rowGapDecl && !colGapDecl) return

              // 解析间距数值
              let rowGapValue = ''
              let colGapValue = ''

              if (gapDecl) {
                const values = gapDecl.value.trim().split(/\s+/)
                rowGapValue = values[0]
                colGapValue = values[1] || values[0]
              }
              if (rowGapDecl) {
                rowGapValue = rowGapDecl.value
              }
              if (colGapDecl) {
                colGapValue = colGapDecl.value
              }

              // 注入用于子元素继承的 CSS 变量
              const targetDecl = gapDecl || rowGapDecl || colGapDecl
              if (targetDecl) {
                if (colGapValue) {
                  targetDecl.cloneBefore({ prop: '--flex-gap-x', value: colGapValue })
                }
                if (rowGapValue) {
                  targetDecl.cloneBefore({ prop: '--flex-gap-y', value: rowGapValue })
                }
              }

              // 为 Grid 布局提供旧版的 grid-* 属性 fallback
              if (gapDecl) {
                const hasGridGap = rule.nodes?.some(
                  (n) => n.type === 'decl' && (n as Declaration).prop === 'grid-gap',
                )
                if (!hasGridGap) {
                  gapDecl.cloneBefore({ prop: 'grid-gap', value: gapDecl.value })
                }
              }
              if (rowGapDecl) {
                const hasGridRowGap = rule.nodes?.some(
                  (n) => n.type === 'decl' && (n as Declaration).prop === 'grid-row-gap',
                )
                if (!hasGridRowGap) {
                  rowGapDecl.cloneBefore({ prop: 'grid-row-gap', value: rowGapDecl.value })
                }
              }
              if (colGapDecl) {
                const hasGridColGap = rule.nodes?.some(
                  (n) => n.type === 'decl' && (n as Declaration).prop === 'grid-column-gap',
                )
                if (!hasGridColGap) {
                  colGapDecl.cloneBefore({ prop: 'grid-column-gap', value: colGapDecl.value })
                }
              }

              // 为自身带有 display: flex 的自定义选择器做专属 owl 降级，防遗漏
              const displayDecl = rule.nodes?.find(
                (n): n is Declaration => n.type === 'decl' && n.prop === 'display',
              )
              const isRuleFlex = displayDecl ? ['flex', 'inline-flex'].includes(displayDecl.value) : false
              if (!isRuleFlex) return

              const dirDecl = rule.nodes?.find(
                (n): n is Declaration => n.type === 'decl' && n.prop === 'flex-direction',
              )
              const isRuleColumn = dirDecl?.value.includes('column') ?? false
              const isRuleReverse = dirDecl?.value.includes('reverse') ?? false

              const selector = rule.selector
              const fallbackSelector = selector.split(',').map(s => `.no-flex-gap ${s.trim()} > * + *`).join(', ')

              let fallbackRule: Rule | null = null

              if (isRuleColumn) {
                fallbackRule = postcss.rule({ selector: fallbackSelector }).append(
                  postcss.decl({ prop: isRuleReverse ? 'margin-bottom' : 'margin-top', value: rowGapValue }),
                  postcss.decl({ prop: 'margin-left', value: '0px' }),
                  postcss.decl({ prop: 'margin-right', value: '0px' }),
                  postcss.decl({ prop: isRuleReverse ? 'margin-top' : 'margin-bottom', value: '0px' })
                )
              } else {
                fallbackRule = postcss.rule({ selector: fallbackSelector }).append(
                  postcss.decl({ prop: isRuleReverse ? 'margin-right' : 'margin-left', value: colGapValue }),
                  postcss.decl({ prop: 'margin-top', value: '0px' }),
                  postcss.decl({ prop: 'margin-bottom', value: '0px' }),
                  postcss.decl({ prop: isRuleReverse ? 'margin-left' : 'margin-right', value: '0px' })
                )
              }

              if (fallbackRule) {
                rule.parent?.insertAfter(rule, fallbackRule)
              }
            },
          },
        ]).process(source, { from: chunk.fileName })

        chunk.source = result.css
      }
    },
  }
}
```

### 2. 关键插件的工作原理

#### 2.1 strip-css-layer — 平铺 `@layer` 块

Chromium < 99 不支持 CSS `@layer`，遇到后整个块内的规则都会被浏览器直接丢弃。我们将其平铺，消除 `@layer` 命名空间：

```
输入:                              输出:
@layer base {                      *,:after,:before { box-sizing: border-box }
  *,:after,:before { ... }        (无 @layer 包裹，规则直接暴露)
}
@layer theme, base;                (声明语句被移除)
```

#### 2.2 strip-at-property — 转换 `@property` 为 `:root`

Chromium < 85 不支持 `@property` 自定义属性的静态类型注册，导致如 `--tw-border-style` 丢失默认值（从而 `.border` 等失灵）。我们将其转化为 `:root` 声明：

```
输入:                              输出:
@property --tw-border-style {      :root {
  syntax: "*";                       --tw-border-style: solid;
  inherits: false;                   --tw-shadow: 0 0 transparent;
  initial-value: solid;              ...
}                                  }
                                   (@property 被移除)
```

#### 2.3 strip-where — 去除 `:where()` 包装

Chromium < 88 遇到包含 `:where()` 的规则会直接丢弃。将其替换为内部的选择器：

```
输入:                              输出:
:where([type=button]) {            [type=button] {
  appearance: button;                appearance: button;
}                                  }
```

#### 2.4 gap-fallback — 基于 CSS 变量继承的通用 Flex Gap Polyfill

为了兼容低版本浏览器不支持 Flex Gap（Chrome 84 以下只支持 Grid Gap）：

```
输入:                              输出:
.role-page {                       .role-page {
  display: flex;                     display: flex;
  flex-direction: column;            --flex-gap-x: 16px;
  gap: 16px;                         --flex-gap-y: 16px;
}                                    grid-gap: 16px;    /* grid 降级 */
                                     gap: 16px;
                                   }

                                   /* 全局注入的通用降级规则 (在 CSS 尾部) */
                                   .no-flex-gap .flex > * + *,
                                   .no-flex-gap .inline-flex > * + * {
                                     margin-left: var(--flex-gap-x, 0px);
                                     margin-top: 0px;
                                   }
                                   .no-flex-gap .flex-col > * + * {
                                     margin-top: var(--flex-gap-y, 0px);
                                     margin-left: 0px;
                                   }
```
通过自动生成的局部变量，任何自定义 gap 数值在子元素中均能通过继承的 CSS 变量完成 margin 兼容，实现了 100% 任意自定义间距的高效解耦适配。
