---
name: gf-fullstack-dev
description: 用于 GF 监测与执法体系的全栈开发和跨仓排查；提供当前已登记仓库清单，并为尚未补齐的子应用预留扩展方式。
---

# GF 全栈开发

本 skill 面向 GF 整体项目的多业务系统全栈开发，指导 AI 跨独立仓库分析和开发。GF 包含“监测”和“执法”两套体系。当前清单收录了“监测”体系中已提供的 `operations`（运维）和 `auto-monitor`（自动监控）仓库；监测体系内其他子系统可按清单格式继续补充。“执法”体系预留目录和扩展模板，子应用与仓库映射后续补齐。

## 本地工作区

监测和执法属于独立业务领域，分别使用独立的工作区根目录；不要把两套体系合并到同一工作区根目录。开发人员手动拉取仓库，并在开发某个领域时打开对应工作区作为 AI 根目录。若任务跨两个领域，应确保两个工作区都可访问，同时保持各自仓库独立。

```text
监测体系工作区：gf-monitor-ai/
├── operations/
│   ├── backend/
│   └── frontend/
├── auto-monitor/
│   ├── backend/
│   └── frontend/
└── <其他监测子系统>/  # 按实际仓库增补

执法体系工作区：gf-law-ai/
└── <执法子应用>/  # 预留；子应用和仓库映射待补齐
```

每个子目录都是独立 Git 工作区。不要把这些仓库合并，也不要假设只打开其中一个仓库就能访问其他仓库。

### 任务入口：确定业务领域

- 开始读代码前，先确定任务属于监测、执法，还是同时涉及两个领域。
- 用户明确指定时按指定领域工作；未指定时，可根据当前打开的 `gf-monitor-ai/` 或 `gf-law-ai/` 工作区和任务涉及的系统名判断。
- 领域无法可靠判断时，先向用户确认，不要默认把任务归到监测体系。
- 跨领域任务需要两个工作区都可访问；分别盘点仓库、分支和工作区状态，保持仓库彼此独立。
- 当前只有监测体系的仓库地址清单。执法领域在仓库映射补齐前，只能分析已提供且本地可访问的代码，并明确覆盖范围。

## 仓库清单

| 项目 | 端 | 本地目录 | Git 地址 | 说明 |
|---|---|---|---|---|
| 运维 | 后端 | `operations/backend/amdb-yw` | `http://192.168.6.139/project/backend/mointor/amdb-yw.git` | 运维后端 |
| 运维 | 后端 | `operations/backend/jointsky-operations-api` | `http://192.168.6.139/zhangbinbin/jointsky-operations-api.git` | 运维第三方数据接入 |
| 运维 | 前端 | `operations/frontend/zdjk-provider-mobile` | `http://192.168.6.139/project/front/guo-fa/public/zdjk-provider-mobile.git` | 运维移动端 |
| 运维 | 前端 | `operations/frontend/zdjk-provider-filing` | `http://1.85.6.157:6139/project/front/guo-fa/public/zdjk-provider-filing.git` | 运维 PC 端 |
| 运维 | 前端 | `operations/frontend/provider-common` | `http://192.168.6.139/project/front/guo-fa/public/provider-common.git` | 运维记录详情公共组件 |
| 自动监控 | 后端 | `auto-monitor/backend/amdb` | `http://192.168.6.139/project/backend/mointor/amdb.git` | 包含部分企业端和管理端功能，后端覆盖不完整 |
| 自动监控 | 前端 | `auto-monitor/frontend/zdjk-system` | `http://192.168.6.139/project/front/guo-fa/public/zdjk-system.git` | 管理端 |
| 自动监控 | 前端 | `auto-monitor/frontend/zdjk-company` | `http://1.85.6.157:6139/project/front/guo-fa/public/zdjk-company.git` | 企业端 |

当前清单记录了以上 8 个 Git 仓库，均属于“监测”体系；这些路径相对于 `gf-monitor-ai/`。这份清单可随其他监测子系统继续扩展。此前移除的 SVN 地址不属于当前代码来源。“执法”使用独立的 `gf-law-ai/` 工作区，子应用名称、仓库地址和职责尚待维护；收到相关任务时，先从用户或项目文档确认这些信息，不要根据系统名称臆造仓库或代码归属。

### 执法体系扩展模板

补齐执法体系时，按实际子应用逐项填写，明确前端、后端、公共组件和接口关联；表中本地目录相对于 `gf-law-ai/`。确认目录拓扑后，再扩展克隆命令：

| 子业务系统/应用 | 端 | 本地目录 | Git 地址 | 关联仓库或接口 | 分支/版本约定 |
|---|---|---|---|---|---|
| 待补充 | 待补充 | 待补充 | 待补充 | 待补充 | 待补充 |

以下命令用于手动准备 `gf-monitor-ai/` 下当前已登记的监测仓库。执法仓库映射补齐后，再按实际目录为 `gf-law-ai/` 增补拉取命令。AI 不要在用户未要求时自行 clone、fetch、pull：

```sh
mkdir -p gf-monitor-ai/operations/backend gf-monitor-ai/operations/frontend gf-monitor-ai/auto-monitor/backend gf-monitor-ai/auto-monitor/frontend
cd gf-monitor-ai
git clone http://192.168.6.139/project/backend/mointor/amdb-yw.git operations/backend/amdb-yw
git clone http://192.168.6.139/zhangbinbin/jointsky-operations-api.git operations/backend/jointsky-operations-api
git clone http://192.168.6.139/project/front/guo-fa/public/zdjk-provider-mobile.git operations/frontend/zdjk-provider-mobile
git clone http://1.85.6.157:6139/project/front/guo-fa/public/zdjk-provider-filing.git operations/frontend/zdjk-provider-filing
git clone http://192.168.6.139/project/front/guo-fa/public/provider-common.git operations/frontend/provider-common
git clone http://192.168.6.139/project/backend/mointor/amdb.git auto-monitor/backend/amdb
git clone http://192.168.6.139/project/front/guo-fa/public/zdjk-system.git auto-monitor/frontend/zdjk-system
git clone http://1.85.6.157:6139/project/front/guo-fa/public/zdjk-company.git auto-monitor/frontend/zdjk-company
```

执行前确认目标路径尚未包含现有仓库。若已有仓库，应检查并沿用，不要覆盖。涉及当前清单中仓库的完整跨端分析时，确保相关仓库都可见；缺少仓库时，说明会影响哪些判断。涉及清单外的监测子系统或“执法”体系时，先确认并补齐相关子应用与仓库映射，再做跨仓分析。

## 开始分析或开发前

1. 阅读工作区和仓库内适用的 `AGENTS.md` 等开发约定。
2. 盘点当前领域工作区内相关子系统的仓库。对每个存在的仓库检查 `origin` 地址、当前分支、提交号和工作区改动。可使用 `git -C <仓库路径> remote -v`、`git -C <仓库路径> status --short --branch`、`git -C <仓库路径> rev-parse HEAD`。
3. 为任务涉及的每个仓库确认目标分支、标签或提交。各仓库分支名可能不同；不要假设所有仓库使用同名分支，也不要默认最新分支就是需求版本。
4. 目标版本明确且仓库没有未提交改动时，先切换到指定版本再追踪代码。只做只读熟悉时，目标未指定可以先检查当前版本并明确标注；修改代码或做版本敏感的对比前，若目标版本仍不明确，应询问用户。工作区有未提交改动时，不覆盖、不丢弃改动；先说明状态，再处理切换需求。
5. 开发人员负责手动拉取仓库并准备本地工作区。不要默默 clone、fetch、pull 或切换分支来填补缺失。仓库缺失时，指出因此无法确认的代码链路。

按任务维护简短版本清单：

| 仓库 | 需求版本 | 当前版本 | 工作区状态 | 结果 |
|---|---|---|---|---|

## 跨仓库排查方式

- 动手前先确定功能属于“监测”还是“执法”体系，再确定子业务系统、用户端、相关公共组件和后端仓库。执法体系映射尚未补齐时，先确认任务涉及的仓库和职责。
- 对前后端功能，沿实际页面或路由、组件、请求封装和接口路径，继续追踪到后端路由/控制器、服务及相关数据处理。接口路径、参数和返回值都要从所选版本的源码确认，不根据仓库名称推断。
- 运维记录详情相关功能要检查 `provider-common`，并查看其调用方，评估公共改动的影响。
- `amdb` 只包含部分企业端和管理端后端功能。需要确认它实际实现了哪些接口；如果对应实现不在现有代码中，明确指出，不要默认由 `amdb-yw` 或其他仓库负责。
- 仓库存在 `.codegraph/` 时，先用 CodeGraph 理解代码，再使用 grep/find 或大范围读取。若有 CodeGraph MCP 工具则使用该工具；否则从对应仓库执行 `codegraph explore "<符号或问题>"`。没有 `.codegraph/` 时再使用常规代码搜索。
- 遵循各仓库自己的约定。不要假设不同仓库使用相同的框架、依赖版本、命令、接口归属或分支规则。

## 修改与汇报

- 只修改任务相关的仓库；各仓库保持独立的工作区和 Git 历史。
- 修改前后检查 Git 状态。不要丢弃用户改动，也不要擅自 commit 或 push。
- 遵循当前任务关于验证的要求；汇报中区分实际执行的检查和未验证的部分。
- 按仓库汇总结果。跨端任务应说明已从前端到接口再到后端核实的调用链，并指出缺失仓库、未确认的代码归属或版本不匹配。
