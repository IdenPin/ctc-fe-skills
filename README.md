# CTC FE Skills

`ctcfront` 团队的前端开发规范 Skill 仓库，供团队成员和 AI 编码助手在架构设计、Vue 3 开发和浏览器兼容性评估时按需加载。

[![skills.sh](https://skills.sh/b/IdenPin/ctc-fe-skills)](https://skills.sh/IdenPin/ctc-fe-skills)

当前正式版本：**v1.1.0**。变更内容及升级说明见 [CHANGELOG.md](./CHANGELOG.md)。

## 安装

团队项目建议通过 tag 安装固定版本：

```bash
npx skills add https://github.com/IdenPin/ctc-fe-skills/tree/v1.1.0 -y
```

使用 Vue 规范时，建议同时安装结构规范，以便获取文件归属、目录容量和体积检查规则：

```bash
npx skills add https://github.com/IdenPin/ctc-fe-skills/tree/v1.1.0 --skill ctc-fe-structure --skill ctc-fe-vue3 -y
```

需要体验主分支最新修改时安装全部 skills：

```bash
npx skills add IdenPin/ctc-fe-skills -y
```

按需安装：

```bash
npx skills add IdenPin/ctc-fe-skills --skill ctc-fe-structure -y
npx skills add IdenPin/ctc-fe-skills --skill ctc-fe-vue3 -y
npx skills add IdenPin/ctc-fe-skills --skill ctc-fe-adapt-broswer -y
npx skills add IdenPin/ctc-fe-skills --skill ctc-fe-cicd-release -y
```

上述简写来源跟随默认分支，安装时取得当时内容；已安装的副本不会因仓库更新而自动变更。主分支安装可通过 `npx skills check` 检查更新，再执行 `npx skills update`；固定版本升级时，使用新的 tag URL 重新安装，并核对项目的 `skills-lock.json` 与变更。

安装器会将分册、脚本和 `agents/` 元数据一起安装；不要只复制 `SKILL.md`。使用结构扫描器需要本机 Python 3。

> `ctc-fe-adapt-broswer` 是已发布的历史拼写。为避免破坏现有安装路径暂时保留，后续破坏性版本迁移为 `ctc-fe-adapt-browser`。

## Skills

### [ctc-fe-structure](./ctc-fe-structure/SKILL.md)

用于目录拓扑、业务模块边界、依赖方向和老项目渐进迁移。主要约定：

- 页面流程和易变业务规则就近放入 `features` 或 `views`。
- 无业务语义的 UI、hooks 和工具放入 `shared/ui|lib`。
- `UserSelector`、`DictTag` 等稳定跨模块业务能力放入 `shared/biz`。
- 网络请求、WebSocket 等传输基础设施放入 `services`。
- 统一维护目录容量、文件体积、命名与文件归属约束；新增或扩展模块时先判断子域，防止拆分后继续平铺。
- 随 Skill 分发只读结构扫描器，递归检查同级源码文件数与源码行数，超限返回非零。

分册：[目录结构](./ctc-fe-structure/references/structure.md)、[依赖边界](./ctc-fe-structure/references/boundaries.md)、[命名](./ctc-fe-structure/references/naming.md)、[迁移](./ctc-fe-structure/references/migration.md)、[治理](./ctc-fe-structure/references/governance.md)。

### [ctc-fe-vue3](./ctc-fe-vue3/SKILL.md)

用于 Vue 3 组件职责、拆分条件、组件 API、composable 契约、类型边界、模板渲染、异步交互、样式隔离与组件验收。目录容量与体积阈值引用 `ctc-fe-structure`，不重复维护。规范区分 MUST、SHOULD、MAY：可机械检查的要求交给工具，涉及上下文判断的要求进入 Code Review。

分册：[组件设计](./ctc-fe-vue3/references/component-design.md)、[组合函数](./ctc-fe-vue3/references/composables.md)、[模板与交互](./ctc-fe-vue3/references/template-interaction.md)、[验证与验收](./ctc-fe-vue3/references/validation.md)。

### [ctc-fe-adapt-broswer](./ctc-fe-adapt-broswer/SKILL.md)

用于 Vite/Vue 3 项目的生产构建兼容性诊断。该 skill 明确 Tailwind CSS 4 的现代浏览器基线；对老内核的 CSS 改写属于项目专项实验，必须经过 fixture、视觉回归、关键流程和真实设备验证。

### [ctc-fe-cicd-release](./ctc-fe-cicd-release/SKILL.md)

用于 CTC 前端项目的 GitLab Pipeline、Runner、SSH 部署、运行时环境配置和回滚流程。规范区分已落地能力与建议目标，重点约束 Runner 凭据边界、一次构建多环境发布以及可验证的回滚路径。

分册：[Pipeline 与 Runner](./ctc-fe-cicd-release/references/pipeline-runner.md)、[SSH 部署](./ctc-fe-cicd-release/references/ssh-deployment.md)、[环境配置](./ctc-fe-cicd-release/references/environment-config.md)、[回滚](./ctc-fe-cicd-release/references/rollback.md)。

## 规范等级

- **MUST**：影响正确性、安全、边界或长期维护，必须由工具或明确 Review 门禁执行。
- **SHOULD**：团队默认做法；可以在说明理由后偏离。
- **MAY**：可选建议，由项目上下文决定。

规范不能替代 Code Review、测试和真实环境验收。AI 生成结果同样必须经过项目现有质量门禁。

## 仓库验证

```bash
npm test
```

验证内容包括：Skill frontmatter、skill 名称与目录一致性，以及仓库内 Markdown 相对链接。

发布或更新 skill 前还应在目标项目执行对应的 lint、typecheck、test、build 和业务验收。

## 版本与发布

Skills 通过 GitHub 仓库及 `npx skills add` 分发。`package.json` 的 `version`、Git tag `v<version>`、CHANGELOG 与 GitHub Release 必须对应；不需要将本仓库作为 CLI 包发布到 npm。

1. 核对远端主分支、tags 与 Releases，确定尚未发布的版本号。已写入但未发布的版本可以继续完善；已发布的 tag 不得覆盖。
2. 更新 `package.json`、本页固定版本安装示例和 `CHANGELOG.md`，说明新增约束及升级影响。
3. 执行仓库校验、变更脚本与通用示例检查，在临时项目通过 skills CLI 试装，确认分册、脚本及元数据完整。
4. 提交版本内容，在该提交上创建附注 tag；推送主分支与该 tag，然后创建同名 GitHub Release，发布说明取自 CHANGELOG。
5. 通过远端 tag URL 再次试装，核对版本、安装文件与发布提交。GitHub 自动提供该 tag 对应的源码压缩包。

本仓库发布验证不等于使用项目已符合新约束；消费项目升级后按实际改动执行结构检查及相应验收。已有超限按结构规范渐进处理。

## 维护约定

- `SKILL.md` 只保留触发条件、决策流程和核心规则，详细资料按需放入 `references/`。
- 新增 MUST 规则时，同时说明自动化工具或人工 Review 的执行方式。
- 工具、框架和浏览器版本相关结论必须注明支持范围，并在升级后重新验证。
- 修改 skill 时先用真实任务建立失败基线，再验证调整后的输出；不能只检查 Markdown 格式。
- 仓库版本只在准备发布时更新，发布记录以 Git tag 和 release notes 为准。

## 使用示例

```text
参照 ctc-fe-structure 判断 UserSelector 应放在哪一层，并说明依赖边界。
参照 ctc-fe-vue3 评审这个组件的类型、异步副作用和样式隔离问题。
参照 ctc-fe-adapt-broswer 制定奇安信浏览器的生产构建兼容验收方案。
参照 ctc-fe-cicd-release 为新前端项目设计 Pipeline、部署环境选择和回滚方案。
```
