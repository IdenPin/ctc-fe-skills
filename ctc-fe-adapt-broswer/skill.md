# CTC 前端浏览器兼容性适配 (Legacy Browser Adaptation)

## Description

为 Vite + Vue 3 项目适配老旧浏览器（奇安信信创浏览器、低版本 Chrome/Edge 等），通过 `@vitejs/plugin-legacy` 生成兼容产物。适用于需要支持政企信创环境、国产浏览器、低版本 Chromium 内核浏览器的前端项目。

## When to use

- 项目需要支持奇安信可信浏览器、360安全浏览器等国产信创浏览器
- 目标用户可能使用低版本 Chrome（< 80）、Edge（< 80）、Safari（< 14）
- 构建后在老浏览器上出现 `SyntaxError: Unexpected token` 等语法错误
- 需要将 Vue 3 + Vite 项目部署到政企信创环境

## 问题背景

现代前端工具链（Vite、Vue 3、ESBuild）默认构建目标为现代浏览器，产出的代码包含：
- ES Module (`<script type="module">`)
- 可选链 `?.`、空值合并 `??`
- 顶层 await
- 私有类字段 `#private`
- 其他 ES2020+ 语法

老旧浏览器（Chromium < 80）无法解析这些语法，导致页面白屏、控制台报 SyntaxError。

## 解决方案

### 1. 安装依赖

```bash
npm install -D @vitejs/plugin-legacy
# 或
pnpm add -D @vitejs/plugin-legacy
```

> `plugin-legacy` 依赖 `terser` 进行压缩，如未安装需一并添加。

### 2. 配置 vite.config.ts

```ts
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import legacy from '@vitejs/plugin-legacy'

export default defineConfig({
  plugins: [
    vue(),
    // 添加 legacy 插件
    legacy({
      // 目标浏览器版本，根据实际需求调整
      targets: [
        'Chrome >= 63',
        'Edge >= 79', 
        'Firefox >= 67',
        'Safari >= 12',
        'iOS >= 12',
      ],
      // 为现代浏览器也注入 polyfill（如 Promise、Symbol 等）
      modernPolyfills: true,
      // 可选：额外注入 legacy polyfill
      // additionalLegacyPolyfills: ['regenerator-runtime/runtime'],
    }),
  ],
})
```

### 3. Targets 配置参考

| 场景 | Targets 配置 |
|---|---|
| 奇安信信创浏览器 | `['Chrome >= 63']` |
| 360安全浏览器 | `['Chrome >= 69']` |
| 通用政企环境 | `['Chrome >= 63', 'Edge >= 79', 'Firefox >= 67', 'Safari >= 12']` |
| IE11（不推荐） | `['ie 11']` 需额外配置 |

### 4. 验证方式

```bash
# 1. 构建生产版本（plugin-legacy 只对 build 生效）
npm run build

# 2. 启动 preview 服务
npm run preview -- --host

# 3. 用目标浏览器访问测试
# 如：http://192.168.x.x:4173/your-app/
```

## 关键要点

| 要点 | 说明 |
|---|---|
| **Dev server 不兼容** | `vite dev` 强制要求浏览器支持原生 ESM，plugin-legacy 对其无效 |
| **必须用 build 测试** | 老浏览器只能验证 `vite build` + `vite preview` 的产物 |
| **自动双份产物** | 现代浏览器加载 `*.js`，老浏览器自动降级加载 `*-legacy.js` |
| **Polyfill 按需注入** | 根据 targets 自动判断需要哪些 polyfill |

## 常见问题

### Q: Dev 环境无法在老浏览器调试？

A: 这是 Vite 的架构限制。开发时：
- 使用现代浏览器（Chrome 最新版）进行开发
- 功能完成后用 `vite build` + `vite preview` 在目标浏览器验证
- 如需在老浏览器调试，可考虑 Webpack 方案

### Q: 构建后仍有语法错误？

A: 检查：
1. 是否所有代码都经过 Vite 构建（排除外部 CDN 引入的库）
2. `targets` 配置是否覆盖了目标浏览器版本
3. 第三方库是否支持降级（部分库已放弃老浏览器）

### Q: 如何判断浏览器是否支持？

A: 在目标浏览器打开控制台，检查：
- `typeof Promise` 是否为 'function'
- `typeof Symbol` 是否为 'function'
- 是否支持 `<script type="module">`

## 浏览器兼容性测试页面

建议项目中添加一个免登录的测试页面，用于快速检测浏览器支持情况：

```vue
<!-- src/views/browserTest/BrowserTestPage.vue -->
<template>
  <div class="browser-test">
    <h1>浏览器兼容性测试</h1>
    <!-- 检测项：UA、存储、CSS特性、JS API、网络、图形等 -->
  </div>
</template>
```

测试页面应覆盖：
- User Agent / 浏览器版本
- localStorage / sessionStorage
- CSS Grid / Flexbox / 变量
- Promise / fetch / async
- WebSocket / WebRTC
- Canvas / WebGL

## 相关资源

- [@vitejs/plugin-legacy 文档](https://github.com/vitejs/vite/tree/main/packages/plugin-legacy)
- [Browserslist 配置语法](https://github.com/browserslist/browserslist)
- [Can I Use](https://caniuse.com/) - 查询特性兼容性

## Example

完整 vite.config.ts 示例：

```ts
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import legacy from '@vitejs/plugin-legacy'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

export default defineConfig({
  plugins: [
    vue(),
    vueJsx(),
    legacy({
      targets: ['Chrome >= 63', 'Edge >= 79', 'Firefox >= 67', 'Safari >= 12'],
      modernPolyfills: true,
    }),
    AutoImport({
      resolvers: [ElementPlusResolver()],
    }),
    Components({
      resolvers: [ElementPlusResolver()],
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
