---
name: ctc-fe-design-page
description: 根据 L01～L08 布局契约创建或调整 Vue 3 页面。支持纯布局骨架和业务页面装配；在用户需要通用表格报表、侧栏树联动、主从协同、GIS 地图全景、复合双栏核查、网格看板、长卷表单或步骤向导时使用。
---

# 生成或调整页面布局

先读取[统一布局契约](references/layout-contract.md)与[布局变量](assets/layout-tokens.css)。进入 page 模式后，按所选模板读取[输入 Schema](references/page-spec.schema.json)的相关分支。需要示意时查看[HTML 预览](assets/layout-spec.html)；需要配置参考时读取[输入示例](references/page-spec.examples.json)。纯布局任务无需加载完整业务配置。

## 1. 需求选型与裁决规则 (Taxonomy & Boundary Rules)

当需求描述可能重叠或边界模糊时，**必须按以下 6 条仲裁规则**严格判定，杜绝同一需求生成不同布局：

1. **宿主基座 vs 本页面边界**：
   - 若左侧导航/菜单已由微前端基座或系统框架提供，当前页面仅负责右侧数据检索与展示，**一律选 L01**；
   - 仅当左侧组织树、行政区划树或分类目录是**本业务模块内部私有状态**且需要与右侧深度联动时，才选 **L02**。
2. **严禁在 L02 右侧嵌套 L01**：
   - 当 L02 右侧需要完整的“筛选 + 表格 + 分页”工作台时，**必须直接使用 L02 原生插槽**：`#content-header` 承载筛选与工具条、`#content-body` 承载表格、`#content-footer` 承载分页；**严禁将 `CtcTablePageLayout` 嵌套塞入 L02**。
3. **弹窗/抽屉 vs 页面级双栏**：
   - 凡是在浮层（`CtcDialog` 或 `CtcDrawer`）内部执行两段式案卷核查、公文审阅与审批流转，**一律选 L05**，且外壳必须声明 `content-fill`；
   - 路由级独立完整页面、左侧为可无限滚动的主对象卡片列表、右侧为详情表单的主从协同，选 **L03**；
   - 弹窗内单栏业务直接由弹窗自身承载，严禁使用 L05。
4. **带 KPI 的表格 vs 网格看板**：
   - 若主体依然是数据检索表格，仅在表格上方陈列 2~4 个摘要指标条，**选 L01**（指标条放入 `#toolbar` 或作为表格顶部扩展）；
   - 仅当页面以多图表组合呈现、多卡片弹性流动、支持 12 栅格自适应布局时，才选 **L06**。
5. **长卷档案 vs 步骤向导**：
   - 允许用户自由上下滚动、跳跃查阅、随时通过侧边目录定位且单次保存的表单档案，选 **L07**；
   - 严格按业务阶段漏斗推进、各步骤存在数据先后依赖、需要上一步/下一步严格校验的，选 **L08**。
6. **按承载区域裁决**：主页面与每个 Dialog/Drawer 分别选型并保存独立 Spec。一个台账页打开双栏审核弹窗时，主页面可选 L01，弹窗选 L05；浮层优先级不能替代主页面。以下队列仅在同一承载区域内使用：
   `L05 (浮层双栏)` > `L04 (GIS全景)` > `L08 (步骤向导)` > `L02 (内含侧栏树)` > `L03 (页面主从)` > `L07 (长卷档案)` > `L06 (网格看板)` > `L01 (标准检索)`

---

## 2. 标准化 6 步受控装配工作流

页面生成必须严格执行以下流水线，禁止直接凭经验手写未经校验的代码：

```
Step 1: 需求提取与选型裁决 ➔ Step 2: 生成并冻结 PageSpec ➔ Step 3: PageSpec Schema 校验
    ➔ Step 4: 装配布局骨架 ➔ Step 5: 填充业务插槽 ➔ Step 6: validate-page 验证交付
```

- **Step 1: 需求提取与选型裁决**：按照上述 6 条裁决规则提取用户需求，锁定唯一的 `templateId` 与所需插槽集合；
- **Step 2: 生成并冻结 PageSpec**：参照 [Schema](references/page-spec.schema.json) 与 [示例](references/page-spec.examples.json) 生成规范的 PageSpec JSON 对象，明确 `mode`、`pageTitle`、`enabledSlots`、`surface`（embedded/standalone/dialog/drawer）及必要业务配置；多个同类实例设置 `layoutKey`，并在对应布局组件上添加相同的 `data-layout-id`。L05 必须声明 dialog 或 drawer；
- **Step 3: PageSpec Schema 校验**：验证 PageSpec 满足字段契约、无非法字段、卡片 span 在 1~12 之间、steps 至少 2 项；
- **Step 4: 装配布局骨架**：从 `@ctc-front/components-ui-next/layout` 引入对应的标准布局组件，严禁捏造虚假组件或私自手写布局外层容器；
- **Step 5: 填充业务插槽**：使用 `<template #slot-name>` 填充真实业务组件（`<CtcTable>`、表单、图表），业务只管理内部控件与数据，不得篡改布局容器样式；
- **Step 6: validate-page 验证交付**：使用 `python3 scripts/validate-page.py <Page.vue> --spec <page-spec.json>` 校验交付。页面含浮层时重复传入 `--spec <review-spec.json>`，每个布局实例必须唯一匹配一份 Spec。校验依赖 `jsonschema`，缺少时明确失败；静态通过后仍需验证宿主高度链和浏览器滚动。

---

## 3. 插槽装配与代码规范

- **生产级组件导入**：页面统一从 `@ctc-front/components-ui-next/layout` 引入标准布局骨架：
  ```ts
  import {
    CtcTablePageLayout,
    CtcSidebarTreeLayout,
    CtcMasterDetailLayout,
    CtcGisHudLayout,
    CtcDualPaneReview,
    CtcDashboardGridLayout,
    CtcAnchorScrollLayout,
    CtcStepWizardLayout,
  } from '@ctc-front/components-ui-next/layout'
  ```
- **插槽作用域与单根性**：
  - L07 必须使用 `#anchor-nav="{ scrollContainer }"` 将布局内部唯一的滚动容器实例传递给 `<el-anchor :container="scrollContainer">`；
  - L05 必须置于 `<CtcDialog content-fill>` 或 `<CtcDrawer content-fill>` 内部，外壳自动赋予 `overflow: hidden; padding: 0;`。
- **受控配置绑定**：在 Vue 文件中通过相对路径导入冻结 JSON，如 `import pageSpec from './page-spec.json'`，用 `v-bind="pageSpec.layoutProps"` 或字面量绑定结构属性。未在 Spec 中声明的属性只能使用组件登记的默认值，禁止通过根节点 style/class 或组件内部选择器改变结构。动态业务步骤状态允许传给 `activeStep`，各插槽通过 `{ activeStep }` 读取；表单校验与流转由业务处理。
- **L06 受控网格**：使用 `:cards="pageSpec.grid.cards"`；`#dashboard-grid="{ card, index }"` 只渲染该卡片的业务内容，span 与 height 由组件设置，禁止手写卡片外层栅格。
- **未启用插槽不占位**：未传入内容的可选插槽不保留多余空白包装、边框或高度。
- **类型安全**：页面必须使用 Vue 3 `<script setup lang="ts">`，严禁使用 `any` 掩盖未知数据。

---

## 4. 边界核查与交付清单 (Pre-flight Checklist)

1. **容器高度链自查**：嵌入宿主基座或页签的页面，**严禁全局 `100vh` 锁死**，统一使用 `height: 100%`，确保所有中间层 Flex 节点具备 `min-height: 0; min-width: 0; flex: 1;` 收缩链；
2. **滚动责任人检查**：确认单滚动根节点归属，杜绝同方向内外嵌套双滚动条；
3. **浮层禁滚检查**：浮层内挂载双栏核查时，外壳 `CtcDialog` 或 `CtcDrawer` 必须开启 `content-fill`，确保外层容器 `overflow: hidden; padding: 0;`；
4. **副作用清理**：GIS 地图和 ECharts 图表必须在 `onUnmounted` 中正确调用 `destroy` 或 `dispose` 释放实例，断开 `ResizeObserver`。

---

## 维护资料

JSON 导入的枚举字段在 TypeScript 中可能被推断为 string。先完成 Schema 校验，再使用公开类型断言，例如 `v-bind="pageSpec.layoutProps as CtcTablePageLayoutProps"`；校验器支持此写法，禁止使用 any。

在当前技能目录执行 `python3 scripts/check-package.py` 自动化检查契约、Schema、HTML 机器标签与示例一致性。
修改公共资料后，执行 `python3 scripts/sync-shared-resources.py --target ../ctc-fe-code-auditor --apply` 比较或同步到审查技能。
