# SSH 部署

## 凭据和 Runner

- 私钥留在专用部署 Runner 的宿主机，由 Docker Runner 只读挂载到部署容器，例如 `/opt/ci-secrets/id_ed25519:/run/secrets/deploy_key:ro`。宿主机私钥归 root 所有且权限 `0600`；容器内部署脚本只检查可读性和权限，不输出私钥内容。
- `fe-build` Runner 不应挂载或访问部署私钥。只有 tag 匹配 `fe-deploy` 的 job 才能使用。
- 不要将私钥、口令、Webhook 写进仓库、Artifact 或 job 日志。当前项目的 GitLab CI/CD 变量只需要企业微信 `WECOM_BOT_WEBHOOK`；即使别的项目必须使用 CI secret，也应最小授权、隐藏并保护。
- 私钥对应的公钥必须预先安装在每个目标服务器的目标账号上。增加服务器时，确认公钥授权、账号权限、目标目录写权限和网络 ACL；“Runner 有私钥”本身不会自动授权访问新主机。

## 主机身份和命令边界

- 将经带外核验的 SSH host key 固定在部署配置中。连接时使用 `StrictHostKeyChecking=yes` 和独立的临时 `known_hosts`；禁止 `StrictHostKeyChecking=no`，也不要在每次部署时无验证地信任 `ssh-keyscan` 结果。
- 部署账号遵循最小权限。优先使用专用非 root 账号，仅能写目标发布目录；可用 forced command 限制到固定接收器，并禁用端口转发、Agent 转发和伪终端。
- 本项目开发环境已有 forced-command 接收模式；测试和生产配置当前仍使用 `root`。这是现状，不是新增项目的规范。新环境不应复制 root 登录。
- 当前部署脚本用 tar 经 SSH 标准输入传输 Artifact；远端命令使用严格引用和失败即停止。部署镜像应预装 ssh/tar，避免在流水线里临时安装。
- 不要把 SSH 错误输出、`set -x` 或调试打印扩展到密钥内容、Webhook 或认证数据。

## 上线前检查

1. 确认 Runner tag 指向部署 Runner，挂载密钥路径只读且文件权限合规。
2. 确认选中的环境存在，host/port/user/target/host key 合法；不从任意流水线变量拼接主机或 shell 命令。
3. SSH 使用 pinned host key 建连；远端只接收预期 Artifact，校验包结构和入口文件。
4. 上传后检查入口文件和应用健康地址，再报告部署成功。

如果 SSH 连接失败，先分别检查 Runner 排队状态、容器内 ssh 客户端、密钥挂载、目标公钥授权、host key 和网络连通；不要旋转 Runner token 来解决 SSH 认证问题。
