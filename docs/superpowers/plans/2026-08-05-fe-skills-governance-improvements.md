# FE Skills Governance Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将当前前端规范仓库调整为边界更准确、技术承诺更可信、能够自动校验的公司级 Skills 基线。

**Architecture:** 保持三个 skill 的现有职责，不引入新的大而全规范。`ctc-fe-structure` 明确 `shared/ui|lib|biz` 分区；`ctc-fe-vue3` 区分可自动执行规则和评审建议；浏览器兼容 skill 收敛为 Tailwind 4 的有限兼容评估与实验性方案，不再承诺完整降级。根目录提供轻量校验脚本，检查 skill frontmatter、链接和仓库一致性。

**Tech Stack:** Markdown、YAML frontmatter、Python 3、Agent Skills 校验器

**Status:** 已于 2026-08-05 实施并通过计划中的最终验证；下列复选框保留为原始执行清单。

---

### Task 1: 建立仓库验证基线

**Files:**
- Create: `scripts/validate-skills.py`
- Modify: `package.json`

- [ ] 编写校验脚本，枚举一级 skill 目录并校验 `SKILL.md` 的 `name`、`description`、目录名一致性和相对 Markdown 链接。
- [ ] 运行 `python3 scripts/validate-skills.py`，确认它能暴露当前 Vue description 尖括号、README 失效链接和仓库清单漂移。
- [ ] 在 `package.json` 中增加 `validate` 和 `test` 命令，并移除不存在的 CommonJS 入口声明。

### Task 2: 修订目录架构规范

**Files:**
- Modify: `ctc-fe-structure/SKILL.md`
- Modify: `ctc-fe-structure/references/structure.md`
- Modify: `ctc-fe-structure/references/boundaries.md`
- Modify: `ctc-fe-structure/references/naming.md`
- Modify: `ctc-fe-structure/references/governance.md`
- Modify: `ctc-fe-structure/references/migration.md`

- [ ] 将 `shared` 拆分为无业务语义的 `ui/lib/styles` 与稳定跨模块业务能力 `biz`。
- [ ] 写明 `shared/biz` 准入条件、依赖方向、公开出口、调用方包装规则及 `UserSelector`、`DictTag` 示例。
- [ ] 将“复用两次即上移”改为根据跨域范围、稳定性和所有权判断。
- [ ] 登记 `biz` 为团队批准缩写，并更新迁移与检查清单。

### Task 3: 修订 Vue 3 规范

**Files:**
- Modify: `ctc-fe-vue3/SKILL.md`

- [ ] 修复 frontmatter，使其通过 Agent Skill 校验并只描述触发场景。
- [ ] 将八段式顺序从无法自动证明的绝对规则改为推荐组织方式。
- [ ] 修正 `any`、`unknown`、异常收窄、循环依赖和 `type/interface` 的矛盾或过度承诺。
- [ ] 提供 ESLint flat config 示例，加入 scoped style、宏顺序、安全和 Vue 推荐规则，并明确每项规则的执行方式。

### Task 4: 收敛浏览器兼容 skill

**Files:**
- Modify: `ctc-fe-adapt-broswer/SKILL.md`
- Modify: `ctc-fe-adapt-broswer/references/legacyCss.md`
- Modify: `ctc-fe-adapt-broswer/references/browserTest.md`

- [ ] 保留现有目录名以避免破坏安装路径，但在文档中标记历史拼写和后续迁移建议。
- [ ] 明确 Tailwind 4 官方浏览器基线、有限兼容边界和真实浏览器验收要求。
- [ ] 将 `legacyCssCompat` 标记为项目特定实验方案，记录 `@layer`、`:where()`、`@property`、transform、gap 和 crossorigin 改写风险。
- [ ] 将验证从“语法已消除即兼容”升级为构建、功能、视觉和目标浏览器四层验证。

### Task 5: 修复仓库入口文档

**Files:**
- Modify: `README.md`

- [ ] 使用相对链接替换本机 `file://` 链接。
- [ ] 根据当前实际目录更新 skill 清单，不恢复已删除的 `postgres-sync`。
- [ ] 移除“完美合规、替代 Code Review”等过度承诺。
- [ ] 增加规范等级、验证命令及版本维护说明。

### Task 6: 最终验证

**Files:**
- Verify: all modified files

- [ ] 运行 `python3 scripts/validate-skills.py`，预期退出码 0。
- [ ] 运行 `npm test`，预期退出码 0。
- [ ] 运行官方 `quick_validate.py` 分别校验三个 skill，预期全部通过。
- [ ] 使用 `rg` 检查失效 `file://`、过期 `postgres-sync`、不准确的完整兼容承诺和未登记缩写。
- [ ] 检查 `git diff --check`、`git diff --stat` 和工作区状态，确认未覆盖任务外改动。
