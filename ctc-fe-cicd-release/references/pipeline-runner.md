# Pipeline 与 Runner

## 推荐流水线

新项目优先采用以下阶段：

1. **validate**：MR 和受支持分支运行 lint、类型检查及单元测试；不要让部署通知代替质量门禁。
2. **build**：对提交构建一次，生成带提交 SHA 的不可变 Artifact。部署 job 只下载它，不重新安装依赖或重新构建。
3. **deploy**：由一个通用 job 接受已校验的 `DEPLOY_ENVIRONMENT`，按所选目标发布同一个 Artifact。若 GitLab 版本不能在手动 job 上安全收集变量，用支持的 pipeline inputs 或受控的环境 job matrix；不要复制每套环境的构建脚本。
4. **notify**：部署成功后发送通知。通知 job 必须 `needs` 对应的 deploy job，并沿用同一个 `DEPLOY_ENVIRONMENT`；不能只依赖整条 pipeline 的成功状态，否则无法保证通知描述的是实际发布目标。通知失败不能把已经成功的部署说成失败，也不能自动触发二次部署或回滚。

## 通知触发规则

- 当前项目只在对应环境的 deploy job 成功后发送企业微信通知：`notify-wecom-development → deploy-development`、`notify-wecom-test → deploy-test`、`notify-wecom-production → deploy-production`。GitLab 默认成功条件加上 `needs` 依赖意味着 validate、build 或 deploy 失败时不会发送“部署成功”通知。
- 当前通知 job 使用 `allow_failure: true`，因此 webhook 故障不会把已成功部署标记为失败；但应在 job 日志里保留不含 webhook 值的错误信息，方便排查通知本身。
- 当前通知 job 的 branch rules 分别限制为 `dev`、`test`、`main`。生产 deploy 手动成功后才会触发生产通知。
- 成功通知应包含项目、环境、访问 URL、分支、提交人、短 SHA、提交标题和 Pipeline URL；不得包含密钥或 webhook URL。
- 当前没有失败通知。若团队要求失败通知，单独增加 `when: on_failure` 通知 job，并明确去重与责任人；不能复用“部署成功”文案，也不能让通知失败触发重试部署。

生产环境使用受保护的 environment 和人工触发。开发环境是否 push 后自动部署由团队明确决定；无论采用哪种触发方式，环境选择必须落到固定 allowlist，不能直接把任意用户输入拼成主机或远端命令。

同一提交从测试晋级到生产时，尽量使用同一 Artifact，并记录 commit SHA、Pipeline URL、目标环境和 Artifact 标识。Artifact 留存时间要覆盖团队的发布与回滚窗口。

## Runner 职责

| Tag | 用途 | 凭据 |
| --- | --- | --- |
| `fe-build` | 依赖安装、质量检查和构建 | 不挂载部署私钥 |
| `fe-deploy` | 下载 Artifact、配置运行时环境并 SSH 发布 | 仅部署 job 可读部署私钥 |

本团队已使用 6.243 上的 Docker Executor，并以 `fe-build-01/02`、`fe-deploy-01/02` 分摊任务。GitLab job 的 tag 必须与可用 Runner 对齐；排队时检查 Runner 是否 online、是否被锁定到项目/群组、是否允许受保护分支、并发数和 tag，而不是盲目增加 CI 重试。

## 缓存与耗时

- Node/pnpm 版本固定，安装使用 lockfile frozen 模式。
- 将 pnpm store、Corepack 下载缓存和 Turbo 缓存放到 Runner 宿主机持久卷；缓存路径要按项目隔离。
- 只有确认可安全复用后，才从 Git 清理范围中排除 `node_modules/`、`.turbo/`、`.pnpm-store/` 等目录。检查缓存权限、runner 并发工作目录隔离和依赖锁文件一致性。
- 记录每个阶段耗时和缓存命中情况。该项目曾因构建缓存没有跨 job/清理周期保留而接近 25 分钟；恢复 Runner 缓存后，整条流水线曾降至约 4 分钟。把它当作性能排查证据，不保证其他仓库可达到相同耗时。
- 普通 CI 镜像应包含部署/打包需要的系统工具。不要依赖 job 运行时从不稳定软件源安装 SSH 客户端；Alpine TLS 源故障已导致部署重试失败。当前部署 job 使用 Debian Bookworm Node 镜像和 tar/ssh 流式传输。

## 当前仓库差异

当前 `self-monitor-system/.gitlab-ci.yml` 是 `dev`、`test`、`main` 三个命名 build/deploy job；`dev` 和 `test` 自动发布，`main` 发布手动触发。推广到新项目前，应以单次构建 Artifact + 通用环境选择为目标进行迁移，不要把当前复制 job 的结构误作最终通用规范。
