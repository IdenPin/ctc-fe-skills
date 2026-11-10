<script setup lang="ts">
/**
 * T01_STANDARD_TABLE_PAGE 通用标准表格/报表页布局组件 (TablePageLayout)
 * 100% 镜像对齐 @ctc-front/components-ui-next 中 CtcReport 的真实 Slot 规范与高度链设计。
 *
 * 插槽体系（与 CtcReport 保持绝对一致）：
 * - custom-tool-bar: 全自定义置顶头部插槽
 * - tool-bar / tool-bar-left / tool-bar-right: 操作工具栏（支持左右弹性分流）
 * - search-bar / search-bar-left / search-bar-right: 条件搜索筛选栏（支持左右分流）
 * - container-top: 容器顶部区域（指标统计、KPI 卡片、分类页签 tabs）
 * - table-bar / table-title / table-info-left / table-info-right: 表格标题与小统计栏
 * - default: 默认自定义插槽（位于表格上方的前置自定义区域）
 * - append-table: 表格后置追加区域（批量勾选操作、底栏）
 * - pagination: 底部常驻受控分页栏
 * - 核心表格由 CtcTable 承载，列定义由 :columns 属性驱动，无 columns 容器插槽
 */
defineOptions({
  name: 'TablePageLayout',
})

defineSlots<{
  'custom-tool-bar'?: () => any
  'tool-bar'?: () => any
  'tool-bar-left'?: () => any
  'tool-bar-right'?: () => any
  'search-bar'?: () => any
  'search-bar-left'?: () => any
  'search-bar-right'?: () => any
  'container-top'?: () => any
  'table-bar'?: () => any
  'table-title'?: () => any
  'table-info-left'?: () => any
  'table-info-right'?: () => any
  default?: () => any
  'append-table'?: () => any
  pagination?: () => any
  [key: string]: any
}>()
</script>

<template>
  <div class="ctc-table-page-layout">
    <!-- 头部区域：支持 custom-tool-bar，或 tool-bar 与 search-bar -->
    <header
      v-if="
        $slots['custom-tool-bar'] ||
          $slots['tool-bar'] ||
          $slots['tool-bar-left'] ||
          $slots['tool-bar-right'] ||
          $slots['search-bar'] ||
          $slots['search-bar-left'] ||
          $slots['search-bar-right']
      "
      class="ctc-table-page-layout__header"
    >
      <slot v-if="$slots['custom-tool-bar']" name="custom-tool-bar" />
      <template v-else>
        <!-- 操作工具栏（支持 default / left / right） -->
        <div
          v-if="$slots['tool-bar'] || $slots['tool-bar-left'] || $slots['tool-bar-right']"
          class="ctc-table-page-layout__toolbar-bar"
        >
          <slot v-if="$slots['tool-bar']" name="tool-bar" />
          <template v-else>
            <div v-if="$slots['tool-bar-left']" class="ctc-table-page-layout__bar-left">
              <slot name="tool-bar-left" />
            </div>
            <div v-if="$slots['tool-bar-right']" class="ctc-table-page-layout__bar-right">
              <slot name="tool-bar-right" />
            </div>
          </template>
        </div>

        <!-- 筛选检索栏（支持 default / left / right） -->
        <div
          v-if="$slots['search-bar'] || $slots['search-bar-left'] || $slots['search-bar-right']"
          class="ctc-table-page-layout__search-bar"
        >
          <slot v-if="$slots['search-bar']" name="search-bar" />
          <template v-else>
            <div v-if="$slots['search-bar-left']" class="ctc-table-page-layout__bar-left">
              <slot name="search-bar-left" />
            </div>
            <div v-if="$slots['search-bar-right']" class="ctc-table-page-layout__bar-right">
              <slot name="search-bar-right" />
            </div>
          </template>
        </div>
      </template>
    </header>

    <!-- 主容器 -->
    <div class="ctc-table-page-layout__container">
      <!-- 容器顶部：KPI 指标统计、汇总或分类 Tabs -->
      <section v-if="$slots['container-top']" class="ctc-table-page-layout__container-top">
        <slot name="container-top" />
      </section>

      <!-- 主工作区内容白卡（自适应撑满剩余视口，内部滚动） -->
      <main class="ctc-table-page-layout__body">
        <!-- 表格标题/小统计栏 -->
        <div
          v-if="
            $slots['table-bar'] ||
              $slots['table-title'] ||
              $slots['table-info-left'] ||
              $slots['table-info-right']
          "
          class="ctc-table-page-layout__table-bar"
        >
          <slot v-if="$slots['table-bar']" name="table-bar" />
          <template v-else>
            <div v-if="$slots['table-title']" class="ctc-table-page-layout__table-title">
              <slot name="table-title" />
            </div>
            <div
              v-if="$slots['table-info-left'] || $slots['table-info-right']"
              class="ctc-table-page-layout__table-info"
            >
              <div v-if="$slots['table-info-left']" class="ctc-table-page-layout__bar-left">
                <slot name="table-info-left" />
              </div>
              <div v-if="$slots['table-info-right']" class="ctc-table-page-layout__bar-right">
                <slot name="table-info-right" />
              </div>
            </div>
          </template>
        </div>

        <!-- 默认插槽：表格前置自定义内容（如警告、提示、自定义小组件） -->
        <div v-if="$slots.default" class="ctc-table-page-layout__before">
          <slot />
        </div>

        <!-- 表格视口承载容器（核心高度链：内置 CtcTable，通过 :columns 属性与动态单元格插槽渲染） -->
        <div class="ctc-table-page-layout__table-container">
          <slot />
        </div>

        <!-- 表格后置追加区域（批量勾选底栏、操作栏） -->
        <footer v-if="$slots['append-table']" class="ctc-table-page-layout__after">
          <slot name="append-table" />
        </footer>

        <!-- 可选：底部分页控制栏 -->
        <footer v-if="$slots.pagination" class="ctc-table-page-layout__pagination">
          <slot name="pagination" />
        </footer>
      </main>
    </div>
  </div>
</template>

<style scoped>
.ctc-table-page-layout {
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  min-width: 0;
  min-height: 0;
  padding: var(--layout-frame-gap, 16px);
  gap: var(--layout-frame-gap, 16px);
  background-color: var(--layout-workspace-bg, #f5f7fc);
  overflow: hidden;
}

/* 顶部独立卡片区 */
.ctc-table-page-layout__header {
  box-sizing: border-box;
  flex: none;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
  padding: 16px;
  background-color: var(--layout-content-bg, #ffffff);
  border-radius: var(--layout-card-radius, 4px);
  box-shadow: var(--layout-card-shadow, 0 1px 3px rgba(0, 0, 0, 0.05));
}

.ctc-table-page-layout__toolbar-bar,
.ctc-table-page-layout__search-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-width: 0;
}

.ctc-table-page-layout__bar-left,
.ctc-table-page-layout__bar-right {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.ctc-table-page-layout__bar-right {
  margin-left: auto;
}

/* 主容器 */
.ctc-table-page-layout__container {
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
}

/* 容器顶部：KPI 或统计卡 */
.ctc-table-page-layout__container-top {
  flex: none;
  min-width: 0;
}

/* 核心内容白卡：高度链自适应填满视口 */
.ctc-table-page-layout__body {
  box-sizing: border-box;
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  padding: 16px;
  background-color: var(--layout-content-bg, #ffffff);
  border-radius: var(--layout-card-radius, 4px);
  box-shadow: var(--layout-card-shadow, 0 1px 3px rgba(0, 0, 0, 0.05));
  overflow: hidden;
}

/* 表格顶栏 */
.ctc-table-page-layout__table-bar {
  flex: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-width: 0;
  margin-bottom: 12px;
}
.ctc-table-page-layout__table-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--layout-text-primary, #1e293b);
}
.ctc-table-page-layout__table-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}

/* 前置自定义内容 */
.ctc-table-page-layout__before {
  flex: none;
  min-width: 0;
  margin-bottom: 12px;
}

/* 表格视口承载容器：高度链关键节点，必须 min-height: 0 与 overflow: hidden */
.ctc-table-page-layout__table-container {
  box-sizing: border-box;
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
}

/* 后置追加区域 */
.ctc-table-page-layout__after {
  flex: none;
  min-width: 0;
  padding-top: 12px;
  border-top: 1px solid var(--layout-border-color, #e2e8f0);
}

/* 分页控制栏：紧贴白卡底部 */
.ctc-table-page-layout__pagination {
  flex: none;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  min-width: 0;
  padding-top: 12px;
}
</style>
