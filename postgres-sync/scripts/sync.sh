#!/usr/bin/env bash
# postgres-sync: 把远程 PostgreSQL 数据库同步到本地
# 用法见上层 SKILL.md
set -euo pipefail

# ----- defaults -----
REMOTE_HOST=""
REMOTE_PORT="5432"
REMOTE_USER=""
REMOTE_PASS=""
REMOTE_DB=""
LOCAL_HOST="127.0.0.1"
LOCAL_PORT="5432"
LOCAL_USER=""
LOCAL_PASS=""
LOCAL_DB=""
KEEP_DUMP=false
DRY_RUN=false
VERIFY_TABLES="system_users,system_menu,system_role,system_dept"

# ----- arg parse -----
while [[ $# -gt 0 ]]; do
  case "$1" in
    --remote-host) REMOTE_HOST="$2"; shift 2 ;;
    --remote-port) REMOTE_PORT="$2"; shift 2 ;;
    --remote-user) REMOTE_USER="$2"; shift 2 ;;
    --remote-pass) REMOTE_PASS="$2"; shift 2 ;;
    --remote-db)   REMOTE_DB="$2";   shift 2 ;;
    --local-host)  LOCAL_HOST="$2";  shift 2 ;;
    --local-port)  LOCAL_PORT="$2";  shift 2 ;;
    --local-user)  LOCAL_USER="$2";  shift 2 ;;
    --local-pass)  LOCAL_PASS="$2";  shift 2 ;;
    --local-db)    LOCAL_DB="$2";    shift 2 ;;
    --verify-tables) VERIFY_TABLES="$2"; shift 2 ;;
    --keep-dump)   KEEP_DUMP=true;   shift ;;
    --dry-run)     DRY_RUN=true;     shift ;;
    -h|--help)
      grep -E '^# ' "$0" | sed 's/^# //'; exit 0 ;;
    *) echo "❌ Unknown option: $1" >&2; exit 2 ;;
  esac
done

# ----- validate -----
missing=()
for v in REMOTE_HOST REMOTE_USER REMOTE_PASS REMOTE_DB LOCAL_USER LOCAL_PASS LOCAL_DB; do
  [[ -z "${!v}" ]] && missing+=("--${v,,}" )  # zsh-safe via bash
done
if [[ ${#missing[@]} -gt 0 ]]; then
  echo "❌ Missing required args: ${missing[*]}" >&2
  echo "   Run with -h for help." >&2
  exit 2
fi

for cmd in psql pg_dump pg_restore; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "❌ $cmd not found in PATH"; exit 1; }
done

TS="$(date +%Y%m%d-%H%M%S)"
DUMP_FILE="/tmp/${REMOTE_DB}-${TS}.dump"

run() {
  if $DRY_RUN; then
    echo "DRY-RUN> $*"
  else
    eval "$@"
  fi
}

echo "🔧 Plan:"
echo "   Source: ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PORT}/${REMOTE_DB}"
echo "   Target: ${LOCAL_USER}@${LOCAL_HOST}:${LOCAL_PORT}/${LOCAL_DB}  (will be DROPPED)"
echo "   Dump:   ${DUMP_FILE}"
echo

# ----- 1. test remote -----
echo "▶ [1/5] Testing remote connection..."
run "PGPASSWORD='${REMOTE_PASS}' psql -h '${REMOTE_HOST}' -p '${REMOTE_PORT}' -U '${REMOTE_USER}' -d '${REMOTE_DB}' -c 'SELECT version();' >/dev/null"
echo "   ✅ remote ok"

# ----- 2. drop & recreate local -----
echo "▶ [2/5] Dropping & recreating local database..."
run "PGPASSWORD='${LOCAL_PASS}' psql -h '${LOCAL_HOST}' -p '${LOCAL_PORT}' -U '${LOCAL_USER}' -d postgres -c 'DROP DATABASE IF EXISTS \"${LOCAL_DB}\" WITH (FORCE);'"
run "PGPASSWORD='${LOCAL_PASS}' psql -h '${LOCAL_HOST}' -p '${LOCAL_PORT}' -U '${LOCAL_USER}' -d postgres -c 'CREATE DATABASE \"${LOCAL_DB}\" TEMPLATE template0 ENCODING '\\''UTF8'\\'' OWNER \"${LOCAL_USER}\";'"
echo "   ✅ local recreated"

# ----- 3. dump remote -----
echo "▶ [3/5] Dumping remote database (this may take a while)..."
run "PGPASSWORD='${REMOTE_PASS}' pg_dump -h '${REMOTE_HOST}' -p '${REMOTE_PORT}' -U '${REMOTE_USER}' -d '${REMOTE_DB}' -Fc --no-owner --no-acl -f '${DUMP_FILE}'"
if ! $DRY_RUN; then
  echo "   ✅ dump created: $(ls -lh "${DUMP_FILE}" | awk '{print $5}')"
fi

# ----- 4. restore -----
echo "▶ [4/5] Restoring into local database..."
# pg_restore returns non-zero on warnings (e.g. permissions); we tolerate but log.
if $DRY_RUN; then
  echo "DRY-RUN> PGPASSWORD='***' pg_restore -h '${LOCAL_HOST}' -p '${LOCAL_PORT}' -U '${LOCAL_USER}' -d '${LOCAL_DB}' --no-owner --no-acl '${DUMP_FILE}'"
else
  set +e
  PGPASSWORD="${LOCAL_PASS}" pg_restore \
    -h "${LOCAL_HOST}" -p "${LOCAL_PORT}" -U "${LOCAL_USER}" \
    -d "${LOCAL_DB}" --no-owner --no-acl "${DUMP_FILE}" 2>/tmp/pg_restore.err
  rc=$?
  set -e
  if [[ $rc -ne 0 ]]; then
    err_count=$(grep -c '^pg_restore: error' /tmp/pg_restore.err || true)
    warn_count=$(grep -c '^pg_restore: warning' /tmp/pg_restore.err || true)
    echo "   ⚠️  pg_restore exited $rc (errors=${err_count}, warnings=${warn_count}). See /tmp/pg_restore.err"
  else
    echo "   ✅ restore completed without errors"
  fi
fi

# ----- 5. verify -----
echo "▶ [5/5] Verifying..."
if $DRY_RUN; then
  echo "DRY-RUN> verify queries"
else
  TOTAL=$(PGPASSWORD="${LOCAL_PASS}" psql -h "${LOCAL_HOST}" -p "${LOCAL_PORT}" -U "${LOCAL_USER}" -d "${LOCAL_DB}" -tAc \
    "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';")
  echo "   Total tables: ${TOTAL}"

  IFS=',' read -ra TBLS <<< "${VERIFY_TABLES}"
  for t in "${TBLS[@]}"; do
    t_trim="$(echo -n "$t" | tr -d '[:space:]')"
    [[ -z "$t_trim" ]] && continue
    cnt=$(PGPASSWORD="${LOCAL_PASS}" psql -h "${LOCAL_HOST}" -p "${LOCAL_PORT}" -U "${LOCAL_USER}" -d "${LOCAL_DB}" -tAc \
      "SELECT count(*) FROM \"${t_trim}\";" 2>/dev/null || echo "N/A")
    printf "   %-30s %s\n" "${t_trim}:" "${cnt}"
  done
fi

# ----- cleanup -----
if ! $KEEP_DUMP && ! $DRY_RUN; then
  rm -f "${DUMP_FILE}"
  echo "   🧹 dump file removed (use --keep-dump to retain)"
else
  echo "   📁 dump kept at ${DUMP_FILE}"
fi

echo
echo "✅ Sync complete: ${REMOTE_HOST}/${REMOTE_DB} → local/${LOCAL_DB}"
