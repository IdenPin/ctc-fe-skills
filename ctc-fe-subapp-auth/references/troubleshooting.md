# 踩坑避雷与防御性编程指南

本分册总结子应用在接入 `@ctc-front/gf-framework-auth` 和 `@ctc-front/bridge-next` 过程中的高频踩坑点与防御性编码规范。

## 一、生命周期陷阱

### 1. Vue 2 严禁在 `beforeCreate` 中调用 methods / 同步方法
- **现象**：控制台抛出 `TypeError: this.syncFrameworkToken is not a function`。
- **根因**：Vue 2 的 `beforeCreate` 阶段尚未执行 `initState`，`methods` 和 `data` 尚未绑定到实例上下文。
- **规范（MUST）**：`this.syncFrameworkToken()` 和 `frameworkAuth.subscribe` 必须在 `created()` 钩子中执行。

### 2. Vue 3 避免在组件挂载前发起不可控副作用
- **现象**：SSR 或提前执行的代码中访问 `localStorage` / `window.location` 报错。
- **规范（SHOULD）**：使用 `useFrameworkAuth` 时，将会话订阅和初始同步放在 `onMounted` 钩子中进行，卸载时通过 `onBeforeUnmount` 自动释放订阅。

## 二、页面加载与防白屏死锁

### 1. 首屏初始化必须包裹 `try / catch / finally`
- **现象**：当用户通过外部链接打开携带已过期 Token 的 URL，或者网络波动导致初始接口抛错时，页面永久停留在 Loading/骨架屏状态。
- **根因**：首屏初始请求抛出异常或 401 被挂起，未被 `catch` 捕获，导致 `isLoaded = true` 永远无法执行。
- **规范（MUST）**：首屏加载逻辑必须用 `try ... catch ... finally` 包裹，确保无论成功、失败还是续租重试中，`isLoaded` 必须在 `finally` 中被置为 `true`：
  ```javascript
  try {
    if (currentToken && this.fetchUserInfo) {
      await this.fetchUserInfo()
    }
  } catch (err) {
    console.warn('[App] 初始化用户信息失败:', err)
  } finally {
    this.isLoaded = true // 杜绝白屏死锁
  }
  ```

## 三、Axios 拦截器顺序与响应守卫

### 1. 拦截器挂载顺序：`attachAxios` 必须先于业务响应拦截器
- **现象**：接口返回 401 无法被静默挂起并进入重试队列，直接弹出了“未登录”并跳转或强行退出。
- **根因**：Axios 的 response 拦截器是 FIFO（先入先出）执行的。如果业务拦截器先挂载，会先一步将 401 当作业务异常抛出（`Promise.reject`），导致 SDK 的挂起拦截器无法接管。
- **规范（MUST）**：必须先执行 `frameworkAuth.attachAxios(service, options)`，再执行 `service.interceptors.response.use(...)`。

### 2. 解包拦截器防重复执行：添加响应对象结构守卫
- **现象**：401 重试成功后的请求返回报错，或报 `TypeError: Cannot read properties of undefined`。
- **根因**：SDK 挂起的重试请求由 Axios 重新发出，响应会完整再次走过子应用的拦截器链。若子应用在第一次通过时已经把 `res.data` 解包为普通业务数据对象，重复解包会导致取不到内层数据。
- **规范（MUST）**：在业务 response 拦截器开头必须添加守卫，防止已解包对象被二次处理：
  ```javascript
  service.interceptors.response.use(
    res => {
      // 防御已解包数据重复进入拦截器
      if (res && res.code !== undefined && !res.request && !res.headers) {
        return res
      }
      // 后续正常解包逻辑...
    }
  )
  ```

## 四、通信与会话同步

### 1. 严禁在 401 拦截器中自行向基座发送强退消息
- **现象**：401 静默续租过程中，基座直接发生闪退或强制退出登录。
- **根因**：历史老代码在业务拦截器捕获 401 时主动调用了 `postMessage({ __type__: 'doLogout' })`。
- **规范（MUST）**：接入新 SDK 后，401 请求交给 `attachAxios` 统一通知基座续租；业务拦截器在确认最终失败（超过重试次数）前，不得擅自触发强退广播。

### 2. 本地开发独立运行支持
- **现象**：脱离微前端基座独立本地联调（`localhost` 运行）时频繁提示未授权。
- **规范（SHOULD）**：本地开发时可通过 Mock 或在 `common/utils/frameworkAuth.js` 中支持环境变量注入模拟 Token，确保子应用具备单兵调试能力。
