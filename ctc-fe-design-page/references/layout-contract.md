# 页面布局契约

版本：2.0.0。本契约随每个技能独立携带；两份技能发布时保持同版本规则，运行时只读取各自目录内的资料。

## 入口与职责

- [输入结构](page-spec.schema.json)：PageSpec 的字段类型、模板分支与必填条件。
- [输入示例](page-spec.examples.json)：八个通用布局的规范示例。
- [布局变量](../assets/layout-tokens.css)：颜色、外圈间距、内边距、栏宽的唯一取值来源。
- [HTML 预览](../assets/layout-spec.html)：展示区域位置与机器可读插槽标记。
- [技能入口](../SKILL.md)：当前技能的执行流程。

优先级为用户明确要求、目标项目的已确认约定、本契约。遇到差异说明采用的约定，不擅自升级依赖或重做项目结构。完整复制当前技能目录即可携带入口和全部配套资料；不使用目录外引用或另一技能的文件。

## 模板与插槽

下表是插槽名称的唯一清单。名称不含 `#`；文档中 `#main-viewport` 等是可视标注，组件库声明对应的 Vue 命名插槽，业务仅装配插槽内容。

| templateId | 必需插槽 | 可选插槽 |
| --- | --- | --- |
| L01_STANDARD_TABLE_PAGE | main-viewport | filter-bar, toolbar, footer-bar |
| L02_SIDEBAR_TREE_SPLIT | sidebar-nav, content-body | content-header, content-footer |
| L03_MASTER_DETAIL_SPLIT | master-list, detail-body | master-filter, detail-head, detail-actions |
| L04_GIS_HUD_DASHBOARD | canvas-bg | hud-top, hud-left, hud-right, hud-bottom-left, hud-bottom-right |
| L05_DUAL_PANE_REVIEW | pane-left, pane-right | 无 |
| L06_GRID_DASHBOARD | dashboard-grid | metric-cards, dashboard-toolbar |
| L07_SECTION_ANCHOR_FLOW | anchor-nav, sections-stream | profile-header, sticky-actions |
| L08_STEP_WIZARD_FUNNEL | step-tracker, stage-viewport, action-rail | step-summary |

## 组件登记表 (Canonical Layout Component Registry)

所有模板的组件名、属性默认值、插槽定义与滚动归属以本登记表为唯一机器真源：

| templateId | 对应组件名 | 属性与默认值 | 必需插槽 | 可选插槽 | 滚动责任归属 | 宿主约束 |
|---|---|---|---|---|---|---|
| `L01_STANDARD_TABLE_PAGE` | `CtcTablePageLayout` | `autoHeight: true`, `toolbarPlacement: 'separate'`, `card: true` | `main-viewport` | `filter-bar`, `toolbar`, `footer-bar` | 子组件滚动 (`CtcTable auto-height`) | 嵌入宿主使用 `height: 100%`，严禁 `100vh` |
| `L02_SIDEBAR_TREE_SPLIT` | `CtcSidebarTreeLayout` | `sidebarWidth: '260px'`, `collapsible: true` | `sidebar-nav`, `content-body` | `content-header`, `content-footer` | 分轨双滚 (内建滚动容器托管) | 右侧复杂检索优先直接使用自带插槽，禁止嵌套 L01 |
| `L03_MASTER_DETAIL_SPLIT` | `CtcMasterDetailLayout` | `masterWidth: '340px'` | `master-list`, `detail-body` | `master-filter`, `detail-head`, `detail-actions` | 分轨双滚 (主列表滚动 + 详情滚动) | 页面级主从协同，非弹层场景 |
| `L04_GIS_HUD_DASHBOARD` | `CtcGisHudLayout` | `theme: 'light'` | `canvas-bg` | `hud-top`, `hud-left`, `hud-right`, `hud-bottom-left`, `hud-bottom-right` | 底图禁滚，HUD 浮层内部按需滚动 | HUD 容器 `pointer-events: none` 穿透底图 |
| `L05_DUAL_PANE_REVIEW` | `CtcDualPaneReview` | `leftWidth: '45%'`, `gap: '16px'` | `pane-left`, `pane-right` | 无 | 分轨双滚 (左栏证据 + 右栏审批) | 必须内嵌于 `CtcDialog`/`CtcDrawer` 并声明 `content-fill` |
| `L06_GRID_DASHBOARD` | `CtcDashboardGridLayout` | `gap: '16px'`, `scrollable: true` | `dashboard-grid` | `metric-cards`, `dashboard-toolbar` | 视口自适应或网格整体滚动 | 主体网格为 12 栅格；`:cards="pageSpec.grid.cards"` 托管 span/height，`dashboard-grid` 接收 `{ card, index }` |
| `L07_SECTION_ANCHOR_FLOW` | `CtcAnchorScrollLayout` | `anchorWidth: '180px'` | `anchor-nav`, `sections-stream` | `profile-header`, `sticky-actions` | 单根唯一滚动 (`scrollRootRef`) | 严禁子卡片局部二次滚动；`anchor-nav` 接收 `scrollContainer` |
| `L08_STEP_WIZARD_FUNNEL` | `CtcStepWizardLayout` | `activeStep: 0`（插槽作用域） | `step-tracker`, `stage-viewport`, `action-rail` | `step-summary` | 单视口受控滚动 (`stage-viewport`) | 步骤列表 `steps` 至少 2 步，底部操作条常驻 |

- **L01**：标准检索与表格报表工作台。`main-viewport` 为核心内容插槽（放入项目现有的 `<CtcTable>` 或表格组件，由表格负责内部滚动）；可选插槽提供筛选栏、操作工具栏、底部常驻分页栏。默认启用 `card: true` 卡片式承载（浅灰底背景衬托白色卡片与细边框，并将 `footer-bar` 置于卡片内部底部）；支持 `toolbarPlacement: 'filter-inline'` 将工具栏并入筛选行。
- **L02**：侧栏树/导航联动布局。左侧 `sidebar-nav`（默认宽 `260px`）与右侧内容区双轨独立纵向滚动，右侧主体包含可选头部工具条、必选内容体与可选底栏。
- **L03**：主从协同卡片/详情布局。左侧 `master-list`（默认宽 `340px`）卡片列表与右侧 `detail-body` 详情/表单双轨分栏独立滚动，右侧包含可选头部与底部操作吸底条。
- **L04**：GIS 地图全景工作台。`canvas-bg` 地图底图铺满，HUD 覆盖层包装容器 `pointer-events: none` 穿透底层事件，各功能浮层面板恢复 `pointer-events: auto` 并可折叠。
- **L05**：复合双栏核查工作台。**纯双栏内容布局**，专用于两段式案卷核查与证据审阅。必需包含 `pane-left`（左栏证据/详情，独立滚动）与 `pane-right`（右栏审批/填报，独立滚动）。外壳直接由业务项目标准浮层 `<CtcDialog>` 或 `<CtcDrawer>` 提供，48px Header 与 Footer 由外壳原生管控。单栏业务直接由外壳承载，不走 L05。
- **L06**：响应式网格看板。`dashboard-grid` 承载弹性 CSS 网格；可选 `metric-cards` 提供 KPI 统计条；子卡片必须自行挂载 `ResizeObserver` 响应尺寸。
- **L07**：锚点长卷档案表单。统一全局单滚动根节点；`anchor-nav` 侧边浮动菜单 Sticky 跟随视口联动高亮；`sections-stream` 为纵向长卷内容；`sticky-actions` 常驻底部操作栏。
- **L08**：步骤向导漏斗。`step-tracker` 顶部引导指示；`stage-viewport` 中间当前步骤受控工作台（单视口内部自负责滚动）；`action-rail` 底部导航动作条；可选 `step-summary` 承载阶段说明摘要。

HTML 预览会标出全部可选插槽以说明位置。实际输出只启用必需插槽，以及用户明确要求或业务配置实际使用的可选插槽。没有内容的可选区域不保留空白包装、边框或高度。

## 空间约束与高度传导规则

1. **容器高度驱动**：在嵌入宿主基座、微前端或带页签的页面布局中，**严禁全局 `100vh` 锁死**。布局根节点使用 `height: 100%` 填满父容器。
2. **完整收缩链**：所有 Flex 纵向或横向嵌套层，必须保持完整的 `min-height: 0; min-width: 0; flex: 1;` 收缩链，防止工具栏和分页栏被意外挤出视口。
3. **独立全屏与浮层例外**：独立全屏大屏页面（如 L04 全屏态）或顶层 Teleport 浮层外壳（`<CtcDialog>` / `<CtcDrawer>`）可按自身需求采用视口尺寸策略。

## 滚动责任人唯一矩阵

| 布局模版 | 滚动类型 | 滚动责任人归属 | 说明 |
|---|---|---|---|
| L01 检索工作台 | 子组件滚动 | `main-viewport` 内子表格/虚拟列表 | 布局只限定高，表格自身溢出滚动 |
| L02 侧栏联动 | 分轨双滚 | `sidebar-nav` 与 `content-body` 各自独立 | 左右各自滚动，互不干扰 |
| L03 主从协同 | 分轨双滚 | `master-list` 与 `detail-body` 各自独立 | 左栏卡片滚动，右栏详情滚动 |
| L04 地图 HUD | 视口禁滚 | 仅各浮层面板内部按需滚动 | 地图画布禁止滚动，保留拖拽缩放 |
| L05 双栏核查 | 分轨双滚 | `pane-left` 与 `pane-right` 各自独立 | 外壳 overflow:hidden 禁滚，内部两栏独立滚动 |
| L06 网格看板 | 视口自适应 | `dashboard-grid` 容器滚动或视口定高 | 内部图表通过 ResizeObserver 适配 |
| L07 长卷档案 | 全局单根滚动 | `sections-stream` 所在的长卷根容器 | 唯一点单根滚动，严禁子卡片嵌套滚动 |
| L08 步骤向导 | 视口定高锁定 | 仅 `stage-viewport` 当前步骤视口滚动 | 步骤条与底部操作栏常驻不滚 |

## 两种输出模式

### layout：仅布局

用户说“只要布局、骨架、线框”时采用此模式。PageSpec 最小输入为 `mode: layout` 和 `templateId`。
输出区域骨架和必要的插槽标识；不填业务字段、示例数据、真实控件、图表系列或地图地理内容。`enabledSlots` 用于选择额外区域。

### page：业务页面

从自然语言、现有页面和用户提供的配置归一化为 PageSpec。page 模式还必须提供 `pageTitle`。
下表列出各模板的 PageSpec 字段。`surface` 声明当前承载区域，主页面与各浮层独立选型；同模板多实例用 `layoutKey` 对应 `data-layout-id`。`enabledSlots` 选择可选区域，必需插槽始终启用；兼容在列表中同时列出必需插槽。未显式设置的属性使用组件默认值。

| templateId | 必需 PageSpec 字段 | 可选 PageSpec 字段 |
| --- | --- | --- |
| L01_STANDARD_TABLE_PAGE | pageTitle, viewport | filters, toolbar, footer, pagination, layoutProps |
| L02_SIDEBAR_TREE_SPLIT | pageTitle, sidebar, content | toolbar, pagination, layoutProps |
| L03_MASTER_DETAIL_SPLIT | pageTitle, master, detail | masterFilter, detailActions, layoutProps |
| L04_GIS_HUD_DASHBOARD | pageTitle, map | panels, legend, mapTools, layoutProps |
| L05_DUAL_PANE_REVIEW | pageTitle, leftPane, rightPane, surface | actions, layoutProps |
| L06_GRID_DASHBOARD | pageTitle, grid | metrics, toolbar, layoutProps |
| L07_SECTION_ANCHOR_FLOW | pageTitle, sections | profileHeader, stickyActions, layoutProps |
| L08_STEP_WIZARD_FUNNEL | pageTitle, steps | stepSummary, actionRail, layoutProps |

## 组件与消费原则

1. **唯一生产真源**：全部布局组件由 `@ctc-front/components-ui-next/layout` 导出；
2. **标准业务引用**：业务页面以 `import { CtcTablePageLayout, CtcDualPaneReview, ... } from '@ctc-front/components-ui-next/layout'` 方式消费；
3. **受控校验**：交付时使用 `validate-page.py <Page.vue> --spec <page-spec.json>`，每个浮层再追加一份 `--spec`；通过 JSON 导入绑定配置，原生 ElDialog/ElDrawer 不能替代 CTC 的 content-fill 外壳。
4. **插槽填充**：业务只在对应插槽中填入实际业务控件（表单、表格、图表），严禁重写外层 flex/grid 容器样式。
