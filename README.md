# CTC FE Skills - 团队前端开发规范

这是一个专为 `ctcfront` 团队定制的前端开发规范 Skill 仓库。该规范通过 `skills` 客户端进行分发，可直接供团队成员或 AI 编码助手（如 Cursor、Gemini 等）在开发中进行静态约束与规范调用。

[![skills.sh](https://skills.sh/b/IdenPin/ctc-fe-skills)](https://skills.sh/IdenPin/ctc-fe-skills)

---

## 🛠️ 安装说明

团队成员或外部贡献者可以通过 `skills` 客户端，从 GitHub 公网一键导入这些规范到本地：

### 1. 一键安装本仓库的所有规范 (推荐)
```bash
npx skills add IdenPin/ctc-fe-skills -y
```

### 2. 精准按需安装单个规范
* **只安装目录架构与依赖治理规范 (`ctc-fe-structure`)**：
  ```bash
  npx skills add IdenPin/ctc-fe-skills --skill ctc-fe-structure -y
  ```
* **只安装 Vue 3 + TS 编码风格规范 (`ctc-fe-vue3`)**：
  ```bash
  npx skills add IdenPin/ctc-fe-skills --skill ctc-fe-vue3 -y
  ```
* **只安装 PostgreSQL 数据库同步规范 (`postgres-sync`)**：
  ```bash
  npx skills add IdenPin/ctc-fe-skills --skill postgres-sync -y
  ```

---

## 📌 Skills 规范概览

### 1. [ctc-fe-structure](file:///Users/pdeng/ctc/ctc-fe-skills/ctc-fe-structure/SKILL.md) — 目录拓扑与依赖治理规范
* **核心职责**：规范大型项目、中后台系统的物理层级架构（`app / features / shared / services`），定义物理级业务模块的“就近闭环”边界，严防循环依赖和模块越界穿透。
* **主要分册**：
  * [structure.md](file:///Users/pdeng/ctc/ctc-fe-skills/ctc-fe-structure/references/structure.md) (拓扑与共享接口)
  * [boundaries.md](file:///Users/pdeng/ctc/ctc-fe-skills/ctc-fe-structure/references/boundaries.md) (单向依赖与 Router/Store 边界)
  * [naming.md](file:///Users/pdeng/ctc/ctc-fe-skills/ctc-fe-structure/references/naming.md) (去冗余目录简化原则及命名规范)
  * [migration.md](file:///Users/pdeng/ctc/ctc-fe-skills/ctc-fe-structure/references/migration.md) (老项目就近闭环迁移方案)
  * [governance.md](file:///Users/pdeng/ctc/ctc-fe-skills/ctc-fe-structure/references/governance.md) (测试、i18n、配置就近治理)

### 2. [ctc-fe-vue3](file:///Users/pdeng/ctc/ctc-fe-skills/ctc-fe-vue3/SKILL.md) — Vue 3 & TS 编码风格规范
* **核心职责**：规范 SFC `<script setup>` 组件内部的 **8段式逻辑书写顺序**。针对 TypeScript 类型安全实施 **`any` 警告降级与局部逃生通道（`eslint-disable-next-line`）** 的平滑过渡策略，强制 scoped 样式隔离，并配有 ESLint/Prettier 的"无分号"标准配置模板。

### 3. [postgres-sync](file:///Users/pdeng/ctc/ctc-fe-skills/postgres-sync/SKILL.md) — PostgreSQL 数据库同步规范
* **核心职责**：把远程 PostgreSQL 数据库（测试/预发服）整库同步到本地实例。封装了完整的 **删库 → 重建 → dump → restore → 校验** 流程，提供一键脚本 `sync.sh` 与手动命令两种方式，覆盖 macOS `libpq` 安装、权限角色缺失、会话占用等常见坑。
* **主要文件**：
  * [SKILL.md](file:///Users/pdeng/ctc/ctc-fe-skills/postgres-sync/SKILL.md) (规范文档：前置条件、参数、流程、常见坑)
  * [sync.sh](file:///Users/pdeng/ctc/ctc-fe-skills/postgres-sync/scripts/sync.sh) (一键同步脚本)

---

## 🤖 配合 AI 协同开发 (AI-Friendly)

这些规范在设计之初就深度考虑了 **AI 协同编码（RAG 检索）**。本地安装完成后，你可以在与 AI 助手聊天时直接引用：

> **Prompts 引用示例**：
> * "*请参照本地 `ctc-fe-structure` 规范，为我现有的 views 进行就近闭环重构，说明移动步骤。*"
> * "*根据本地 `ctc-fe-vue3` 规范，帮我写一个列表筛选组件，注意 script setup 内部的逻辑书写顺序，不需要写分号。*"
> * "*参照本地 `postgres-sync` 规范，把测试服的数据库同步到本地，帮我执行一键脚本。*"

AI 会自动根据安装好的规范，产出结构一致、完美合规的代码，省去了大量人工修改和 Code Review 的心智成本。
