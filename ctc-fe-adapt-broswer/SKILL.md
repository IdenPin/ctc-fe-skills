---
name: ctc-fe-adapt-broswer
description: 为 Vite + Vue 3 + Tailwind CSS 4 项目适配老旧浏览器（奇安信信创浏览器、低版本 Chrome/Edge 等），覆盖 JS 语法降级与 CSS 现代特性兼容。适用于需要支持政企信创环境、国产浏览器、低版本 Chromium 内核浏览器的前端项目。
---

> 本文是基于新版 `legacyCss.ts` 源码（含 CSS 嵌套降级、逻辑属性转换、独立 transform 属性兼容等增强）更新的 skill 副本。

# CTC 前端浏览器兼容性适配

## When to use

- 项目需要支持奇安信可信浏览器、360安全浏览器等国产信创浏览器
- 目标用户可能使用低版本 Chrome（< 80）、Edge（< 80）、Safari（< 14）
- 构建后在老浏览器上出现 `SyntaxError: Unexpected token` 等语法错误或白屏
- 构建后页面样式丢失（Tailwind CSS 4 的 `@layer`/`@property`/`:where()` 不支持）

## 问题背景

现代前端默认构建目标为现代浏览器，低版本内核（Chromium < 80）面临以下障碍：
- **JS 层面**：可选链 `?.`、空值合并 `??`、顶层 `await` 等无法解析。
- **CSS 层面**：不支持 CSS 原生嵌套（`&` 语法）、逻辑属性（`padding-inline`/`margin-block`）、`@layer`、`@property`、`:where()`、独立 transform 属性（`translate`/`rotate`/`scale`）、以及 Flex 布局下的 `gap`（低版本只支持 Grid 布局的 gap，不支持 Flexbox 的 gap 间距）。

---

## 解决方案

### Part 1: JS 兼容 — @vitejs/plugin-legacy

#### 1.1 安装依赖

```bash
pnpm add -D @vitejs/plugin-legacy terser
```

#### 1.2 配置 vite.config.ts

```ts
import legacy from '@vitejs/plugin-legacy'

export default defineConfig({
  plugins: [
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
*构建后会自动生成双份 JS 产物（现代版 ESM 配合 `nomodule` 格式的 legacy 降级包，由浏览器通过标签属性自动分流）。*

---

### Part 2: CSS 兼容 — legacyCss.ts Vite 插件

由于 `@vitejs/plugin-legacy` 不处理 CSS，Tailwind CSS 4 产生的新语法必须通过 PostCSS 最终在构建包阶段降级。

当前插件按顺序完成 7 项处理：

0. **CSS 原生嵌套 → 平铺** — `postcss-nesting` 将 `& > div { ... }` 等嵌套语法展开（Chrome < 120）
1. **逻辑属性 → 物理属性** — `postcss-logical` 将 `padding-inline`/`margin-block` 转为物理方向（Chrome < 87）
2. **`@layer` 剥离** — 将 `@layer name { ... }` 内规则平铺（Chrome < 99）
3. **`@property` → `:root` 变量** — 提取 `initial-value` 转为 `:root` 声明（Chrome < 85）
4. **`:where()` 剥离** — 替换为内部实际选择器（Chrome < 88）
5. **独立 transform 属性 → `transform()` 函数** — 合并到 `transform` 属性中（Chrome < 104）
6. **gap fallback** — 基于 CSS 变量继承的通用 Flex/Grid Gap Polyfill

#### 2.1 引入插件
在项目中引入 `legacyCssCompat` 插件（必须放在 `vite.config.ts` 插件列表最后，因为 `enforce: 'post'` 能确保在所有插件以及 Tailwind 完成样式抽取后再处理产物）：

```ts
import { legacyCssCompat } from './src/app/config/legacyCss'

export default defineConfig({
  plugins: [
    // ...其他插件
    legacyCssCompat(),
  ],
})
```

#### 2.2 详细设计与原理
关于 `legacyCss.ts` 的**完整插件源码**、**自动注入 head 特征检测脚本与 crossorigin 清理机制**、**各 PostCSS 插件的实现原理**（包括 CSS 嵌套降级、逻辑属性转换、独立 transform 属性兼容），以及**基于 CSS 变量继承的通用 Flex Gap Polyfill** 原理解析，详见：
[legacyCss.ts 源码与原理解析](./references/legacyCss.md)

---

### Part 3: 浏览器兼容性测试页面

建议添加一个免登录的测试页面，用以在客户设备或老旧机器上直接测量当前的软硬件环境及支持的 API（包括对 Flex Gap 进行高精度的实际测量），详见：
[测试页面配置及代码示例](./references/browserTest.md)

---

## 验证方式

```bash
# 1. 构建生产版本并启动预览
pnpm run build
pnpm run preview -- --host

# 2. 访问测试页验证
# 浏览器兼容性测试页：http://<IP>:4173/browser-test
```

### 验证打包 CSS 产物

```bash
# 检查 @layer、@property、:where、CSS 嵌套、逻辑属性、独立 transform 是否已消除（应均为 0）
grep -c '@layer' dist/*/assets/index-*.css
grep -c '@property' dist/*/assets/index-*.css
grep -c ':where(' dist/*/assets/index-*.css
grep -cE '& \[' dist/*/assets/index-*.css
grep -c -E '(padding-inline|margin-block)' dist/*/assets/index-*.css
grep -cE '(translate|rotate|scale)[ :]' dist/*/assets/index-*.css

# 检查 transform 函数写法是否出现（应大于 0）
grep -oE 'translate\(|rotate\(|scale\(' dist/*/assets/index-*.css | head -3

# 检查 flex gap 通用变量与标记类是否注入（应大于 0）
grep -o '\-\-flex-gap' dist/*/assets/index-*.css | wc -l
grep -o 'no-flex-gap' dist/*/assets/index-*.css | wc -l
```

---

## 关键要点

| 要点 | 说明 |
|---|---|
| **Dev server 不兼容** | `vite dev` 运行在原生 ESM 下，plugin-legacy 和 legacyCss 对其无效。必须用 `build` + `preview` 测试老浏览器。 |
| **Tailwind 4 特殊性** | `@layer`/`@property`/`:where()` 是 Tailwind 4 架构核心，必须全量清除。还需处理 CSS 嵌套、逻辑属性、独立 transform 等。 |
| **插件执行顺序** | `postcss-nesting` 和 `postcss-logical` 必须优先执行，因为它们处理的是 CSS 源码层面的语法转换，之后的插件才能正确识别展开后的规则。 |
| **no-flex-gap 隔离防冲突** | 注入的降级样式绑定在 `.no-flex-gap` 下，由顶层 JS 探测到不支持时才同步挂在 html 上，现代浏览器自动跳过，有效解决双重边距。 |
| **crossorigin 剥离** | 插件会自动移除 `<link rel="stylesheet">` 上的 `crossorigin` 属性，避免 `vite preview` 因不返回 CORS 头导致外部样式被忽略。 |
| **免登录测试页** | 部署后提供一个免登录的测试路由能显著提高现场故障排查与适配论证效率。 |
