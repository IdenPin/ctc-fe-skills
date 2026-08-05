# 浏览器诊断页面设计

## 使用边界

诊断页用于客户现场采集兼容性事实，不是永久公开的系统功能。默认只在测试、预发或显式开启的诊断环境注册路由；生产环境需要短期启用时，应配置访问控制和关闭时间。

禁止展示或上传 Cookie、Token、localStorage 内容、设备唯一标识和业务数据。User-Agent、浏览器能力和测试结果默认只在当前页面展示，由现场人员主动复制。

## 路由开关

```ts
const diagnosticRoutes = import.meta.env.VITE_ENABLE_BROWSER_DIAGNOSTICS === 'true'
  ? [
      {
        path: '/browser-test',
        name: 'BrowserTest',
        component: () => import('@/views/browser-test/index.vue'),
        meta: { public: true, title: '浏览器兼容性测试' }
      }
    ]
  : []
```

公开路由只表示不依赖业务登录态，不表示允许长期暴露到公网。项目应结合网关白名单、临时口令或内部环境限制访问。

## 建议采集内容

- User-Agent、操作系统和浏览器显示版本。
- `CSS.supports` 对项目实际使用特性的检测结果。
- Promise、Fetch、URL、AbortController 等关键运行时 API 是否存在。
- Canvas、WebGL、文件下载、上传、WebSocket 等项目实际需要的能力。
- 页面加载错误和资源请求失败摘要，不记录请求凭证或响应正文。

浏览器名称只能作为辅助信息，兼容结论必须绑定实际内核和完整版本。国产双核浏览器需要分别记录当前使用的极速/兼容模式。

## Flex gap 实测

不要只使用 `CSS.supports('gap', '1px')` 判断 Flex gap；旧浏览器可能支持 Grid gap 但不支持 Flex gap。使用 DOM 尺寸实测，并确保元素在检测结束后清理：

```ts
function supportsFlexGap(): boolean {
  const flex = document.createElement('div')
  flex.style.cssText = [
    'position:absolute',
    'visibility:hidden',
    'display:flex',
    'flex-direction:column',
    'row-gap:1px'
  ].join(';')

  flex.append(document.createElement('div'), document.createElement('div'))
  document.body.appendChild(flex)

  try {
    return flex.scrollHeight === 1
  } finally {
    flex.remove()
  }
}
```

不要在渲染同一结果时重复执行检测；先计算一次，再展示结果。

## 验收输出

诊断页最终输出应包含：测试时间、环境名称、浏览器/内核信息、每项能力的 pass/fail、项目版本和构建版本。诊断结果只能帮助定位问题，最终兼容结论仍以关键业务流程和视觉验收为准。
