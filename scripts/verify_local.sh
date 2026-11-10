#!/usr/bin/env bash
# Verifies the local Docker deployment of the Pair 17 Handshake platform.
#
#   scripts/verify_local.sh             # health, gateway routing, MongoDB, assistant reachability
#   scripts/verify_local.sh --chat      # also send one real message through the assistant (needs Ollama)
#   scripts/verify_local.sh --failover  # also stop MongoDB and confirm health checks go 503/unhealthy and recover
#
# Requires: docker compose stack running and seeded (see docker-compose.yml header), curl, python3.
set -uo pipefail

WEB=${WEB:-http://localhost:9170}
STUDENT_EMAIL=student001@seed.p17.example
COMPANY_EMAIL=company001@seed.p17.example
PASSWORD='SeedPass17!'
SERVICES=(student:9171 company:9172 job:9173 application:9174 event:9175 assistant:9176)

RUN_CHAT=false; RUN_FAILOVER=false
for arg in "$@"; do
  case $arg in --chat) RUN_CHAT=true ;; --failover) RUN_FAILOVER=true ;; *) echo "unknown flag $arg"; exit 2 ;; esac
done

failures=0
pass() { printf '  \033[32mPASS\033[0m %s\n' "$*"; }
fail() { printf '  \033[31mFAIL\033[0m %s\n' "$*"; failures=$((failures + 1)); }
section() { printf '\n== %s\n' "$*"; }
json() { python3 -c "import json,sys; d=json.load(sys.stdin); print($1)" 2>/dev/null || echo "(no JSON body)"; }

# expect STATUS DESCRIPTION curl-args...  (prints body to stdout of $BODY)
expect() {
  local want=$1 desc=$2; shift 2
  local out code
  out=$(curl -s -m 30 -w '\n%{http_code}' "$@")
  code=${out##*$'\n'}; BODY=${out%$'\n'*}
  if [[ $code == "$want" ]]; then pass "$desc -> HTTP $code"; else fail "$desc -> HTTP $code (want $want): ${BODY:0:200}"; fi
}

section "1. Container health (docker HEALTHCHECK)"
while read -r name status; do
  if [[ $status == *"(healthy)"* ]]; then pass "$name $status"; else fail "$name $status"; fi
done < <(docker compose ps --format '{{.Name}} {{.Status}}')

section "2. Service /health endpoints (direct host ports)"
for entry in "${SERVICES[@]}"; do
  svc=${entry%%:*}; port=${entry##*:}
  expect 200 "$svc :$port /health" "http://localhost:$port/health"
  echo "       $(echo "$BODY" | json "', '.join(f\"{k}={v['status']}\" for k,v in d['checks'].items())")"
done

section "3. Frontend reaches backend (through the nginx gateway on $WEB)"
expect 200 "SPA index.html" "$WEB/"
[[ $BODY == *'<div id="root">'* ]] && pass "index.html contains the React root" || fail "index.html missing React root"
expect 200 "SPA deep link /login falls back to index.html" "$WEB/login"
for entry in "${SERVICES[@]}"; do
  svc=${entry%%:*}; expect 200 "gateway /api/health/$svc" "$WEB/api/health/$svc"
done

expect 200 "student login (company service)" -X POST "$WEB/api/auth/login" \
  -H 'Content-Type: application/json' -d "{\"email\":\"$STUDENT_EMAIL\",\"password\":\"$PASSWORD\"}"
STUDENT_TOKEN=$(echo "$BODY" | json "d['access_token']" 2>/dev/null || true)
expect 200 "company login (company service)" -X POST "$WEB/api/auth/login" \
  -H 'Content-Type: application/json' -d "{\"email\":\"$COMPANY_EMAIL\",\"password\":\"$PASSWORD\"}"
COMPANY_TOKEN=$(echo "$BODY" | json "d['access_token']" 2>/dev/null || true)

S=(-H "Authorization: Bearer $STUDENT_TOKEN"); C=(-H "Authorization: Bearer $COMPANY_TOKEN")
expect 200 "student profile        -> student service"     "${S[@]}" "$WEB/api/students/me"
expect 200 "student preferences    -> student service"     "${S[@]}" "$WEB/api/student/preferences"
expect 200 "student job search     -> job service"         "${S[@]}" "$WEB/api/student/jobs?limit=3"
echo "       jobs total=$(echo "$BODY" | json "d['total']")"
expect 200 "student applications   -> application service" "${S[@]}" "$WEB/api/student/applications"
expect 200 "student events         -> event service"       "${S[@]}" "$WEB/api/student/events"
expect 200 "company profile        -> company service"     "${C[@]}" "$WEB/api/companies/me"
expect 200 "company dashboard      -> company service"     "${C[@]}" "$WEB/api/dashboards/company"
expect 200 "company jobs           -> job service"         "${C[@]}" "$WEB/api/jobs/mine"
expect 200 "company events         -> event service"       "${C[@]}" "$WEB/api/events/mine"
expect 200 "company team           -> company service"     "${C[@]}" "$WEB/api/team/members"
expect 401 "unauthenticated request is rejected"                     "$WEB/api/student/jobs"
expect 404 "unknown /api path is not routed"                         "$WEB/api/nope"

section "4. Backend services reach MongoDB (ping from inside each container)"
for entry in "${SERVICES[@]}"; do
  svc=${entry%%:*}
  if out=$(docker exec "p17-$svc-service" python -c "
import os; from pymongo import MongoClient
c = MongoClient(os.environ['MONGO_URI'], serverSelectionTimeoutMS=3000)
print(c.admin.command('ping')['ok'], c.server_info()['version'])" 2>&1); then
    pass "p17-$svc-service -> p17-mongodb ping ok=${out% *} (MongoDB ${out#* })"
  else fail "p17-$svc-service -> p17-mongodb: $out"; fi
done

section "5. AI Assistant reaches platform services and Ollama"
expect 200 "assistant /health" "http://localhost:9176/health"
echo "$BODY" | python3 2>/dev/null -c "
import json, sys
for name, c in json.load(sys.stdin)['checks'].items():
    print(f\"       {name:<12} {c['status']:<5} {c.get('detail', c.get('error', ''))}\")"
for target in student:9171 job:9173 event:9175 application:9174 company:9172; do
  svc=${target%%:*}; port=${target##*:}
  if docker exec p17-assistant-service python -c "import urllib.request as u; u.urlopen('http://p17-$svc-service:$port/health', timeout=5)" 2>/dev/null; then
    pass "p17-assistant-service -> p17-$svc-service:$port/health"
  else fail "p17-assistant-service -> p17-$svc-service:$port/health"; fi
done

if $RUN_CHAT; then
  echo "  ... sending a chat turn to the local model (can take a minute on CPU)"
  expect 200 "POST /api/assistant/chat via gateway" -m 400 -X POST "$WEB/api/assistant/chat" "${S[@]}" \
    -H 'Content-Type: application/json' \
    -d '{"message":"Find me internship jobs in Palo Alto","conversation":[]}'
  echo "$BODY" | python3 2>/dev/null -c "
import json, sys
d = json.load(sys.stdin)
print(f\"       tool_call_count={d['tool_call_count']}\")
print('       answer: ' + d['answer'][:400].replace(chr(10), chr(10) + '               '))"
fi

if $RUN_FAILOVER; then
  section "6. Health checks react to a dependency failure (stopping p17-mongodb)"
  docker stop p17-mongodb >/dev/null
  expect 503 "job service /health while MongoDB is down" "http://localhost:9173/health"
  echo "       mongodb check: $(echo "$BODY" | json "d['checks']['mongodb']")"
  echo "  ... waiting for Docker to mark p17-job-service unhealthy (5 failed probes x 15s)"
  for _ in $(seq 1 24); do
    [[ $(docker inspect -f '{{.State.Health.Status}}' p17-job-service) == unhealthy ]] && break; sleep 5
  done
  [[ $(docker inspect -f '{{.State.Health.Status}}' p17-job-service) == unhealthy ]] \
    && pass "Docker marked p17-job-service unhealthy" || fail "p17-job-service never became unhealthy"
  docker start p17-mongodb >/dev/null
  echo "  ... MongoDB restarted, waiting for recovery"
  for _ in $(seq 1 24); do
    [[ $(docker inspect -f '{{.State.Health.Status}}' p17-job-service) == healthy ]] && break; sleep 5
  done
  [[ $(docker inspect -f '{{.State.Health.Status}}' p17-job-service) == healthy ]] \
    && pass "p17-job-service recovered to healthy" || fail "p17-job-service did not recover"
fi

section "Result"
if ((failures == 0)); then echo "  All checks passed."; else echo "  $failures check(s) failed."; exit 1; fi
