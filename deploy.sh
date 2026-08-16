#!/usr/bin/env bash
# Deploy kosmos on the VPS. Run from the clone at /srv/kosmos:
#
#     ./deploy.sh                          # pull, sync from Notion, build, ship
#     ./deploy.sh seed_missions            # ...running these scripts first
#     ./deploy.sh --no-fetch               # code-only: skip the Notion pull
#
# Every step is named; the first failure stops the run and says which step.
# This replaces a hand-typed && chain that dropped its commit step three
# times in one day and was killed once by curl racing the restart.
#
# What it does, in order:
#   1. recover   — a previous partial run leaves data/ synced but uncommitted
#                  and public/ rebuilt; commit the data, discard public/
#                  (it is generated), refuse if anything else is dirty
#   2. pull      — git pull --rebase
#   3. seeds     — python3 scripts/<name>.py for each argument, in order
#   4. fetch     — fetch_elements.py + fetch_all.py   (unless --no-fetch)
#   5. build     — build.py
#   6. ship      — public/*.html + *.json -> $APP_DIR/public/, server.js -> $APP_DIR/
#   7. restart   — $RESTART, then poll /health until it answers ok:true with
#                  no missing pages
#   8. commit    — data/ + public/ if changed, then push
#
# Overridable for testing off the VPS:
#   APP_DIR=/opt/kosmos  PORT=3002  RESTART="systemctl restart kosmos"  NO_PUSH=1
set -euo pipefail

# The whole run lives in main() and is called on the last line, so bash parses
# this entire file before executing any of it. That matters because step 2 is a
# git pull that can update deploy.sh itself: bash reads scripts incrementally,
# and on 2026-08-16 an older copy of this file was mid-run when the pull
# replaced it — it kept executing stale lines and shipped without search.json.
main() {
APP_DIR="${APP_DIR:-/opt/kosmos}"
PORT="${PORT:-3002}"
RESTART="${RESTART:-systemctl restart kosmos}"
NO_PUSH="${NO_PUSH:-}"

cd "$(dirname "$0")"
REPO="$(pwd)"

STEP="start"
on_err() { echo; echo "DEPLOY FAILED at step: $STEP" >&2; exit 1; }
trap on_err ERR
step() { STEP="$1"; echo; echo "── $1"; }

# ---- args
FETCH=1
SEEDS=()
for a in "$@"; do
  case "$a" in
    --no-fetch) FETCH=0 ;;
    --*) echo "unknown flag: $a" >&2; exit 2 ;;
    *)  [[ -f "scripts/$a.py" ]] || { echo "no such script: scripts/$a.py" >&2; exit 2; }
        SEEDS+=("$a") ;;
  esac
done

[[ -d "$APP_DIR" ]] || { echo "APP_DIR $APP_DIR does not exist — this runs on the VPS (or set APP_DIR)" >&2; exit 2; }

# ---- 1. recover a partial previous run
step "recover"
if [[ -n "$(git status --porcelain)" ]]; then
  # public/ is generated from data/ + web/, so anything there is safe to drop
  git checkout -- public/ 2>/dev/null || true
  other="$(git status --porcelain | grep -v '^.. data/' || true)"
  if [[ -n "$other" ]]; then
    echo "uncommitted changes outside data/ and public/ — this clone is a deploy target, not a workspace:" >&2
    echo "$other" >&2
    exit 1
  fi
  if [[ -n "$(git status --porcelain)" ]]; then
    git add data
    git commit -q -m "Sync from Notion (recovered from an interrupted deploy)"
    echo "committed leftover data sync from a previous run"
  fi
else
  echo "clean"
fi

# ---- 2. pull
step "pull"
before="$(git rev-parse HEAD:deploy.sh 2>/dev/null || true)"
git pull --rebase origin main
after="$(git rev-parse HEAD:deploy.sh 2>/dev/null || true)"
if [[ "$before" != "$after" && -z "${DEPLOY_REEXEC:-}" ]]; then
  echo "deploy.sh itself was updated by the pull — re-running with the new version"
  DEPLOY_REEXEC=1 exec bash "$0" "$@"
fi

# ---- 3. seeds
if ((${#SEEDS[@]})); then
  for s in "${SEEDS[@]}"; do
    step "seed: $s"
    python3 "scripts/$s.py"
  done
fi

# ---- 4. fetch
if ((FETCH)); then
  step "fetch elements"
  python3 scripts/fetch_elements.py
  step "fetch all"
  python3 scripts/fetch_all.py
else
  step "fetch (skipped: --no-fetch)"
fi

# ---- 5. build
step "build"
python3 scripts/build.py

# ---- 6. ship
step "ship"
mkdir -p "$APP_DIR/public"
cp public/*.html public/*.json "$APP_DIR/public/"
cp server.js "$APP_DIR/"
echo "copied $(ls public/*.html public/*.json | wc -l) files -> $APP_DIR/public/, server.js -> $APP_DIR/"

# ---- 7. restart + health
step "restart"
t0=$(date +%s)
bash -c "$RESTART"
step "health"
# Poll until something answers, then insist it is a process started after the
# restart — a stale server that never went down would otherwise pass this
# check with the pages it loaded last time.
health=""
for i in $(seq 1 40); do
  if health="$(curl -sf --max-time 2 "http://127.0.0.1:$PORT/health" 2>/dev/null)"; then
    if python3 -c "import json,sys; h=json.loads(sys.argv[1]); sys.exit(0 if h.get('startedAt',0)/1000 >= $t0 - 1 else 1)" "$health"; then
      break
    fi
    health=""    # answered, but by the old process — keep waiting
  fi
  sleep 0.5
done
[[ -n "$health" ]] || { echo "no fresh process answered /health within 20s of the restart (a stale one may still be serving)" >&2; exit 1; }
echo "$health"
python3 - "$health" <<'PY'
import json, sys
h = json.loads(sys.argv[1])
if not h.get("ok") or h.get("missing"):
    print("health check failed:", h.get("missing") or h, file=sys.stderr)
    sys.exit(1)
print(f"ok — {h.get('pages')} pages, pid {h.get('pid')}, analyzer {'on' if h.get('analyzer') else 'OFF'}")
PY

# ---- 8. commit + push the sync
step "commit"
git add data public
if git diff --cached --quiet; then
  echo "nothing to commit"
else
  msg="Sync from Notion"
  ((${#SEEDS[@]})) && msg="$msg after ${SEEDS[*]}"
  git commit -q -m "$msg"
  echo "committed: $(git log --oneline -1)"
fi
if [[ -n "$NO_PUSH" ]]; then
  echo "push skipped (NO_PUSH)"
else
  step "push"
  git push origin main
fi

STEP="done"
echo
echo "deployed $(git rev-parse --short HEAD) — https://kosmos.yeahborhood.com"
}

main "$@"
