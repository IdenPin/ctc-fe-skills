# 基座平台与接入矩阵

本分册记录团队内各基座平台的技术标识、会话存储键值（`storageKey`）以及典型子应用的适配实践。

## 一、基座平台与 StorageKey 对照表

| 基座平台名称 | 基座代码标识 | 基座 LocalStorage Key | 典型接入子应用 |
| :--- | :--- | :--- | :--- |
| **重点排污单位监控系统** | `gf-monitor` | `monitor-user-info` *(默认)* | `zdjk-system`、`zdjk-cockpit` |
| **生态环境移动执法/法治系统**| `gf-law` | `law-user-info` | `shj-fxc-biz` |

### 核心约束（MUST）

- **同源限制**：基座与子应用必须部署在同一协议、域名、端口下（通过 Nginx 反向代理挂载在相同域名不同路径），方可通过 `localStorage` 事件与 `window.parent` 安全通信。跨域部署将导致会话事件无法被触发，必须由运维层前置解决。
- **匹配正确的 StorageKey**：初始化 `createGfFrameworkAuth` 时必须显式声明所属基座的 `storageKey`。若子应用挂载到 `gf-law` 基座，必须配置为 `'law-user-info'`，不可默认使用 `'monitor-user-info'`。

## 二、已有项目改造对比备忘录

| 项目名称 | 所属基座 | 采用 StorageKey | 接入特色与治理经验 |
| :--- | :--- | :--- | :--- |
| **`zdjk-system`** | `gf-monitor` | `monitor-user-info` | 包含 `gldAuthToken`、`qiyeAuthToken` 多 Token 混合支持场景；全链路 Bridge 消息互通。 |
| **`shj-fxc-biz`** | `gf-law` | `law-user-info` | 仅在 `isOutside` 模式下作为子应用挂载；初始首屏使用 `try/finally` 防白屏死锁。 |
| **`zdjk-cockpit`**| `gf-monitor` | `monitor-user-info` | 移除了旧有 `ctcPostMessage.emit({ __type__: 'doLogout' })` 强退逻辑，替换为 401 挂起等待基座静默续租，避免了定时刷新图表时偶发踢出登录态。 |

## 三、多 Token 混合业务场景治理

在某些跨平台综合业务子系统中，可能同时存在基座全局 Token 与系统特有业务 Token：
1. **基座主会话**：由 `frameworkAuth` 自动提取并用于通用鉴权与续租。
2. **专属业务 Token**：建议在子应用 Store 中独立存放，通过独立的业务请求头传递，不应与 `frameworkAuth` 维护的 `accessToken` 混淆。
3. **续租隔离**：只有基座层级的 401/402 触发 `notifyTokenExpired`；子系统专属第三方鉴权失效需在子系统业务拦截器内独立处理。
