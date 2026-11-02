---
name: ctc-fe-cicd-release
description: >
  设计、评审或维护 CTC 前端项目的 GitLab Pipeline、Runner、SSH 发布、运行时环境配置和回滚流程时使用。
  适用于新项目接入 CI/CD、增加部署环境、排查流水线变慢或部署失败，以及制定发布规范；不用于普通业务代码构建。
metadata:
  author: pdeng
  version: "1.0.0"
---

# CTC Frontend CI/CD Release

将前端构建、环境选择和远端发布分开管理。开始修改前先检查当前仓库的 `.gitlab-ci.yml`、Runner tags、部署脚本、环境配置和项目说明；仓库文件优先于历史描述。若说明文档与正在执行的流水线不一致，指出差异并修正文档或明确规范目标，不能把计划当成已落地能力。

## 规范原则

- 对新接入项目，优先采用“同一提交构建一次、Artifact 固定保存、部署时选择环境”的流水线，避免每增加一个环境就复制一套 build/deploy job。
- 当质量检查是打包前置门禁且两步使用同一套依赖时，将质量检查和打包放在同一个 Job/容器中，顺序执行“安装依赖 → 质量检查 → 打包”，让打包复用已安装的 `node_modules`。质量检查失败必须立即终止该 Job，不能启动打包。
- 不要依赖不同 Job 自动共享 `node_modules`：Docker Executor 为每个 Job 创建独立容器和工作目录。若 MR 需要单独质量检查，可保留 MR 专用质量 Job；分支 Push 的打包 Job 应自行先完成质量检查，再执行打包。避免用 `needs: []` 让打包绕过质量门禁。
- 把环境名作为受校验的输入；部署脚本只接受仓库环境配置中已定义的名称。
- 将 Runner 分为构建和部署职责：`fe-build` 只构建与校验，`fe-deploy` 才能访问 SSH 部署密钥。
- 前端运行时配置和部署目标配置分开。浏览器配置可以公开；SSH 私钥、Webhook 和口令不能进入前端文件、Artifact、日志或仓库。
- 遵守团队目录和命名约定：CI/CD 构建与部署辅助脚本、部署目标配置及流水线说明放在仓库根目录 `deploy/`；配置文件使用 kebab-case，例如 `service-config.json`。测试仍放在测试目录。移动文件时同步更新 CI YAML、`package.json`、文档、测试引用和相对路径。
- 发布前确认目标环境、分支/提交、Artifact 和回滚路径。生产发布使用受保护环境和人工触发。
- 不声称已经有回滚能力，除非部署实现保留了可恢复版本并验证过切换流程。

## 工作流程

1. 识别当前状态：检查流水线 job 和 rules、Runner tags/执行器、缓存、Artifact、部署脚本、环境配置、通知变量与回滚方式。记录触发来源、分支、目标分支、提交 SHA，并以该提交里的 `.gitlab-ci.yml` 为准；本地尚未提交的规则不会影响远端流水线，推送配置也不会补跑之前的提交。
2. 将发现分为“当前已实现”“本次建议/目标”“尚未实现”。不要将旧 README、架构草图或单次成功记录当成实时事实。
3. 先定义环境选择与配置来源，再调整 CI YAML，避免把主机、API 地址、凭据和分支规则重复维护在多处。确认质量门禁是否阻塞打包；需要复用依赖时让检查与打包在同一 Job 中串行执行，部署仅依赖该 Job 的 Artifact。
4. 部署脚本应校验输入与目标；SSH 使用固定主机指纹校验；发布后检查服务可访问和关键资源有效。
5. 按请求执行验证。未获用户要求时不触发远端部署、生产发布、密钥轮换或 Runner 配置变更。
6. 汇报实际修改、验证证据、未实现的能力和操作风险，尤其说明回滚是否真实可用。

## 本团队已确认的架构约定

- GitLab Runner 运行在 192.168.6.243（6.243）上的 Docker Executor。构建 job 使用 `fe-build`，部署 job 使用 `fe-deploy`。
- 构建缓存放在 Runner 宿主机挂载卷；在清理工作区时只保留经确认可复用的依赖和构建缓存，避免缓存失效导致流水线从数分钟退化到二十多分钟。
- 部署私钥由部署 Runner 宿主机只读挂载到 job 容器 `/run/secrets/deploy_key`；GitLab 项目只保留必要的 `WECOM_BOT_WEBHOOK` 变量。不得将私钥值写进 CI/CD 变量、代码或日志。
- `public/config.env.js` 维护浏览器可见的环境配置；部署时按环境选出一份配置写入产物。`deploy/service-config.json` 维护 SSH 主机、端口、用户、固定 host key、目标目录和访问 URL，不放前端 `runtimeConfig`。
- 当前 `self-monitor-system` 流水线仍按 `dev`、`test`、`main` 分别构建；生产 job 是手动触发。它尚未完全切换到“一个 Artifact 部署到任意环境”的单一通用 deploy job。为其他项目制定目标方案时可采用单次构建模式，但说明并迁移这项差异。
- 现有 `deploy/deploy.mjs` 会清空目标目录后解包，当前实现不提供版本目录或原子回滚，且发布瞬间破坏在途请求，导致仍在使用旧页面的用户请求不到旧 hash chunk 资源引发报错。生产级规范应采用多版本独立目录与原子软链切换（配合 Nginx 放行软链），并保留历史版本以平滑过渡，不能把 GitLab Artifact 留存误称为服务器自动回滚。
- `self-monitor-system` 仓库根目录的 `deploy/README.md` 仍记录旧的 5.140 地址及 `DEV_SSH_PRIVATE_KEY`/`DEV_SSH_KNOWN_HOSTS` 变量方案；它与当前流水线、Runner 主机和部署配置不一致。修改该 README 前以当前 `.gitlab-ci.yml` 与 `deploy/` 中的实现核对，并同步更新文档。

## 按需读取

- Pipeline 与 Runner 设计、缓存、Artifact 和规则：读 [references/pipeline-runner.md](references/pipeline-runner.md)。
- 私钥挂载、SSH 校验和部署账号约束：读 [references/ssh-deployment.md](references/ssh-deployment.md)。
- `config.env.js`、`service-config.json` 和环境选择：读 [references/environment-config.md](references/environment-config.md)。
- 发布保留、回滚和当前能力边界：读 [references/rollback.md](references/rollback.md)。
