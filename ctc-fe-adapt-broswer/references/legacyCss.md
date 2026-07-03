# legacyCss.ts 兼容插件源码与原理解析

### 1. legacyCss.ts 完整源码

在前端项目中创建 Vite 插件文件（如 `src/plugins/legacyCss.ts`），在 `generateBundle` 阶段用 PostCSS 处理所有 CSS 产物：

```ts
import type { AtRule, Container, Declaration, Root, Rule } from 'postcss';
import type { Plugin } from 'vite';

import postcss from 'postcss';
import postcssLogical from 'postcss-logical';
import postcssNesting from 'postcss-nesting';

/**
 * 将 :where(X) 替换为 X，处理嵌套括号
 */
function stripWherePseudo(selector: string): string {
  let result = '';
  let i = 0;
  while (i < selector.length) {
    if (selector.startsWith(':where(', i)) {
      let depth = 1;
      const start = i + 7;
      let j = start;
      while (j < selector.length && depth > 0) {
        if (selector[j] === '(') depth++;
        else if (selector[j] === ')') depth--;
        if (depth > 0) j++;
      }
      result += selector.slice(start, j);
      i = j + 1;
    } else {
      result += selector[i];
      i++;
    }
  }
  return result;
}

/**
 * 按空白字符拆分 CSS 值，但跳过括号内的空白（应对 calc(var(--spacing) * 6) 等）
 */
function splitCssValue(value: string): string[] {
  const parts: string[] = [];
  let current = '';
  let depth = 0;
  for (const ch of value.trim()) {
    if (ch === '(') depth++;
    if (ch === ')') depth--;
    if (ch === ' ' && depth === 0) {
      if (current) {
        parts.push(current);
        current = '';
      }
    } else {
      current += ch;
    }
  }
  if (current) parts.push(current);
  return parts;
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
 * 4. aspect-ratio polyfill: Chromium < 88 不支持 aspect-ratio，用 ::before padding-top hack 降级
 * 5. individual transform properties → transform(): Chromium < 104 不支持独立的 translate/rotate/scale 属性，转为 transform 函数写法
 * 6. gap fallback: 基于 CSS 变量继承的通用 Flex Gap Polyfill (针对低版本信创浏览器)
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
      `;
      const result = html.replace('<head>', `<head>\n${detectScript.trim()}`);
      // 去掉 stylesheet 的 crossorigin，vite preview 不返回 CORS 头会导致样式不被应用
      return result.replaceAll(
        /(<link[^>]*rel="stylesheet"[^>]*) crossorigin([^>]*>)/g,
        '$1$2',
      );
    },
    async generateBundle(_options, bundle) {
      for (const chunk of Object.values(bundle)) {
        if (chunk.type !== 'asset' || !chunk.fileName.endsWith('.css'))
          continue;

        const source =
          typeof chunk.source === 'string'
            ? chunk.source
            : new TextDecoder().decode(chunk.source);

        const result = await postcss([
          // 0. CSS 原生嵌套 → 平铺（Chrome < 120 不支持嵌套）
          postcssNesting(),
          // 1. 逻辑属性 → 物理属性（Chrome < 87 不支持 padding-inline/padding-block 等）
          postcssLogical(),
          // 2. strip @layer: 将 @layer name { ... } 平铺为普通规则，移除 @layer 声明
          {
            postcssPlugin: 'strip-css-layer',
            AtRule: {
              layer(node: AtRule) {
                if (node.nodes?.length) {
                  node.replaceWith(...node.nodes);
                } else {
                  node.remove();
                }
              },
            },
          },
          // 3. strip @property: 将 @property --x { initial-value: y } 转为 :root { --x: y }
          {
            postcssPlugin: 'strip-at-property',
            Once(root: Root) {
              const initialValues: Array<{
                name: string;
                value: string;
              }> = [];
              root.walkAtRules('property', (node: AtRule) => {
                const name = node.params.trim();
                const initialDecl = node.nodes?.find(
                  (n): n is Declaration =>
                    n.type === 'decl' && n.prop === 'initial-value',
                );
                if (initialDecl) {
                  initialValues.push({ name, value: initialDecl.value });
                }
                node.remove();
              });
              if (initialValues.length === 0) return;
              let rootRule = (root as Container).nodes?.find(
                (n): n is Rule =>
                  n.type === 'rule' && (n as Rule).selector === ':root',
              );
              if (!rootRule) {
                rootRule = postcss.rule({ selector: ':root' });
                root.prepend(rootRule);
              }
              for (const { name, value } of initialValues) {
                rootRule.append(postcss.decl({ prop: name, value }));
              }
            },
          },
          // 4. strip :where(): Chromium < 88 不支持 :where()，整条规则会被丢弃
          {
            postcssPlugin: 'strip-where',
            Rule(rule: Rule) {
              if (!rule.selector.includes(':where(')) return;
              rule.selector = stripWherePseudo(rule.selector);
            },
          },
          // 5. individual transform properties → transform functions (Chrome < 104)
          {
            postcssPlugin: 'individual-transform-props',
            Rule(rule: Rule) {
              const transformProps = ['translate', 'rotate', 'scale'] as const;
              const decls = rule.nodes?.filter(
                (n): n is Declaration =>
                  n.type === 'decl' &&
                  (transformProps as readonly string[]).includes(n.prop),
              );
              if (!decls?.length) return;

              const transformParts: string[] = [];
              const existingTransform = rule.nodes?.find(
                (n): n is Declaration =>
                  n.type === 'decl' && n.prop === 'transform',
              );

              for (const decl of decls) {
                if (decl.value === 'none') {
                  decl.remove();
                  continue;
                }

                switch (decl.prop) {
                  case 'rotate': {
                    transformParts.push(`rotate(${decl.value})`);
                    break;
                  }
                  case 'scale': {
                    const parts = splitCssValue(decl.value);
                    if (parts.length === 1) {
                      transformParts.push(`scale(${parts[0]})`);
                    } else if (parts.length >= 2) {
                      transformParts.push(`scale(${parts[0]}, ${parts[1]})`);
                    }
                    break;
                  }
                  case 'translate': {
                    const parts = splitCssValue(decl.value);
                    if (parts.length === 1) {
                      transformParts.push(`translate(${parts[0]})`);
                    } else if (parts.length >= 2) {
                      transformParts.push(
                        `translate(${parts[0]}, ${parts[1]})`,
                      );
                    }
                    break;
                  }
                }

                decl.remove();
              }

              if (transformParts.length === 0) return;

              const transformValue = [
                existingTransform?.value,
                ...transformParts,
              ]
                .filter(Boolean)
                .join(' ');

              if (existingTransform) {
                existingTransform.value = transformValue;
              } else {
                rule.append(
                  postcss.decl({
                    prop: 'transform',
                    value: transformValue,
                  }),
                );
              }
            },
          },
          // 6. gap fallback — 仅对有 gap 属性的 flex 容器生成 fallback，避免误覆盖 ml-* 等独立 margin
          {
            postcssPlugin: 'gap-fallback',
            Rule(rule: Rule) {
              const gapDecl = rule.nodes?.find(
                (n): n is Declaration => n.type === 'decl' && n.prop === 'gap',
              );
              const rowGapDecl = rule.nodes?.find(
                (n): n is Declaration =>
                  n.type === 'decl' && n.prop === 'row-gap',
              );
              const colGapDecl = rule.nodes?.find(
                (n): n is Declaration =>
                  n.type === 'decl' && n.prop === 'column-gap',
              );

              if (!gapDecl && !rowGapDecl && !colGapDecl) return;

              let rowGapValue = '';
              let colGapValue = '';

              if (gapDecl) {
                const values = splitCssValue(gapDecl.value);
                rowGapValue = values[0] ?? '';
                colGapValue = values[1] ?? values[0] ?? '';
              }
              if (rowGapDecl) {
                rowGapValue = rowGapDecl.value;
              }
              if (colGapDecl) {
                colGapValue = colGapDecl.value;
              }

              const targetDecl = gapDecl || rowGapDecl || colGapDecl;
              if (targetDecl) {
                if (colGapValue) {
                  targetDecl.cloneBefore({
                    prop: '--flex-gap-x',
                    value: colGapValue,
                  });
                }
                if (rowGapValue) {
                  targetDecl.cloneBefore({
                    prop: '--flex-gap-y',
                    value: rowGapValue,
                  });
                }
              }

              if (gapDecl) {
                const hasGridGap = rule.nodes?.some(
                  (n) =>
                    n.type === 'decl' && (n as Declaration).prop === 'grid-gap',
                );
                if (!hasGridGap) {
                  gapDecl.cloneBefore({
                    prop: 'grid-gap',
                    value: gapDecl.value,
                  });
                }
              }
              if (rowGapDecl) {
                const hasGridRowGap = rule.nodes?.some(
                  (n) =>
                    n.type === 'decl' &&
                    (n as Declaration).prop === 'grid-row-gap',
                );
                if (!hasGridRowGap) {
                  rowGapDecl.cloneBefore({
                    prop: 'grid-row-gap',
                    value: rowGapDecl.value,
                  });
                }
              }
              if (colGapDecl) {
                const hasGridColGap = rule.nodes?.some(
                  (n) =>
                    n.type === 'decl' &&
                    (n as Declaration).prop === 'grid-column-gap',
                );
                if (!hasGridColGap) {
                  colGapDecl.cloneBefore({
                    prop: 'grid-column-gap',
                    value: colGapDecl.value,
                  });
                }
              }

              // 判断是否为单值 gap（无法区分 row/column 方向）
              const isSingleGapValue = !!(
                gapDecl &&
                !rowGapDecl &&
                !colGapDecl &&
                splitCssValue(gapDecl.value).length === 1
              );

              const selector = rule.selector;
              const fallbackSelector = selector
                .split(',')
                .map((s) => `.no-flex-gap ${s.trim()} > * + *`)
                .join(', ');

              const decls: Declaration[] = [];

              if (isSingleGapValue) {
                // 单值 gap：默认按 flex row 方向，只生成 margin-left
                decls.push(
                  postcss.decl({ prop: 'margin-left', value: colGapValue }),
                  postcss.decl({ prop: 'margin-top', value: '0px' }),
                  postcss.decl({ prop: 'margin-right', value: '0px' }),
                  postcss.decl({ prop: 'margin-bottom', value: '0px' }),
                );
              } else {
                // 独立 column-gap / row-gap 或多值 gap，按实际方向生成
                if (colGapValue) {
                  decls.push(
                    postcss.decl({ prop: 'margin-left', value: colGapValue }),
                  );
                }
                if (rowGapValue) {
                  decls.push(
                    postcss.decl({ prop: 'margin-top', value: rowGapValue }),
                  );
                }
                if (!colGapValue && !rowGapValue) return;

                if (!colGapValue)
                  decls.push(
                    postcss.decl({ prop: 'margin-left', value: '0px' }),
                  );
                if (!rowGapValue)
                  decls.push(
                    postcss.decl({ prop: 'margin-top', value: '0px' }),
                  );
                decls.push(
                  postcss.decl({ prop: 'margin-right', value: '0px' }),
                  postcss.decl({ prop: 'margin-bottom', value: '0px' }),
                );
              }

              const fallbackRule = postcss
                .rule({ selector: fallbackSelector })
                .append(...decls);

              rule.parent?.insertAfter(rule, fallbackRule);

              // 单值 gap：添加 flex-col / grid 复合选择器覆盖
              if (isSingleGapValue) {
                const gapValue = colGapValue;

                // flex-col / flex-column 覆盖：用 margin-top，取消 margin-left
                const colSelector = selector
                  .split(',')
                  .flatMap((s) => [
                    `.no-flex-gap ${s.trim()}.flex-col > * + *`,
                    `.no-flex-gap ${s.trim()}.flex-column > * + *`,
                  ])
                  .join(', ');
                const colRule = postcss
                  .rule({ selector: colSelector })
                  .append(
                    postcss.decl({ prop: 'margin-left', value: '0px' }),
                    postcss.decl({ prop: 'margin-right', value: '0px' }),
                    postcss.decl({ prop: 'margin-top', value: gapValue }),
                    postcss.decl({ prop: 'margin-bottom', value: '0px' }),
                  );
                rule.parent?.insertAfter(fallbackRule, colRule);

                // grid / inline-grid 覆盖：两个方向都需要 margin
                const gridSelector = selector
                  .split(',')
                  .flatMap((s) => [
                    `.no-flex-gap ${s.trim()}.grid > * + *`,
                    `.no-flex-gap ${s.trim()}.inline-grid > * + *`,
                  ])
                  .join(', ');
                const gridRule = postcss
                  .rule({ selector: gridSelector })
                  .append(
                    postcss.decl({ prop: 'margin-left', value: gapValue }),
                    postcss.decl({ prop: 'margin-right', value: '0px' }),
                    postcss.decl({ prop: 'margin-top', value: gapValue }),
                    postcss.decl({ prop: 'margin-bottom', value: '0px' }),
                  );
                rule.parent?.insertAfter(colRule, gridRule);
              }
            },
          },
        ]).process(source, { from: chunk.fileName });

        chunk.source = result.css;
      }
    },
  };
}
```

### 2. 关键插件的工作原理

#### 2.0 postcss-nesting — CSS 原生嵌套 → 平铺

Chromium < 120 不支持 CSS 原生嵌套语法（`& > div { ... }`）。`postcss-nesting` 将嵌套规则展开为平铺的选择器：

```css
/* 输入 */
.card {
  & > div { color: red; }
}

/* 输出 */
.card > div { color: red; }
```

#### 2.1 postcss-logical — 逻辑属性 → 物理属性

Chromium < 87 不支持 `padding-inline`/`padding-block`/`margin-block` 等逻辑属性。`postcss-logical` 根据书写模式转换为物理方向：

```css
/* 输入 */
.element {
  padding-inline: 12px;
  margin-block: 8px;
}

/* 输出 (ltr) */
.element {
  padding-left: 12px;
  padding-right: 12px;
  margin-top: 8px;
  margin-bottom: 8px;
}
```

#### 2.2 strip-css-layer — 平铺 `@layer` 块

Chromium < 99 不支持 CSS `@layer`，遇到后整个块内的规则都会被浏览器直接丢弃。我们将其平铺，消除 `@layer` 命名空间：

```css
/* 输入 */
@layer base {
  *,:after,:before { box-sizing: border-box }
}
@layer theme, base;     /* 声明语句被移除 */

/* 输出 */
*,:after,:before { box-sizing: border-box }
```

#### 2.3 strip-at-property — 转换 `@property` 为 `:root`

Chromium < 85 不支持 `@property` 自定义属性的静态类型注册，导致如 `--tw-border-style` 丢失默认值（从而 `.border` 等失灵）。我们将其转化为 `:root` 声明：

```css
/* 输入 */
@property --tw-border-style {
  syntax: "*";
  inherits: false;
  initial-value: solid;
}

/* 输出 */
:root {
  --tw-border-style: solid;
  --tw-shadow: 0 0 transparent;
  ...
}
/* @property 被移除 */
```

#### 2.4 strip-where — 去除 `:where()` 包装

Chromium < 88 遇到包含 `:where()` 的规则会直接丢弃。将其替换为内部的选择器：

```css
/* 输入 */
:where([type=button]) {
  appearance: button;
}

/* 输出 */
[type=button] {
  appearance: button;
}
```

#### 2.5 individual-transform-props — 独立 transform 转为函数

Chromium < 104 不支持独立的 `translate`/`rotate`/`scale` CSS 属性，必须合并到 `transform` 属性中通过函数写法实现：

```css
/* 输入 */
.element {
  translate: 100px 200px;
  rotate: 45deg;
  scale: 0.5;
  transform: skewX(-10deg);
}

/* 输出 */
.element {
  transform: skewX(-10deg) translate(100px, 200px) rotate(45deg) scale(0.5);
}
```

注意：
- `value: none` 的声明会被直接移除（无需合并）
- 多值时使用 `splitCssValue()` 正确拆分，避免 `calc(…)` 内的空格被误分割
- 同时存在已有 `transform` 属性的，追加到其后

#### 2.6 gap-fallback — 基于 CSS 变量继承的通用 Flex Gap Polyfill

为了兼容低版本浏览器不支持 Flex Gap（Chrome 84 以下只支持 Grid Gap）：

```css
/* 输入 */
.role-page {
  display: flex;
  gap: 16px;
}

/* 输出 */
.role-page {
  display: flex;
  --flex-gap-x: 16px;
  --flex-gap-y: 16px;
  grid-gap: 16px;    /* grid 降级 */
  gap: 16px;
}

/* 每容器独立生成专属 owl 选择器，全量重置四个方向 margin */
.no-flex-gap .role-page > * + * {
  margin-left: 16px;
  margin-top: 0px;
  margin-right: 0px;
  margin-bottom: 0px;
}
```

**新版本 vs 旧版本的设计差异：**

| 对比维度 | 旧版（`OnceExit` + 全局通用规则） | 新版（`Rule` 内按选择器逐条生成） |
|---|---|---|
| 全局规则 | 尾部注入 4 条通用 `.flex`/`.flex-col`/… 选择器 | 不注入通用规则，仅对有 gap 的实际选择器逐条生成专属 `> * + *` 规则 |
| 方向判断 | 获取当前规则的 `display` + `flex-direction` 判断方向 | 不读取 `flex-direction`，优先从 `row-gap`/`column-gap` 独立值确定方向，无独立值时按 row 方向 |
| 单值 gap | 始终按 gap 数值 + display/flex-direction 判断方向 | 引入 `isSingleGapValue` 逻辑：单值 gap 默认为 row 方向，同时额外生成 `.flex-col`/`.grid` 覆盖规则 |
| margin 隔离 | 只设置用到的方向，其他方向不显式归零 | **强制全量重置四个方向**，杜绝与其他 margin 类（如 `ml-*`）冲突 |
| 值解析 | `value.trim().split(/\s+/)` | `splitCssValue()` 跳过括号内空白，正确支持 `calc(...)` |

**新版核心改进：**

- **CSS 变量继承**：通过 `--flex-gap-x` 和 `--flex-gap-y` 将 gap 数值暴露为 CSS 变量，子元素通过继承机制自动获取。任意自定义间距均能适配。

- **严格的方向隔离**：所有 fallback 规则同时显式声明 `margin-top/right/bottom/left` 四个方向值（多余方向置 `0px`），杜绝使用 `margin-left` 时其他 margin 值被覆盖的问题。

- **单值 gap 特殊处理**：当遇到 `gap: 16px`（单值，无 `row-gap`/`column-gap`）时，会额外生成两类选择器的降级：
  - `.flex-col` / `.flex-column` 覆盖：将 margin 从水平方向转为垂直方向
  - `.grid` / `.inline-grid` 覆盖：两个方向均添加 margin

- **零误判机制**：所有降级样式绑定在 `.no-flex-gap` 父选择器下，仅当 JS 运行时检测到浏览器不支持 flex gap 时，才会在 `<html>` 上添加该类名，现代浏览器完全跳过。

### 3. `splitCssValue` 辅助函数

用于安全地按空白拆分 CSS 值，自动跳过括号内的空白：

```ts
splitCssValue('16px')                        // → ['16px']
splitCssValue('16px 8px')                    // → ['16px', '8px']
splitCssValue('calc(var(--spacing) * 6)')    // → ['calc(var(--spacing) * 6)']
splitCssValue('scale(0.5, 0.3)')             // → ['scale(0.5, 0.3)']
```

这是对旧版 `value.trim().split(/\s+/)` 的改进——旧版会将 `calc(var(--spacing) * 6)` 错误地拆成 `['calc(var(--spacing)', '*', '6)']`。

### 4. `transformIndexHtml` 增强

除了注入 flex gap 特征检测脚本外，新版还额外处理了 **stylesheet 的 crossorigin 属性**：

```ts
return result.replaceAll(
  /(<link[^>]*rel="stylesheet"[^>]*) crossorigin([^>]*>)/g,
  '$1$2',
);
```

原因：`vite preview` 启动的静态服务器不返回 CORS 头，如果 `<link>` 标签带有 `crossorigin` 属性，浏览器会因跨域限制拒绝加载样式表。
