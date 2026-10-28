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
- 把环境名作为受校验的输入；部署脚本只接受仓库环境配置中已定义的名称。
- 将 Runner 分为构建和部署职责：`fe-build` 只构建与校验，`fe-deploy` 才能访问 SSH 部署密钥。
- 前端运行时配置和部署目标配置分开。浏览器配置可以公开；SSH 私钥、Webhook 和口令不能进入前端文件、Artifact、日志或仓库。
- 发布前确认目标环境、分支/提交、Artifact 和回滚路径。生产发布使用受保护环境和人工触发。
- 不声称已经有回滚能力，除非部署实现保留了可恢复版本并验证过切换流程。

## 工作流程

1. 识别当前状态：检查流水线 job 和 rules、Runner tags/执行器、缓存、Artifact、部署脚本、环境配置、通知变量与回滚方式。
2. 将发现分为“当前已实现”“本次建议/目标”“尚未实现”。不要将旧 README、架构草图或单次成功记录当成实时事实。
3. 先定义环境选择与配置来源，再调整 CI YAML，避免把主机、API 地址、凭据和分支规则重复维护在多处。
4. 部署脚本应校验输入与目标；SSH 使用固定主机指纹校验；发布后检查服务可访问和关键资源有效。
5. 按请求执行验证。未获用户要求时不触发远端部署、生产发布、密钥轮换或 Runner 配置变更。
6. 汇报实际修改、验证证据、未实现的能力和操作风险，尤其说明回滚是否真实可用。

## 本团队已确认的架构约定

- GitLab Runner 运行在 192.168.6.243（6.243）上的 Docker Executor。构建 job 使用 `fe-build`，部署 job 使用 `fe-deploy`。
- 构建缓存放在 Runner 宿主机挂载卷；在清理工作区时只保留经确认可复用的依赖和构建缓存，避免缓存失效导致流水线从数分钟退化到二十多分钟。
- 部署私钥由部署 Runner 宿主机只读挂载到 job 容器 `/run/secrets/deploy_key`；GitLab 项目只保留必要的 `WECOM_BOT_WEBHOOK` 变量。不得将私钥值写进 CI/CD 变量、代码或日志。
- `public/config.env.js` 维护浏览器可见的环境配置；部署时按环境选出一份配置写入产物。`deploy/serviceConfig.json` 维护 SSH 主机、端口、用户、固定 host key、目标目录和访问 URL，不放前端 `runtimeConfig`。
- 当前 `self-monitor-system` 流水线仍按 `dev`、`test`、`main` 分别构建；生产 job 是手动触发。它尚未完全切换到“一个 Artifact 部署到任意环境”的单一通用 deploy job。为其他项目制定目标方案时可采用单次构建模式，但说明并迁移这项差异。
- 现有 `deploy/deploy.mjs` 会清空目标目录后解包，当前实现不提供版本目录或原子回滚。生产级规范应先补足可恢复发布机制，不能把 GitLab Artifact 留存误称为服务器自动回滚。
- `scripts/deploy/README.md` 仍记录旧的 5.140 地址及 `DEV_SSH_PRIVATE_KEY`/`DEV_SSH_KNOWN_HOSTS` 变量方案；它与当前流水线、Runner 主机和部署配置不一致。修改该 README 前以当前 `.gitlab-ci.yml` 与 `deploy/` 中的实现核对，并同步更新文档。

## 按需读取

- Pipeline 与 Runner 设计、缓存、Artifact 和规则：读 [references/pipeline-runner.md](references/pipeline-runner.md)。
- 私钥挂载、SSH 校验和部署账号约束：读 [references/ssh-deployment.md](references/ssh-deployment.md)。
- `config.env.js`、`serviceConfig.json` 和环境选择：读 [references/environment-config.md](references/environment-config.md)。
- 发布保留、回滚和当前能力边界：读 [references/rollback.md](references/rollback.md)。
