# CTC FE Skills

`ctcfront` 团队的前端开发规范 Skill 仓库，供团队成员和 AI 编码助手在架构设计、Vue 3 开发和浏览器兼容性评估时按需加载。

[![skills.sh](https://skills.sh/b/IdenPin/ctc-fe-skills)](https://skills.sh/IdenPin/ctc-fe-skills)

## 安装

安装全部 skills：

```bash
npx skills add IdenPin/ctc-fe-skills -y
```

按需安装：

```bash
npx skills add IdenPin/ctc-fe-skills --skill ctc-fe-structure -y
npx skills add IdenPin/ctc-fe-skills --skill ctc-fe-vue3 -y
npx skills add IdenPin/ctc-fe-skills --skill ctc-fe-adapt-broswer -y
```

> `ctc-fe-adapt-broswer` 是已发布的历史拼写。为避免破坏现有安装路径暂时保留，后续破坏性版本迁移为 `ctc-fe-adapt-browser`。

## Skills

### [ctc-fe-structure](./ctc-fe-structure/SKILL.md)

用于目录拓扑、业务模块边界、依赖方向和老项目渐进迁移。主要约定：

- 页面流程和易变业务规则就近放入 `features` 或 `views`。
- 无业务语义的 UI、hooks 和工具放入 `shared/ui|lib`。
- `UserSelector`、`DictTag` 等稳定跨模块业务能力放入 `shared/biz`。
- 网络请求、WebSocket 等传输基础设施放入 `services`。

分册：[目录结构](./ctc-fe-structure/references/structure.md)、[依赖边界](./ctc-fe-structure/references/boundaries.md)、[命名](./ctc-fe-structure/references/naming.md)、[迁移](./ctc-fe-structure/references/migration.md)、[治理](./ctc-fe-structure/references/governance.md)。

### [ctc-fe-vue3](./ctc-fe-vue3/SKILL.md)

用于 Vue 3 SFC、TypeScript 类型边界、Composition API、副作用、样式隔离、模块导入和 ESLint 配置。规范区分 MUST、SHOULD、MAY：可机械检查的要求交给工具，涉及上下文判断的要求进入 Code Review。

### [ctc-fe-adapt-broswer](./ctc-fe-adapt-broswer/SKILL.md)

用于 Vite/Vue 3 项目的生产构建兼容性诊断。该 skill 明确 Tailwind CSS 4 的现代浏览器基线；对老内核的 CSS 改写属于项目专项实验，必须经过 fixture、视觉回归、关键流程和真实设备验证。

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
```
