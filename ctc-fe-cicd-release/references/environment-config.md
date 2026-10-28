# 环境配置

## 配置职责

- `apps/<app>/public/config.env.js`：浏览器运行时需要的公开配置，例如 API base path、公共站点路径或功能开关。按环境集中维护，通过 `DEPLOY_ENVIRONMENT` 选择一份并写入最终 Artifact。
- `deploy/serviceConfig.json`：部署目标元数据，例如 host、port、sshUser、固定 host key、远端 target 和访问 URL。不要在这里再复制前端 `runtimeConfig`。
- GitLab CI variables：只存真正需要保密的值，如 Webhook 或不可避免的凭据。公共 API 地址不是秘密；浏览器能访问的任何值都不能作为密钥处理。

当前 `self-monitor-system` 用 `window.__CTC_ENV_CONFIGS__` 保存各环境配置，部署脚本从 `public/config.env.js` 读取 map，再将所选环境的对象写入构建产物的 `config.env.js`。`index.html` 在应用模块启动前加载该文件。应用配置读取逻辑在生产环境让 `window.__CTC_ENV__` 覆盖构建时注入值；本地开发仍以 `import.meta.env` 为准。

已知环境地址：测试 API 为 `/zxjcjg-test-api/admin-api`；开发和生产目前沿用 `/zxjcjg-api/admin-api`。当后端路径变更时更新运行时配置 map，并检查所有 API、上传、WebSocket、Swagger、监控页和文件 URL 是否走同一配置 helper。

## 新增环境

1. 给 `serviceConfig.json` 增加 host、port、sshUser、经核验 host key、target 和 url。
2. 给 `public/config.env.js` 环境 map 增加同名配置；公共默认相同的字段可以复用 `sharedConfig`，差异只覆盖需要改变的字段。
3. 在 GitLab 受控的环境选择中允许该环境名；部署脚本必须验证它同时存在于目标配置和前端环境配置中。
4. 确认对应服务器的授权公钥、Runner 网络可达性、Nginx 静态目录、API 反向代理和健康检查。
5. 用测试环境验证最终产物中的 `config.env.js` 只含所选环境的公开配置，再发布到生产。

环境配置要做 allowlist 校验。`config.env.js` 是公开资源；不得放 private key、数据库密码、Webhook、登录凭据或需要保密的加解密密钥。构建环境变量也会进入浏览器产物时，不能因此视作私密。
