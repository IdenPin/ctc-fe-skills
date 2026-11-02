# Pipeline 与 Runner

## 推荐流水线

新项目优先采用以下阶段：

1. **validate/build**：MR 可运行独立质量检查 Job。对需要打包的分支 Push，将依赖安装、质量检查和构建放在同一个 Job/容器里按顺序执行；检查失败时 Job 立即失败，不开始构建。这样构建复用质量检查已安装的 `node_modules`，也避免两个重型 Job 并行争用 Runner 资源。
2. **Artifact**：对提交构建一次，生成带提交 SHA 的不可变 Artifact。部署 job 只下载它，不重新安装依赖或重新构建。
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

## Pipeline 与 job 触发规则

- `workflow: rules` 决定是否创建整条 Pipeline；job 自己的 `rules` 决定 Pipeline 中是否出现该 job。排查“没有流水线”先看 workflow，排查“流水线里缺少部署/通知节点”再看对应 job 的 rules 和依赖。
- 分支 push 使用 `CI_COMMIT_BRANCH`；合并请求的目标分支使用 `CI_MERGE_REQUEST_TARGET_BRANCH_NAME`。不要用源分支变量判断 MR 的目标，也不要仅因一个 job 有 rules 就假设 Pipeline 一定会被创建。
- 先把需求写清楚：哪些 `CI_PIPELINE_SOURCE` 应触发、匹配源分支还是 MR 目标分支、需要哪些 job。若“所有以 test 开头的分支”，`/^test.*$/` 会匹配 `test`、`test/6.243` 和 `test-foo`；若只接受 `test/` 命名空间，使用 `^test/.*$`。向用户举例确认语义，不要把 `test*` 和 `test/*` 当作相同范围。
- 如果 push 和 MR 都应触发，workflow 必须分别允许 `push` 与 `merge_request_event`，MR 条件按目标分支判断。确认同一 push 在存在开放 MR 时是否允许产生 push 和 MR 两条 Pipeline；不要为了消除重复而悄悄丢掉用户要求的触发类型。
- `when: never` 会拒绝此前未匹配的流水线来源。修改 workflow 时同时检查手动 `web` Pipeline 是否仍需要，以及“合并后手动部署”应从哪个来源的 Pipeline 提供入口。
- `when: manual` 的部署/回滚 job 也要允许期望的来源（例如 `push` 或 `web`），并与该 job 对应环境的分支精确匹配。逐个核对环境名、branch rule、`environment.name`、`resource_group` 和部署目标；复制 job 时特别检查是否误把相邻环境分支写入条件（例如 6.243 环境 job 误匹配到 5.7 分支）。不存在匹配 Pipeline 的手动作业不会显示为可点击按钮。
- H5 构建命令以 `package.json` 的 scripts 为准；CI 调用对应的包脚本（例如 `pnpm run build`），不要保留已删除或改名的旧命令。同步 README、本地复现说明和 Artifact 路径。

## 通知作业可见性与变量

- `after_script` 在所属 job 的结束流程中执行，只会显示在该 job 的日志里，不会成为单独的 Pipeline 节点。若用户需要看到通知节点，使用独立 notify job，并明确 `needs`、`when`、成功/失败条件和 `allow_failure`；若只要求通知结果随部署日志可查，`after_script` 可以满足。
- 企业微信通知脚本若在发请求前因 `WECOM_BOT_WEBHOOK` 未设置或为空而退出，说明变量没有进入该 job，不能据此判断 webhook 网络或地址错误。检查 key 是否准确、变量是否非空、Protected variable 是否可用于该 ref，以及 Environment scope 是否匹配该 job 的 `environment.name` 或 `*`。不得打印变量值来验证。
- 若通知失败不能改变部署结果，在脚本或独立通知 job 中明确设置非阻塞行为，并让日志保留可诊断错误。区分通知发送失败与部署/回滚失败；失败通知应使用自己的状态和文案，不能宣称部署成功。
- 更改脚本目录、配置文件名或包命令后，搜索整个仓库中的旧路径/旧命令，并更新 CI YAML、package scripts、测试、README 和相对导入。核对远端实际运行的 commit 中是否已包含这些变更；未提交到远端的修改不会改变 GitLab 行为。

## Runner 职责

| Tag | 用途 | 凭据 |
| --- | --- | --- |
| `fe-build` | 依赖安装、质量检查和构建 | 不挂载部署私钥 |
| `fe-deploy` | 下载 Artifact、配置运行时环境并 SSH 发布 | 仅部署 job 可读部署私钥 |

本团队已使用 6.243 上的 Docker Executor，并以 `fe-build-01/02`、`fe-deploy-01/02` 分摊任务。GitLab job 的 tag 必须与可用 Runner 对齐；排队时检查 Runner 是否 online、是否被锁定到项目/群组、是否允许受保护分支、并发数和 tag，而不是盲目增加 CI 重试。

## 缓存与耗时

- Node/pnpm 版本固定，安装使用 lockfile frozen 模式。
- Docker Executor 下每个 Job 有独立容器和工作目录；不同 Job 不会自动共享 `node_modules`。pnpm store cache 命中也只减少包下载，不代表项目工作目录已有安装好的依赖。若质量检查是打包门禁，不要让 validate 与 build 成为相互独立、可并行的 Job；避免给 build 配置 `needs: []`。
- 若 MR 只需质量检查，可保留 MR 专用的 `quality-gate`；分支 Push 的构建 Job 自身应先执行相同质量脚本，再构建。部署 Job 只依赖包含质量检查和构建的 Artifact Job，不要再依赖 MR 专用质量 Job。
- 将 pnpm store、Corepack 下载缓存和 Turbo 缓存放到 Runner 宿主机持久卷；缓存路径要按项目隔离。
- 只有确认可安全复用后，才从 Git 清理范围中排除 `node_modules/`、`.turbo/`、`.pnpm-store/` 等目录。检查缓存权限、runner 并发工作目录隔离和依赖锁文件一致性。
- 记录每个阶段耗时和缓存命中情况。该项目曾因构建缓存没有跨 job/清理周期保留而接近 25 分钟；恢复 Runner 缓存后，整条流水线曾降至约 4 分钟。把它当作性能排查证据，不保证其他仓库可达到相同耗时。
- 普通 CI 镜像应包含部署/打包需要的系统工具。不要依赖 job 运行时从不稳定软件源安装 SSH 客户端；Alpine TLS 源故障已导致部署重试失败。当前部署 job 使用 Debian Bookworm Node 镜像和 tar/ssh 流式传输。

## 当前仓库差异

当前 `self-monitor-system/.gitlab-ci.yml` 是 `dev`、`test`、`main` 三个命名 build/deploy job；`dev` 和 `test` 自动发布，`main` 发布手动触发。推广到新项目前，应以单次构建 Artifact + 通用环境选择为目标进行迁移，不要把当前复制 job 的结构误作最终通用规范。
