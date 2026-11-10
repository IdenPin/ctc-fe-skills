# 页面布局契约

版本：1.0.0。本契约随每个技能独立携带；两份技能发布时保持同版本规则，运行时只读取各自目录内的资料。

## 入口与职责

- [输入结构](page-spec.schema.json)：PageSpec 的字段类型、模板分支与必填条件。
- [输入示例](page-spec.examples.json)：一个纯布局示例和四个业务页面示例。
- [布局变量](../assets/layout-tokens.css)：颜色、外圈间距、内边距、栏宽的唯一取值来源。
- [HTML 预览](../assets/layout-spec.html)：展示区域位置和插槽；不提供可直接导入的 Vue 布局组件。
- [技能入口](../SKILL.md)：当前技能的执行流程。

优先级为用户明确要求、目标项目的已确认约定、本契约。遇到差异说明采用的约定，不擅自升级依赖或重做项目结构。完整复制当前技能目录即可携带入口和全部配套资料；不使用目录外引用、符号链接或另一技能的文件。技能的自动发现由目标运行器配置，资料校验脚本不注册工具命令或提交钩子。

## 模板与插槽

下表是插槽名称的唯一清单。名称不含 `#`；文档中 `#search-bar` 等是可视标注，实际组件需要自行声明对应的 Vue 命名插槽。
各模板涉及的核心数据表格统一由 `@ctc-front/components-ui-next` 的标准表格组件（`<CtcReport>` / `<CtcTable>`）承载，列定义由组件属性 `:columns="columns"`（Props）驱动，单元格定制采用动态列插槽 `#[column.slot]`，不再设立虚拟的 `#columns` 容器插槽。

| templateId | 必需插槽 | 可选插槽 |
| --- | --- | --- |
| T01_STANDARD_TABLE_PAGE | 无 | search-bar, tool-bar, container-top, table-bar, default, append-table, pagination |
| T02_SIDEBAR_QUERY_TABLE | sidebar-tree, toolbar | pagination |
| T03_GIS_HUD_DASHBOARD | map-canvas | left-kpi, left-chart, right-kpi, right-alarm, site-list, legend, map-tools |
| T04_SECTION_ANCHOR_FLOW | sections | header-summary, anchor-nav, actions-footer |
| T05_SPLIT_TWO_PANE | master-list, slave-body | master-header, slave-toolbar, slave-footer |
| T06_GRID_DASHBOARD | charts-grid | dashboard-toolbar, metric-cards, ranking-board |
| T07_STEP_WIZARD_FUNNEL | step-tracker, stage-viewport, action-rail | step-summary |

- T01：标准通用表格/报表工作区。插槽体系 100% 对应 `@ctc-front/components-ui-next` 中 `<CtcReport>` 原生规范：核心表格由内置 `<CtcTable>` 驱动（通过 `:columns` 属性与动态列插槽渲染），外层提供搜索筛选（`search-bar`）、操作工具（`tool-bar`）、指标统计/分类Tabs（`container-top`）、表格栏（`table-bar`）、前置自定义默认插槽（`default`）、表格后置追加/底栏（`append-table`）与受控分页（`pagination`）。参考实现见[TablePageLayout.vue](../templates/TablePageLayout.vue)。
- T02：左侧导航独立，右侧顶部查询工具条（`toolbar`），下方白卡内嵌 `<CtcTable>`（通过 `:columns` 与 `:data` 属性驱动，可选 `pagination` 扩展）。
- T03：地图画布铺满布局容器，浮层按插槽叠加，中央保留地图视野。深浅主题由项目或显式输入确定；预览中的深色仅为示例。
- T04：顶部概览区，主体为纵向多卡片长卷，侧边/顶部浮动锚点轨联动视口高亮，底部常驻吸底操作栏。
- T05：全高垂直双栏（左右 100% 视口定高），左栏主清单、右栏从属详情/编辑，各自拥有独立纵向滚动条。
- T06：无全景底图的纯二维响应式多卡片网格系统，多行多列白卡拼装自适应视口，内部图表随容器响应式缩放。
- T07：步骤轨迹驱动单视口受控切换，顶部引导阶段指示，中间独立工作台聚焦当前步骤，底部导航动作轨道。

HTML 预览会标出全部可选插槽以说明位置。实际输出只启用必需插槽，以及用户明确要求、`enabledSlots` 指定或业务配置实际使用的可选插槽。没有内容的可选区域不保留空白包装、边框或高度。若配置显式 `enabled: false`，不能同时在 `enabledSlots` 启用该区域；遇到这种冲突应先修正配置。

## 两种输出模式

### layout：仅布局

用户说“只要布局、骨架、线框”时采用此模式。未明确需要业务页面时先采用 layout。PageSpec 最小输入为 `mode: layout` 和 `templateId`。

输出区域骨架和必要的插槽标识；不填业务字段、示例数据、真实控件、图表系列或地图地理内容。`enabledSlots` 用于选择额外区域。图例和工具仅用空白区域表示。不要为了凑齐输入而向用户索要实体名、API 或业务 Schema。

### page：业务页面

从自然语言、现有页面和用户提供的配置归一化为 PageSpec，不要求用户手填 JSON。按输入 Schema 校验所属模板的配置；只追问无法从项目和上下文推断、且会影响正确实现的业务决定。

旧版 T01～T03 输入若使用 `schema` 字段数组，先迁移为 `columns`，由已有 `prop` 补齐缺失的 `key`，再移除旧字段并校验。其它模板配置从实际需求和项目补齐，不由列数组推测页签、树或地图。校验器接受的是归一化后的新格式。

- T01：需要 `filters`、`columns`；按需提供 `summary`、`actions`、`pagination`。
- T02：需要 `tabs`、`toolbar`、`columns`；按需提供 `actions`、`pagination`、`footer`。
- T03：需要 `sidebar`、`toolbar`、`columns`；按需提供 `pagination`。
- T04：需要 `map`；按需提供 `panels`、`legend`、`mapTools`。不强制声明实体表格或分页。
- T05：需要 `sections`；按需提供 `headerSummary`、`anchorNav`、`actionsFooter`。
- T06：需要 `master`、`slave`；按需提供 `masterHeader`、`slaveToolbar`、`slaveFooter`。
- T07：需要 `widgets`；按需提供 `dashboardToolbar`、`metricCards`、`rankingBoard`。
- T08：需要 `steps`；按需提供 `stepSummary`。

表格列的 `key` 在同一表内唯一；`prop` 缺省等于 `key`，操作列使用 `actions`。查询字段、页签、摘要和动作的 `key` 在各自集合内唯一。`defaultKey` 必须属于页签集合，`pageSize` 应属于配置的 `pageSizes`。这些跨字段约束由生成/审查流程检查。

配置中的 `dataSourceRef`、`adapterRef` 指向项目现有数据服务或组件，必须核实存在。缺少服务时使用类型明确的 props/emits 作为接入面，并说明接入点；不编造 URL、SDK 密钥、导入路径或看似真实的请求成功结果。

## 视觉与尺寸

读取本技能 `assets/layout-tokens.css`，业务页面引用或映射其中的变量，不从缩略图像素反推页面尺寸。

T01～T03 的层次固定为：工具栏白色；下方工作区使用 `--layout-workspace-bg`；白色内容卡片与工作区四边均留 `--layout-frame-gap`；表格、摘要和分页位于白色卡片内。T02 底部动作也位于同一白卡内。外圈上边距不能省略。T03 的左侧导航独立于右侧工作区。

卡片内边距、控件间距、侧栏宽度分别使用对应变量。业务布局间距遵守 4px 栅格；1px 边框、字体字号、数据列宽、图表自身坐标不受此规则限制。HTML 的缩略图高度、说明栏宽度、插槽注释是文档尺寸，不复制到业务页面。

显式主题需求可以覆盖颜色；常规报表仍采用工作区浅灰蓝、内容卡片和表格白色的分层。不要因为选择 GIS 布局就自动切换整个项目的主题。

## 容器高度与滚动

- 先确认路由外壳到页面根节点具有可计算的可用高度。只有父级高度已确定时，`h-full` 才能填满它；独立全屏页可使用项目已有视口方案。
- 纵向区域使用可收缩的 flex 布局；需要收缩的中间节点有 `min-height: 0`，横向表格区有 `min-width: 0`。工具栏和底栏不被挤压。
- 表格视口占据剩余高度，数据在表格内部滚动。普通 `el-table` 在父级高度确定时可用 `height="100%"`，也可用项目已有的容器测量方案；不要仅凭属性写法判定布局正确。
- 表格视口高度不等于虚拟滚动。只有确有数据量或性能需求时才使用 `el-table-v2` 等虚拟表格，并按该组件 API 传入测量后的尺寸。
- 分页和配置底栏固定在所属内容卡片的布局底部，不使用浏览器级 `position: fixed` 覆盖其他区域。
- 左树、列表等独立长内容按需滚动；禁止的是意外的页面双滚动和内容被裁掉，不是所有滚动容器。

## 按需求启用的行为

- 查询、重置：若配置了这些动作，更新条件与查询结果；分页查询时回到第一页。使用项目现有数据流，不规定函数必须叫 `fetchData`。
- 分页：页码与页容量受控，页容量变化时回到第一页；请求去重或重载方式遵循项目约定。
- 页签/树选择：只有业务要求联动时才重查。若不保留跨上下文选择，切换时立即清空选择；异步响应需防止旧结果覆盖新上下文。防抖按输入/请求频率决定，不延迟清空选择。
- loading、空态、错误态：适用于真实数据区域；layout 模式不伪装数据请求。无表格的 T04 不必实现表格分支。
- 破坏性操作：沿用项目确认机制，并防重复提交；普通筛选重置不属于破坏性操作。
- 地图/图表：用目标库实际支持的 API 释放本页面拥有的实例，解绑监听器、断开 observer、取消计时器和在途请求；不销毁父级传入且不属于本页的实例。

## GIS 图层

地图层位于底部；覆盖层包装可以 `pointer-events: none`，但每个需要交互的面板必须恢复 `pointer-events: auto`。装饰标签不接收事件。未被面板遮挡的地图区域继续响应拖动、缩放。浮层不得无意覆盖图例、地图工具和主要中心视野。

## 检查与输出

修改本技能资料后，以技能目录为当前目录运行 `python3 scripts/check-package.py`，检查引用、模板 ID、插槽清单和示例结构；安装了 `jsonschema` 时进一步校验输入示例。单独校验配置可使用 `python3 scripts/check-package.py --spec path/to/page-spec.json`，需要工具环境具备 `jsonschema`。该脚本不扫描业务代码，也不是已安装的提交门禁。

生成业务页面后使用项目现有的类型检查、lint 和适用测试，并在可运行时查看目标 PC 尺寸、空数据和长内容。没有可运行项目时准确记录未验证项。审查默认只给有证据的问题；仅在用户请求修复时修改代码。
