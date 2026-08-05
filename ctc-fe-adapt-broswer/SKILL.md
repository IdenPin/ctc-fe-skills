---
name: ctc-fe-adapt-broswer
description: Use when diagnosing or planning production-build compatibility for Vite and Vue 3 applications running in domestic enterprise browsers, older Chromium or Edge engines, or environments showing legacy JavaScript syntax errors, blank pages, missing styles, or unsupported web-platform features.
---

# CTC 前端浏览器兼容性评估

> `broswer` 是历史目录拼写。为避免破坏现有安装路径暂时保留；下一个破坏性版本迁移为 `ctc-fe-adapt-browser`。

## 核心原则

先确定真实浏览器内核和业务验收范围，再选择兼容措施。构建产物中不再出现某段现代语法，只能证明转换发生，不能证明页面行为和视觉正确。

## 支持边界

- `@vitejs/plugin-legacy` 可以降低生产构建的 JavaScript 语法并按目标注入部分 polyfill，但不处理 CSS，也不保证第三方脚本和所有 Web API 可用。
- [Tailwind CSS 4 官方兼容说明](https://tailwindcss.com/docs/compatibility)的基线是 Chrome 111、Safari 16.4 和 Firefox 128，并依赖 `@property`、`color-mix()` 等现代 CSS。低于该基线属于项目专项兼容，不得宣称框架级完整支持。
- 当前仓库不把成熟 Tailwind 4 项目降级到 Tailwind 3.4 作为默认方案。
- `references/legacyCss.md` 中的 CSS 改写只用于解释既有实验方案和风险，不是可直接复制的公司标准插件。

## 评估流程

1. 记录浏览器产品、完整版本、User-Agent、操作系统、Chromium/WebKit 内核版本和部署协议。
2. 使用生产 `build + preview` 或等价静态服务复现；不要使用 Vite dev server 判断 legacy 构建兼容性。
3. 将问题分类为 JS 解析、运行时 API、CSS 解析、CSS 语义、第三方依赖或部署响应头。
4. 建立实际使用特性清单，只处理已经复现并进入验收范围的能力。
5. 在真实目标浏览器完成关键流程和视觉验收；模拟 UA 或只检查产物字符串不能替代验收。

## JavaScript 生产构建

按项目的正式浏览器支持矩阵配置 `@vitejs/plugin-legacy`，不要复制固定版本列表：

```ts
import legacy from '@vitejs/plugin-legacy'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [
    legacy({
      targets: ['Chrome >= 79', 'Edge >= 79', 'Safari >= 12']
    })
  ]
})
```

- targets 必须来自合同、现场统计或测试设备，不以“国产浏览器”名称代替内核版本。
- 仅在确认现代构建也缺少目标运行时 API 时配置 `modernPolyfills`，避免默认全量注入。
- `drop_console`、压缩器选择等生产策略与兼容性无直接关系，不纳入本 skill 的默认配置。
- Web Worker、第三方预构建产物、动态 import 和外部 CDN 脚本必须单独验证。

## Tailwind 4 与现代 CSS

优先按以下顺序处理：

1. 避免在需要兼容的关键路径使用目标浏览器不支持的 utility 或 CSS 特性。
2. 对局部视觉增强使用 `@supports` 和可接受的基础样式渐进增强。
3. 对少量已知问题使用成熟 PostCSS 插件，并为转换前后语义建立 fixture 与视觉回归。
4. 只有在业务明确接受行为差异时，才评估项目特定的 `@layer`、`:where()`、`@property`、transform 或 gap 改写。

禁止用“删除所有 `@layer`、`:where()`、`@property`”作为通用验收标准。这些转换可能改变层叠顺序、选择器优先级、自定义属性继承和动画行为。

## 验证门禁

### 1. 构建验证

```bash
pnpm build
pnpm preview -- --host
```

记录构建工具版本、targets、polyfill 列表、产物大小变化和构建 warning。

### 2. 自动化功能验证

至少覆盖应用启动、登录、路由跳转、表单提交、弹窗、表格、上传下载和错误提示。关键能力应有 Playwright 或项目等价 E2E 测试。

### 3. 视觉验证

对布局、间距、transform、动画、主题色、浮层和响应式断点执行截图对比。CSS 字符串扫描仅作为辅助诊断。

### 4. 真实环境验收

在目标客户设备或同版本浏览器完成 smoke test，记录通过版本、已知差异和不支持能力。未经真实环境验收，不得输出“已兼容”“完整支持”等结论。

## 诊断页面

需要现场采集信息时读取 [浏览器测试页面设计](./references/browserTest.md)。测试页必须受环境开关或访问控制保护，不采集凭证、业务数据和可用于用户追踪的信息。

## 实验性 CSS 方案

维护或评审既有 `legacyCssCompat` 时读取 [实验方案与风险说明](./references/legacyCss.md)。任何转换上线前都必须具备输入输出 fixture、视觉回归、关键流程测试和真实目标浏览器记录。
