# 版本记录

## 1.2.2 — 2026-11-13

### 新增与完善

- 为 `gf-fullstack-dev` 的自动监控前端补充 3 个代码仓库：`zdjk-company-base`（企业端框架）、`gov-zdjk-ministry`（管理端 4.3 框架）、`gf-framework-system`（管理端 5.0 框架）；监测代码仓库由 8 个增至 11 个，总计 13 个 Git 仓库。
- 同步更新仓库清单、工作区准备命令与 README 概览。
- 新增本地同步脚本 `scripts/sync-skill.sh` 与 `npm run sync -- <skill-name>`，在修改 skill 后将源仓库内容同步到已安装的 Qoder、Codex、Claude 本地副本，避免只复制 `SKILL.md` 造成分叉。

### 升级说明

- 使用新的固定版本 tag 重新安装 `gf-fullstack-dev`，或对主分支安装执行 `npx skills update`。
- 本地开发时可通过同步脚本更新工具副本；本地同步不等于发布。

### 验证范围

- `npm test`：校验 8 个 skill 的元数据与本地 Markdown 链接。
- 3 个新增仓库地址均可访问；本地同步后源仓库与 Qoder、Codex 副本哈希一致。

## 1.2.1 — 2026-11-11

### 修正与完善

- 为 `gf-fullstack-dev` 补齐监测需求仓库 `gf-monitor-reqs` 与执法需求仓库 `gf-law-reqs` 的地址、职责和目录，当前共登记 8 个代码仓库与 2 个需求仓库。
- 明确需求仓库位于各自领域工作区根目录，与子业务系统或子应用平级；区分分组目录与独立 Git 仓库目录。
- 增加需求定位与实现关联流程：按仓库实际约定查阅文档、记录需求依据及版本、核对对应实现与验收结果，并说明差异和缺失依据。
- 同步工作区准备命令及执法覆盖范围：执法需求仓库已登记，子应用代码仓库映射仍待补齐。

### 升级说明

- 使用新的固定版本 tag 重新安装 `gf-fullstack-dev`，并按手册手动准备对应领域的需求仓库。
- 保留原有版本核对与验证规则，以及 `provider-common` 的运维前端归属；不涉及应用代码改造。

### 验证范围

- `npm test`：校验 8 个 skill 的元数据与本地 Markdown 链接。
- 核对 10 个仓库地址与克隆示例一致，监测与执法准备命令语法检查通过。
- Skills CLI：在临时项目试装并核对安装文件与源码一致。

## 1.2.0 — 2026-11-10

### 新增与完善

- 新增 GF 多业务系统全栈协作规范 `gf-fullstack-dev`：
  - 将“监测”和“执法”定义为 GF 下的两套体系；现有清单记录“监测”体系中已提供的 8 个前后端 Git 仓库，涉及 `operations`（运维）与 `auto-monitor`（自动监控），并可继续增补其他监测子系统。
  - 为监测与执法分别规划独立工作区 `gf-monitor-ai/` 与 `gf-law-ai/`，并为执法体系补充仓库映射模板，子应用清单待后续补齐。
  - 增加任务领域路由：按监测/执法工作区或用户指定范围选择代码上下文，并规范多仓准备、逐仓需求分支/版本核对及前端到后端的接口追踪。
  - 标明自动监控后端 `amdb` 仅覆盖部分企业端和管理端功能，并要求明确缺失仓库和未确认的代码归属。
- 新增微前端子应用鉴权与静默续租规范 `ctc-fe-subapp-auth`：
  - 适配 `gf-monitor`（`monitor-user-info`）与 `gf-law`（`law-user-info`）两大基座平台。
  - 标准化 401/402 并发拦截挂起、通知基座续租与自动重试队列机制。
  - 增加基座平台接入矩阵与改造备忘分册 `references/platforms.md`。
  - 增加踩坑避雷与防御性编程指南分册 `references/troubleshooting.md`（防白屏死锁、Axios 拦截器顺序、防二次解包守卫、Vue 2/3 生命周期陷阱）。
  - 提供 Vue 2（Options API + Vuex）与 Vue 3（Composition API + Pinia）双栈接入模板代码。
- 新增统一页面布局生成规范 `ctc-fe-design-page`：
  - 基于 T01～T07 统一布局契约（T01 标准通用表格/报表页、T02 左树右查表、T03 GIS HUD 大屏、T04 分段长卷与锚点、T05 全高双栏对比、T06 多卡片网格看板、T07 步骤向导）生成或调整 Vue 3 页面。
  - 将原筛选表与页签表合并收敛为 `T01_STANDARD_TABLE_PAGE`，提供一体化超集插槽（tabs, filters, summary, toolbar, columns, pagination, footer），消除业务选型冗余。
  - 汲取 `@ctc-front/components-ui-next` 中 `CtcReport` 的高度链与视口防溢出经验，提供 T01 标准 Vue 3 布局组件 `TablePageLayout.vue`，并明确 `CtcReport` 插槽映射与复用指引。
- 新增统一页面布局审查规范 `ctc-fe-code-auditor`：
  - 针对遵循 T01～T07 契约的 Vue 页面提供专项审查流程。
  - 重点核对工作区白卡视觉分层、父级高度链与滚动（`min-height: 0` / 表格视口铺满）、插槽规范以及 GIS 图层事件穿透与资源销毁。
  - 增加对复用 `CtcReport` 报表组件的 T01 页面审查规范（核对 `search-bar`、`container-top`、`tool-bar` 插槽映射与 `auto-height` 配置）。

### 验证范围

- `npm test`：校验 8 个 skill 的元数据与本地 Markdown 链接。
- 布局生成与审查 skill：7 个模板、Schema、8 组示例、引用和插槽契约校验通过；两者共享资料一致。
- Skills CLI：在临时项目中完整安装 8 个 skill，确认目录、分册、脚本与元数据随包安装。

## 1.1.0 — 2026-11-05

### 新增与完善

- 增加 CI/CD 发布 Skill 及 Pipeline、Runner、SSH、环境配置和回滚分册，明确现有实现与目标方案的能力边界。
- 强化结构 Skill：明确业务子域与变体归属、目录容量、文件体积及存量渐进治理，禁止拆分后的平铺和转移堆积。
- 提供无第三方依赖的只读结构扫描器，检查同级源码文件数量与源码行数，超限返回非零。
- 完善 Vue Skill 的组件职责、子组件与 composable 拆分条件、响应式输入、实例状态所有权和副作用生命周期。
- 增加 Vue 组件设计、组合函数、模板与交互、验证与验收四个分册，补齐加载与失败恢复、属性透传及公开行为验证。
- 统一 Vue 与结构 Skill 分工；目录和体积阈值由结构 Skill 维护，Vue Skill 引用约束并检查本次修改不得引入新的超限。
- 完善浏览器兼容性分册、Skill 元数据与本地文档校验，统一标准 `SKILL.md` 入口。
- 文档增加固定版本安装、规范协同安装、版本维护和 GitHub Release 发布流程。

### 升级说明

- 本次引入更明确的结构硬门禁。升级后按结构 Skill 检查本次涉及的模块，已有超限按业务子域渐进整理并报告遗留债务。
- 使用 Vue Skill 时同时获取结构 Skill 或项目明确的结构规范；分册与脚本必须随 `SKILL.md` 一同安装。
- 保留已发布的 `ctc-fe-adapt-broswer` 历史名称，安装命令继续兼容。
- 相比 v1.0.2，本仓库不再包含 `postgres-sync`。此前使用该 Skill 的项目升级前应确认其独立来源；本次安装仅分发四份前端 Skills。
- 本仓库按 GitHub tag 分发；固定安装源为 `https://github.com/IdenPin/ctc-fe-skills/tree/v1.1.0`。

### 验证范围

- 校验 Skill 名称、元数据、本地 Markdown 链接与变更格式。
- 通过临时源码目录检查结构扫描器的数量与行数边界、排除规则、退出码及只读行为。
- 使用已有 TypeScript 与 ESLint 依赖检查通用代码示例、错误兜底与 Vue 规则片段。
- 发布前验证本地 skills CLI 安装内容，发布后再次通过远端 tag 试装。

此前版本的内容以仓库已有 Git tags 为准。
