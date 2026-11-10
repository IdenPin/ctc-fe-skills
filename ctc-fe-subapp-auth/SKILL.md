---
name: ctc-fe-subapp-auth
description: >
  微前端或 iframe 子应用接入集团基座鉴权与 Token 静默续租标准规范。涵盖 @ctc-front/gf-framework-auth 与 @ctc-front/bridge-next，适配 gf-monitor 和 gf-law 等基座平台。用于处理 401 并发挂起、通知基座续租、重试队列、状态库双向同步及防白屏异常处理。
metadata:
  author: ctc-front
  version: "1.0.0"
---

# CTC 微前端子应用鉴权与静默续租规范

本规范适用于所有作为 iframe 或微前端子应用接入集团各基座平台（如 `gf-monitor` 重点排污单位监控基座、`gf-law` 移动执法/法治基座）的前端业务系统。

核心目标是提供标准化的会话接入、401 并发静默续租、跨层状态双向同步以及防御性异常处理，杜绝 Token 过期导致的突发白屏与无感中断。

## 适用技术栈与框架无关性

- **核心 SDK**：`@ctc-front/gf-framework-auth@0.3.0` 与 `@ctc-front/bridge-next@0.2.0`。
- **框架中立**：SDK 内部未打包任何 UI 框架运行时，100% 完整支持 **Vue 2（Options API + Vuex）** 与 **Vue 3（Composition API + Pinia / Vuex 4）**。
- **构建适配**：开箱兼容 Vite、Webpack 4 与 Webpack 5 构建体系。

## 基座平台与 StorageKey 矩阵（速查）

| 基座平台名称 | 基座代码标识 | 基座 LocalStorage Key | 典型接入子应用 |
| :--- | :--- | :--- | :--- |
| **重点排污单位监控系统** | `gf-monitor` | `monitor-user-info` *(默认)* | `zdjk-system`、`zdjk-cockpit` |
| **生态环境移动执法/法治系统**| `gf-law` | `law-user-info` | `shj-fxc-biz` |

> 接入前务必确认子应用所挂载的目标基座。若挂载到 `gf-law`，必须显式配置 `storageKey: 'law-user-info'`。详细平台实践见 [references/platforms.md](references/platforms.md)。

## 接入核心流程与规范（MUST）

子应用接入基座鉴权必须遵循以下 6 步标准流程：

```mermaid
flowchart TD
    Step1["1. 确认基座类型 & StorageKey"] --> Step2["2. 安装 SDK 依赖"]
    Step2 --> Step3["3. 封装 appBridge 通信模块"]
    Step3 --> Step4["4. 初始化 frameworkAuth 客户端"]
    Step4 --> Step5["5. Axios attachAxios 挂载 & 拦截器防二次解包"]
    Step5 --> Step6["6. App.vue 生命周期绑定 & 状态双向同步 (防白屏死锁)"]
```

### 1. 依赖安装

使用团队私有 npm 仓库安装正式稳定版：

```bash
# pnpm
pnpm add @ctc-front/gf-framework-auth@0.3.0 @ctc-front/bridge-next@0.2.0

# npm
npm install @ctc-front/gf-framework-auth@0.3.0 @ctc-front/bridge-next@0.2.0 --save
```

### 2. 通信模块与客户端初始化

- **appBridge 封装**：创建 `src/common/utils/appBridge.js`，管理与基座的消息通道、Token 失效通知（`notifyTokenExpired`）与基座登出回调。参见模板 [references/templates/appBridge.js](references/templates/appBridge.js)。
- **frameworkAuth 客户端**：创建 `src/common/utils/frameworkAuth.js`，按所属基座传入正确的 `storageKey`，并将 Bridge 会话注入。参见模板 [references/templates/frameworkAuth.js](references/templates/frameworkAuth.js)。

### 3. Axios 拦截器改造（MUST 门禁）

在 `src/common/utils/request.js` 中改造拦截器逻辑，必须满足以下硬性条件：

1. **挂载顺序**：`frameworkAuth.attachAxios(service, options)` **必须在自定义业务响应拦截器之前调用**。Axios response 拦截器按 FIFO 执行，若业务拦截器先执行会将 401 提早当做错误 reject，导致 SDK 重试队列无法接管。
2. **防二次解包守卫**：重试成功的请求会重新穿透整个响应拦截器链。必须在响应拦截器开头添加守卫判断（如 `if (res && res.code !== undefined && !res.request && !res.headers) return res`），避免解包后的数据再次解包导致 undefined 异常。
3. **未授权识别**：准确配置 `isUnauthorized` 规则，覆盖 HTTP 401/402/403 及网关业务码（如 `40108`）。

参见标准实现 [references/templates/request.snippet.js](references/templates/request.snippet.js)。

### 4. 状态双向同步与防白屏死锁（MUST 门禁）

在根组件（`App.vue`）中建立会话同步：

1. **初始同步**：初始化时从基座 LocalStorage 及 URL 参数（`t__` / `token`）同步初始 Token 至状态库（Pinia / Vuex）。
2. **续租订阅**：通过 `frameworkAuth.subscribe` 监听基座续租广播，Token 更新时双向写回状态库。
3. **防死锁保护**：首屏获取用户信息或初始字典时，**必须使用 `try ... catch ... finally` 包裹**，并在 `finally` 中保证骨架屏状态标记（如 `isLoaded`）置为 `true`，防止首屏请求因 401 挂起或网络故障导致页面永久停留在加载动画中。
4. **Vue 2 生命周期禁忌**：Vue 2 下严禁在 `beforeCreate` 中调用 methods 进行鉴权同步，必须在 `created` 中执行。

- Vue 3 实现模板：[references/templates/vue3/App.vue.snippet.vue](references/templates/vue3/App.vue.snippet.vue) 与 [references/templates/vue3/useFrameworkAuth.ts](references/templates/vue3/useFrameworkAuth.ts)
- Vue 2 实现模板：[references/templates/App.vue.snippet.vue](references/templates/App.vue.snippet.vue)

## 规范等级与检查清单

| 规则 | 等级 | 说明 |
| :--- | :---: | :--- |
| 同源反向代理部署 | MUST | 基座与子应用必须部署在同源同域下，否则 LocalStorage 事件与 Bridge 通信均失效 |
| 正确配置 storageKey | MUST | 严禁在 `gf-law` 基座项目中使用默认的 `monitor-user-info` |
| attachAxios 前置挂载 | MUST | 必须优先于业务响应拦截器执行 |
| 响应拦截器防二次解包 | MUST | 对已解包结构增加对象守卫 |
| 初始加载 try/finally | MUST | 首屏骨架屏加载必须在 finally 中结束，杜绝白屏死锁 |
| 禁止 401 主动强退 | MUST | 静默续租阶段禁止向基座主动发出 doLogout 广播，避免冲刷基座正常重试流程 |
| Pinia / Vuex 状态同步 | SHOULD | 会话变更时及时更新应用内用户状态，保持单向数据流一致 |

## 分册索引（按需调阅）

- 📌 基座平台矩阵、StorageKey 对照与改造备忘录 → 读 [references/platforms.md](references/platforms.md)
- 📌 踩坑避雷清单、生命周期陷阱与防御性编程守则 → 读 [references/troubleshooting.md](references/troubleshooting.md)
- 📌 Vue 2 / Vue 3 标准接入代码模板目录 → 查阅 [references/templates/](references/templates/)
