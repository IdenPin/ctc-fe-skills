---
name: postgres-sync
description: 把远程 PostgreSQL 数据库（测试/预发服）同步到本地 PostgreSQL 实例。使用 pg_dump 自定义格式 + pg_restore，配合 FORCE 删库与 template0/UTF8 重建。Use when the user asks to sync/copy/refresh/mirror/pull a PostgreSQL database from a remote/test/staging server to local, 或者用户说「同步/更新/拉取测试服数据库到本地」「pg_dump / pg_restore 在两台 PostgreSQL 之间复制数据」。
---

# PostgreSQL 数据库同步

把远程 PostgreSQL 数据库整库同步到本地：删除本地库 → 重建空库 → 远程 dump → 本地 restore → 校验。

## 何时使用

当用户提出以下需求时触发：
- 同步 / 复制 / 刷新 / 拉取 一个远程（测试 / 预发 / staging）PostgreSQL 数据库到本地
- 把测试服的 xx 数据库覆盖到本地
- 用 pg_dump / pg_restore 在两台 PG 间复制数据

## 前置条件

- 本机已安装 `psql` / `pg_dump` / `pg_restore`（macOS：`brew install libpq && brew link --force libpq`）
- 本地 PostgreSQL 已启动且可连
- 本地账号具备 `SUPERUSER` 或 `CREATEDB` 权限
- 远程 PG 的 `pg_hba.conf` 允许本机访问，且监听了对外地址

## 必要参数

执行前请先与用户确认。优先从项目 Spring Boot 配置（如 `application-dev.yaml`、`application-local-pg.yaml`）读取。

| 参数 | 示例 |
|------|------|
| 远程主机 | `192.168.5.170` |
| 远程端口 | `5432` |
| 远程用户 | `postgres` |
| 远程密码 | `jointsky@123.com` |
| 远程库名 | `ruoyi-vue-pro` |
| 本地用户 | `root` |
| 本地密码 | `com.ctcUniapp` |
| 本地库名 | `ruoyi-vue-pro` |

## 推荐流程：直接调用脚本

脚本封装了完整流程，是首选方式：

```bash
bash .qoder/skills/postgres-sync/scripts/sync.sh \
  --remote-host 192.168.5.170 \
  --remote-port 5432 \
  --remote-user postgres \
  --remote-pass 'jointsky@123.com' \
  --remote-db ruoyi-vue-pro \
  --local-user root \
  --local-pass 'com.ctcUniapp' \
  --local-db ruoyi-vue-pro
```

可选参数：
- `--local-host` / `--local-port`（默认 `127.0.0.1` / `5432`）
- `--keep-dump`：保留中间 dump 文件 `/tmp/<db>-<时间戳>.dump`
- `--verify-tables system_users,system_menu,system_role,system_dept`：附加行数校验
- `--dry-run`：只打印命令不执行

## 手动流程（脚本不可用时）

按顺序执行：

```bash
# 1. 测试远程连通性
PGPASSWORD='<REMOTE_PASS>' psql -h <REMOTE_HOST> -p <REMOTE_PORT> -U <REMOTE_USER> -d <REMOTE_DB> -c "SELECT version();"

# 2. 强制删除并重建本地库
PGPASSWORD='<LOCAL_PASS>' psql -U <LOCAL_USER> -d postgres \
  -c 'DROP DATABASE IF EXISTS "<LOCAL_DB>" WITH (FORCE);'
PGPASSWORD='<LOCAL_PASS>' psql -U <LOCAL_USER> -d postgres \
  -c 'CREATE DATABASE "<LOCAL_DB>" TEMPLATE template0 ENCODING '\''UTF8'\'' OWNER <LOCAL_USER>;'

# 3. 从远程 dump（自定义格式，去掉 owner / acl）
PGPASSWORD='<REMOTE_PASS>' pg_dump \
  -h <REMOTE_HOST> -p <REMOTE_PORT> -U <REMOTE_USER> -d <REMOTE_DB> \
  -Fc --no-owner --no-acl -f /tmp/<REMOTE_DB>.dump

# 4. 导入本地
PGPASSWORD='<LOCAL_PASS>' pg_restore \
  -U <LOCAL_USER> -d <LOCAL_DB> \
  --no-owner --no-acl /tmp/<REMOTE_DB>.dump

# 5. 校验
PGPASSWORD='<LOCAL_PASS>' psql -U <LOCAL_USER> -d <LOCAL_DB> -c \
  "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';"
```

## 关键决策（为什么这么做）

- **`-Fc` 自定义格式**：体积小，`pg_restore` 自动处理依赖顺序，支持并行恢复
- **`--no-owner --no-acl`**：避免本地缺少远程 owner 角色时报 "role does not exist"
- **`DROP ... WITH (FORCE)`**（PG 13+）：自动踢掉占用会话，告别 "database is being accessed by other users"
- **`TEMPLATE template0`**：避免 `template1` 的 locale / 编码不一致导致的 `CREATE DATABASE` 失败
- **不使用 `pg_dump | pg_restore` 管道**：保留中间文件便于失败重试和 `pg_restore -l` 检查内容

## 常见坑

| 现象 | 处理 |
|------|------|
| 本地报 `role "postgres" does not exist` | brew 装的 PG 没有 `postgres` 角色，使用 macOS 用户名或项目自建用户（如 `root`）|
| `database is being accessed by other users` | 关闭 Spring Boot 应用 + DBeaver / IDEA 数据库工具后重试（脚本默认带 FORCE）|
| 数据-only dump restore 时报 `relation "public.xxx" does not exist` | 不要用 `--data-only` 倒入空库；改用全量 dump（默认即是）|
| JVM 启动报 `UnknownHostException: 127.0.0.1` | 系统 SOCKS 代理问题，与同步无关，参考 `YudaoServerApplication` 处理 |
| macOS 提示 `pg_restore: command not found` | `brew install libpq && echo 'export PATH="/opt/homebrew/opt/libpq/bin:$PATH"' >> ~/.zshrc` |

## 同步完成后的回报模板

```
✅ 同步完成：<REMOTE_HOST>/<REMOTE_DB> → 本地/<LOCAL_DB>
   总表数：<N>
   system_users: <N>   system_menu: <N>
   system_role:  <N>   system_dept: <N>
   Dump 文件：/tmp/<REMOTE_DB>.dump（<size>）
```

## 安全注意

- 本 skill **会销毁本地数据库**，执行前必须与用户确认本地库名
- **绝不**把生产库设为本地目标
- 密码统一通过 `PGPASSWORD` 环境变量传递，避免出现在 `ps` 进程列表里
