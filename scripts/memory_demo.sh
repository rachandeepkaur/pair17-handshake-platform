#!/usr/bin/env bash
# Assistant memory demo: /memory before, consolidation through Kafka, /memory after, checks.
#
#   scripts/memory_demo.sh            # re-seeds student001's 60-entry memory first
#   scripts/memory_demo.sh --no-reseed
set -uo pipefail
cd "$(dirname "$0")/.."
WEB=${WEB:-http://localhost:9170}
section() { printf '\n== %s\n' "$*"; }
chat() {  # chat TOKEN MESSAGE -> prints the answer
  curl -s -m 600 -X POST "$WEB/api/assistant/chat" -H "Authorization: Bearer $1" -H 'Content-Type: application/json' \
    -d "$(python3 -c 'import json,sys; print(json.dumps({"message": sys.argv[1], "conversation": []}))' "$2")" \
    | python3 -c 'import json,sys; print(json.load(sys.stdin)["answer"])'
}

if [[ ${1:-} != --no-reseed ]]; then
  section "0. Seed the instruction layer and student001's learned memory (60 entries)"
  docker compose --profile seed run --rm --entrypoint python p17-db-seed -m db.seed.assistant_memory 2>/dev/null | tail -1
fi

TOKEN=$(curl -s -X POST "$WEB/api/auth/login" -H 'Content-Type: application/json' \
  -d '{"email":"student001@seed.p17.example","password":"SeedPass17!"}' | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')

section "1. /memory BEFORE consolidation"
chat "$TOKEN" "/memory"

section "2. /memory consolidate (the request only publishes a Kafka event)"
start=$(python3 -c 'import time; print(time.time())')
chat "$TOKEN" "/memory consolidate"
python3 -c "import time; print(f'request returned in {time.time() - $start:.2f} s')"

section "3. p17-memory-worker consumes memory.consolidation_requested (model calls run here)"
since=$(date -u +%Y-%m-%dT%H:%M:%SZ)
for _ in $(seq 1 360); do
  status=$(docker exec p17-mongodb mongosh -u p17_admin -p "${P17_MONGO_PASSWORD:-p17_mongo_pass}" --authenticationDatabase admin \
    --quiet p17_handshake --eval 'print((db.student_memory.findOne({_id: db.accounts.findOne({email: "student001@seed.p17.example"})._id}).consolidation || {}).status)')
  [[ $status == done ]] && break
  sleep 5
done
docker logs --since 30m p17-memory-worker 2>&1 | grep -E "received memory|written|committed|attempt|moved" | tail -4
echo "status: $status"

section "4. /memory AFTER consolidation"
chat "$TOKEN" "/memory"

section "5. Checks against the planted duplicates and contradictions"
docker compose --profile seed run --rm --entrypoint python p17-db-seed -m db.seed.check_memory 2>&1 | grep -v "Container \|Network "

section "6. Memory is injected into the prompt: a normal question uses it"
chat "$TOKEN" "Based on what you remember about me, what kind of internships should I look for? Answer in two sentences without searching."
