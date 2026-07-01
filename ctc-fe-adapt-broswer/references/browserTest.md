# 浏览器兼容性测试页面设计与配置

为了能够快速且免登录在客户现场的老浏览器上验证兼容性，推荐在项目中添加一个测试页。

### 1. 路由配置 (无需登录)

在路由器中注册为公开页面（跳过登录拦截）：

```ts
// src/app/router/index.ts
{
  path: '/browser-test',
  name: 'BrowserTest',
  component: () => import('@/views/browser-test/index.vue'),
  meta: { public: true, title: '浏览器兼容性测试' },
}
```

### 2. 测试页面组件 index.vue 模板

页面用于全方位检测：User Agent、Cookie、localStorage/sessionStorage、CSS 变量、Canvas/WebGL、Promise、Fetch、WebRTC 等。

重点是对 **`gap (flexbox)`** 属性采用同等的高精度 DOM 动态测量来避免误判：

```vue
<!-- src/views/browser-test/index.vue -->
<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface TestItem {
  label: string
  value: string
  pass?: boolean
}

interface Section {
  title: string
  items: TestItem[]
}

const sections = ref<Section[]>([])

function detectBrowser(): string {
  const ua = navigator.userAgent
  if (/Edg\//.test(ua)) return 'Edge'
  if (/OPR\//.test(ua) || /Opera/.test(ua)) return 'Opera'
  if (/Chrome/.test(ua) && /Safari/.test(ua) && !/Edg\//.test(ua) && !/OPR\//.test(ua))
    return 'Chrome'
  if (/Firefox/.test(ua)) return 'Firefox'
  if (/Safari/.test(ua) && !/Chrome/.test(ua)) return 'Safari'
  return '未知'
}

function detectOS(): string {
  const ua = navigator.userAgent
  if (/Windows NT 10/.test(ua)) return 'Windows 10/11'
  if (/Windows NT 6\.1/.test(ua)) return 'Windows 7'
  if (/Mac OS X/.test(ua)) return 'macOS'
  if (/iPhone|iPad|iPod/.test(ua)) return 'iOS'
  if (/Android/.test(ua)) return 'Android'
  return '未知'
}

/**
 * 精准特征检测：当前浏览器是否真实支持 Flexbox Gap
 */
function checkActualFlexGap(): boolean {
  if (typeof window === 'undefined') return false
  try {
    const flex = document.createElement('div')
    flex.style.display = 'flex'
    flex.style.flexDirection = 'column'
    flex.style.rowGap = '1px'
    flex.style.height = 'auto'
    flex.style.padding = '0px'
    flex.style.margin = '0px'
    flex.style.border = 'none'

    const child1 = document.createElement('div')
    child1.style.height = '0px'
    child1.style.padding = '0px'
    child1.style.margin = '0px'
    child1.style.border = 'none'

    const child2 = document.createElement('div')
    child2.style.height = '0px'
    child2.style.padding = '0px'
    child2.style.margin = '0px'
    child2.style.border = 'none'

    flex.appendChild(child1)
    flex.appendChild(child2)
    document.body.appendChild(flex)
    const isSupported = flex.scrollHeight === 1
    document.body.removeChild(flex)
    return isSupported
  } catch {
    return false
  }
}

function runTests(): void {
  const result: Section[] = []

  // 1. 基本信息
  result.push({
    title: '设备与浏览器信息',
    items: [
      { label: 'User Agent', value: navigator.userAgent },
      { label: '浏览器', value: detectBrowser() },
      { label: '操作系统', value: detectOS() },
    ],
  })

  // 2. CSS 特性支持
  result.push({
    title: 'CSS 特性支持',
    items: [
      {
        label: 'CSS Grid',
        value: CSS.supports('display', 'grid') ? '支持' : '不支持',
        pass: CSS.supports('display', 'grid'),
      },
      {
        label: 'CSS 变量',
        value: CSS.supports('--test', '0') ? '支持' : '不支持',
        pass: CSS.supports('--test', '0'),
      },
      {
        label: 'gap (flexbox)',
        value: checkActualFlexGap() ? '支持' : '不支持',
        pass: checkActualFlexGap(),
      },
    ],
  })

  sections.value = result
}

onMounted(() => {
  runTests()
})
</script>

<template>
  <div class="browser-test">
    <h1>浏览器兼容性测试</h1>
    <section v-for="section in sections" :key="section.title" class="test-section">
      <h2>{{ section.title }}</h2>
      <table>
        <tbody>
          <tr v-for="item in section.items" :key="item.label">
            <td>{{ item.label }}</td>
            <td :class="[item.pass === false ? 'fail' : 'pass']">{{ item.value }}</td>
          </tr>
        </tbody>
      </table>
    </section>
  </div>
</template>
```
