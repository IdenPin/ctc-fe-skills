# Naming Reference

## 核心策略

**目录一律短横线 (`kebab-case`)，组件一律大驼峰 (`PascalCase`)，组合函数一律以 `use` 开头的小驼峰 (`camelCase`)，普通 TS 文件按领域语义命名并保持全项目统一。**

## 目录命名 (`kebab-case`)

- 推荐：`features/user-profile/`、`views/system/user/`
- 避免：`UserProfile/`、`user_profile/`
- 原因：规范化路径，避免在跨平台（如 Windows、Linux、macOS）合并代码时发生大小写文件系统冲突。

### 目录名称简化原则

目录名称应追求精炼但无歧义。简化必须基于以下五条原则，而非随意删减单词：

**原则 1：保留核心业务语义词汇，去除冗余修饰词**

目录名的首要职责是表达"这是什么业务域"，而非"这个域属于什么管理类别"。`-management`、`-settings`、`-config`、`-info` 等后缀在目录层级中通常是冗余的——因为目录本身已经暗示了管理/配置的语境。

| 简化前 | 简化后 | 理由 |
|--------|--------|------|
| `user-management/` | `user/` | 目录上下文已暗示管理职能，`-management` 不增加语义 |
| `role-management/` | `role/` | 同上 |
| `system-settings/` | `system/` | 设置是 system 的隐含职责，无需显式标注 |
| `order-info/` | `order/` | `info` 不增加区分度，order 本身即信息载体 |
| `log-config/` | `log/` | 配置是 log 的子集行为，非独立业务域 |

**原则 2：避免路径中重复层级语义**

当父目录已经表达了某个语义时，子目录不应重复该语义。路径的可读性来自每一层贡献**新的**信息，而非复述已有信息。

| 简化前 | 简化后 | 理由 |
|--------|--------|------|
| `system-management/role-management/` | `system/role/` | 两级都含 `management`，冗余复述 |
| `user-center/user-profile/` | `user/profile/` | 父级 `user` 已表达归属，`center` 无新信息 |
| `order-management/order-list/` | `order/list/` | 父级 `order` 已表达域，子级再写 `order` 是重复 |
| `data-analysis/analysis-report/` | `data/report/` | `analysis` 出现两次，子级改为 `report` 贡献新信息 |

**原则 3：简化后仍需清晰表达业务含义**

简化不是压缩，删除词汇后目录名仍需让人一眼理解其业务归属。如果删减后产生歧义或语义模糊，则不应删减。

- `payment-channel/` → `channel/` ❌（脱离上下文后 `channel` 可指通信频道、WebSocket 通道等，歧义大）
- `payment-channel/` → `payment/` ✅（保留核心业务域，`channel` 为实现细节可由子目录表达）
- `user-permission/` → `permission/` ✅（在 system 上下文中 `permission` 语义清晰）
- `user-permission/` → `user/` ❌（若 `user/` 已被用户管理模块占用，则产生冲突）

**原则 4：遵循项目已有命名约定和模式**

简化必须与项目现有目录结构保持一致。若项目已建立 `views/system/` 模式，新增模块应沿用而非另起 `views/sys-mgmt/`。统一性优先于个人偏好。

- 若项目已有 `views/system/user/`、`views/system/role/`，则新增应写 `views/system/dept/`，而非 `views/department/` 或 `views/system/dept-management/`
- 若项目已有 `features/order/` 模式，则新增退款模块应写 `features/refund/`，而非 `modules/refund/` 或 `features/order-refund/`（退款若独立于订单则用独立域）

**原则 5：审慎使用单词缩写**

缩写可以缩短路径，但会降低可读性。使用缩写需满足以下条件：

- **行业通识缩写**：团队内外均可无歧义理解，可直接使用
- **项目约定缩写**：团队内部达成共识，需在项目文档中登记，谨慎使用
- **禁止自创缩写**：任何人不可凭个人习惯发明缩写

| 缩写 | 全称 | 分类 | 可用性 |
|------|------|------|--------|
| `sys` | system | 行业通识 | ✅ 可用 |
| `cfg` | config | 行业通识 | ✅ 可用 |
| `auth` | authentication/authorization | 行业通识 | ✅ 可用 |
| `msg` | message | 行业通识 | ✅ 可用 |
| `pwd` | password | 行业通识 | ✅ 可用 |
| `mgr` | manager | 项目约定 | ⚠️ 需登记共识后使用 |
| `svc` | service | 项目约定 | ⚠️ 需登记共识后使用 |
| `dept` | department | 项目约定 | ⚠️ 需登记共识后使用 |
| `usr` | user | 自创式 | ❌ 禁止（`user` 本身已足够短） |
| `perm` | permission | 自创式 | ❌ 禁止（容易与 `per-m` 等混淆，`permission` 更清晰） |
| `mngt` | management | 自创式 | ❌ 禁止（应直接删掉 `-management` 而非缩写） |

**缩写决策流程**：遇到需要缩写的场景 → 判断是否为行业通识 → 是则直接使用 → 否则评估是否项目约定 → 是则在项目文档登记后使用 → 否则禁止使用，保留全称或按原则 1 删除冗余词。

### 简化实操示例

以下是一个完整目录结构的简化前后对比，展示五条原则的综合应用：

```
简化前                                    简化后
─────────────────────────────            ─────────────────────────────
src/                                     src/
  views/                                   views/
    system-management/                      system/
      user-management/                        user/
      role-management/                        role/
      dept-management/                        dept/
      menu-management/                        menu/
      log-config/                             log/
    order-management/                      order/
      order-list/                            list/
      order-detail/                          detail/
      refund-management/                     refund/
    data-analysis/                         data/
      analysis-report/                       report/
      analysis-dashboard/                    dashboard/
    payment-management/                    payment/
      payment-channel/                       channel/    ← 若项目无歧义可简化
      payment-record/                        record/
```

## 组件命名 (`PascalCase`)

除页面入口保持框架约定（如 `index.vue`、`page.tsx`、`layout.tsx`）外，所有组件必须是强语义大驼峰：

- 推荐：`UserFormModal.vue`、`RefundDetailPanel.vue`、`UserTable.vue`
- 避免：`form.vue`、`modal.vue`、`detail.vue`、`index2.vue`
- 价值：利于 IDE 检索，且组件文件名与代码内导出的 Class/类名一一对应，对 AI 的代码生成和上下文理解极其友好。

## 局部文件命名规范

### hooks / composables

必须使用 `useXxx` 小驼峰，如 `useUserGrid.ts`、`useOrderActions.ts`。避免 `userHook.ts`。

### store

单一模块闭环内可直接使用 `store.ts`。若同目录下因业务极度复杂存在多个 store，采用强语义：`userStore.ts`、`permissionStore.ts`。

### api / types

普通模块闭环内直接用 `api.ts`、`types.ts`。复杂模块可拆为 `api/` 或 `types/` 目录，内含强语义子文件（如 `api/userApi.ts`、`api/roleApi.ts`，或者按资源组织为 `api/user.ts`、`api/role.ts`，二选一不要混用），严禁建立全局 `src/types/index.ts` 大杂烩。

### utils / constants

必须说明特定领域：`dateRange.ts`、`priceFormat.ts`、`treeTransform.ts`、`permissionCode.ts`。严禁使用泛化的 `utils.ts`、`helper.ts`、`common.ts`、`format.ts`。

### 样式与测试文件

- **样式**：组件私有样式优先写在组件内。独立样式文件使用语义名：`user-table.css`、`theme-vars.css`。避免 `style.css`、`common.scss`。
- **测试**：单元测试与被测文件同名：`UserFormModal.test.ts`。端到端测试可用场景名：`user-create.spec.ts`。
