#!/usr/bin/env bash
# Kafka pipeline demonstrations for the Pair 17 Handshake platform (Docker Compose stack).
#
#   scripts/kafka_demos.sh            # all: API happy path + failure cases 1-3
#   scripts/kafka_demos.sh 0|1|2|3    # one case
#
# 0. Happy path: real API calls publish every topic; the workers write MongoDB.
# 1. The same event published twice with the same key -> stored once (idempotent consumer).
# 2. Worker killed after its MongoDB write but before committing the offset -> redelivered on
#    restart, skipped as a duplicate; nothing lost, nothing doubled.
# 3. Poison message -> 3 bounded attempts -> <topic>.dlq; the next message on the same
#    partition is still processed.
#
# Requires the stack running and seeded (README), curl, python3.
set -uo pipefail
cd "$(dirname "$0")/.."

WEB=${WEB:-http://localhost:9170}
MONGO_PW=${P17_MONGO_PASSWORD:-p17_mongo_pass}
RUN=$(date +%s)  # makes demo ids unique per run

banner() { printf '\n==================================================================\n%s\n==================================================================\n' "$*"; }
step() { printf '\n--- %s\n' "$*"; }
show() { printf '$ %s\n' "$*"; eval "$@"; }
json() { python3 -c "import json,sys; d=json.load(sys.stdin); print($1)"; }
mongo() { docker exec p17-mongodb mongosh -u p17_admin -p "$MONGO_PW" --authenticationDatabase admin --quiet p17_handshake --eval "$1"; }
produce() {  # produce TOPIC KEY VALUE
  printf '%s|%s\n' "$2" "$3" | docker exec -i p17-kafka /opt/kafka/bin/kafka-console-producer.sh \
    --bootstrap-server localhost:9092 --topic "$1" --property parse.key=true --property 'key.separator=|'
}
group() { docker exec p17-kafka /opt/kafka/bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
  --describe --group "$1" 2>/dev/null | awk '/TOPIC|application|event\.|job\./ {print $2, $3, $4, $5, $6}' | column -t; }
worker_logs() { docker logs --since "$2" "$1" 2>&1 | sed -E 's/^[0-9-]+ ([0-9:]+),[0-9]+ /\1 /'; }
wait_for_log() {  # wait_for_log CONTAINER SINCE PATTERN TIMEOUT
  for _ in $(seq 1 "$4"); do worker_logs "$1" "$2" | grep -q "$3" && return 0; sleep 1; done
  echo "(timed out waiting for '$3' in $1)"; return 1
}
envelope() {  # envelope EVENT_ID TYPE KEY DATA_JSON
  printf '{"event_id":"%s","event_type":"%s","schema_version":1,"occurred_at":"%s","source":"demo-script","key":"%s","data":%s}' \
    "$1" "$2" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$3" "$4"
}

case_0() {
  banner "Case 0: API calls publish events; workers project them into MongoDB"
  local since; since=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  local ctok stok
  ctok=$(curl -s -X POST "$WEB/api/auth/login" -H 'Content-Type: application/json' \
    -d '{"email":"company001@seed.p17.example","password":"SeedPass17!"}' | json "d['access_token']")
  stok=$(curl -s -X POST "$WEB/api/auth/login" -H 'Content-Type: application/json' \
    -d '{"email":"student001@seed.p17.example","password":"SeedPass17!"}' | json "d['access_token']")

  step "Company creates a job (job service -> job.created)"
  JOB_ID=$(curl -s -X POST "$WEB/api/jobs" -H "Authorization: Bearer $ctok" -H 'Content-Type: application/json' \
    -d "{\"title\":\"Kafka Pipeline Intern $RUN\",\"category\":\"internship\",\"city\":\"Palo Alto\",\"skills_required\":\"Python, Kafka\",\"deadline\":\"2027-03-01\",\"salary\":45000}" \
    | json "d['id']")
  echo "POST /api/jobs -> job_id=$JOB_ID"

  step "Student applies (application service -> application.created)"
  printf '%%PDF-1.4\n%% demo resume\n' > /tmp/p17-demo-resume.pdf
  APP_ID=$(curl -s -X POST "$WEB/api/student/jobs/$JOB_ID/apply" -H "Authorization: Bearer $stok" \
    -F "resume=@/tmp/p17-demo-resume.pdf;type=application/pdf" | json "d['id']")
  echo "POST /api/student/jobs/$JOB_ID/apply -> application_id=$APP_ID"

  step "Company marks it Reviewed (application service -> application.updated + application.status_changed)"
  curl -s -X PATCH "$WEB/api/applications/$APP_ID/status" -H "Authorization: Bearer $ctok" \
    -H 'Content-Type: application/json' -d '{"status":"Reviewed"}' | json "f\"PATCH status -> {d['status']}\""

  step "Student registers for an event (event service -> event.registration_created)"
  REG_EVENT=""
  for eid in $(curl -s "$WEB/api/student/events?limit=100" -H "Authorization: Bearer $stok" \
      | json "' '.join(str(e['id']) for e in (d['items'] if isinstance(d, dict) else d) if not e.get('is_registered'))"); do
    code=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$WEB/api/student/events/$eid/register" -H "Authorization: Bearer $stok")
    if [[ $code == 201 ]]; then REG_EVENT=$eid; break; fi
  done
  echo "POST /api/student/events/$REG_EVENT/register -> 201"

  sleep 4
  step "Producer log lines (API services)"
  for s in job application event; do docker logs --since "$since" "p17-$s-service" 2>&1 | grep "published" | sed -E 's/^[0-9-]+ ([0-9:]+),[0-9]+ /\1 /'; done
  step "Worker log lines"
  for w in job application event; do worker_logs "p17-$w-worker" "$since" | grep -E "received|written|committed"; done
  step "MongoDB projections written by the workers"
  mongo "
    const j = db.job_search_index.findOne({_id: $JOB_ID}, {title: 1, city: 1, skills: 1, source_event_id: 1});
    print('job_search_index      ', EJSON.stringify(j));
    db.application_events.find({application_id: $APP_ID}, {event_type: 1}).sort({occurred_at: 1})
      .forEach(d => print('application_events    ', EJSON.stringify(d)));
    db.notifications.find({application_id: $APP_ID}, {message: 1}).forEach(d => print('notifications         ', EJSON.stringify(d)));
    print('event_stats           ', EJSON.stringify(db.event_stats.findOne({_id: ${REG_EVENT:-0}})));"
}

case_1() {
  banner "Case 1: the same event published twice with the same key -> stored once"
  local since eid key data
  since=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  eid="demo-dup-$RUN"; key="99$((RUN % 10000))1"
  data="{\"application_id\":$key,\"job_id\":1,\"student_id\":1,\"company_id\":1,\"status\":\"Pending\"}"
  local value; value=$(envelope "$eid" application.created "$key" "$data")
  step "Publish the identical message twice (topic application.created, key $key, event_id $eid)"
  produce application.created "$key" "$value"; produce application.created "$key" "$value"
  echo "published 2 messages"
  wait_for_log p17-application-worker "$since" "already applied" 30
  step "Application worker log"
  worker_logs p17-application-worker "$since"
  step "MongoDB: documents for this event_id (expect 1)"
  mongo "print('application_events count for $eid =', db.application_events.countDocuments({_id: '$eid'}))"
  step "Consumer group p17-application-worker (LAG 0 = both offsets committed)"
  group p17-application-worker
}

case_2() {
  banner "Case 2: kill the worker after its MongoDB write, before the offset commit"
  local since eid key data value
  step "Restart the application worker with a 30 s pause between the write and the commit"
  P17_WORKER_PAUSE_AFTER_WRITE_SECONDS=30 docker compose up -d --no-deps --wait p17-application-worker 2>&1 | tail -1
  since=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  wait_for_log p17-application-worker "1970-01-01T00:00:00Z" "subscribed" 30 >/dev/null
  sleep 5
  eid="demo-crash-$RUN"; key="99$((RUN % 10000))2"
  data="{\"application_id\":$key,\"job_id\":1,\"student_id\":1,\"company_id\":1,\"status\":\"Pending\"}"
  value=$(envelope "$eid" application.created "$key" "$data")
  step "Publish one event (key $key, event_id $eid)"
  produce application.created "$key" "$value"; echo "published"
  wait_for_log p17-application-worker "$since" "DEMO: write done" 90
  step "Worker log up to the kill"
  worker_logs p17-application-worker "$since"
  step "SIGKILL the worker mid-processing"
  show docker kill p17-application-worker
  step "State while the worker is dead"
  mongo "print('application_events count for $eid =', db.application_events.countDocuments({_id: '$eid'}), '(the write happened)')"
  echo "Consumer group (LAG 1 on this partition = offset NOT committed):"
  group p17-application-worker
  step "Restart the worker normally (no pause)"
  since=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  P17_WORKER_PAUSE_AFTER_WRITE_SECONDS=0 docker compose up -d --no-deps --wait p17-application-worker 2>&1 | tail -1
  wait_for_log p17-application-worker "$since" "$eid" 120
  sleep 2
  step "Worker log after restart (the same offset is redelivered)"
  worker_logs p17-application-worker "$since"
  step "Final state"
  mongo "print('application_events count for $eid =', db.application_events.countDocuments({_id: '$eid'}), '(still 1: reprocessed, not duplicated)')"
  group p17-application-worker
}

case_3() {
  banner "Case 3: poison message -> bounded retries -> dead-letter topic -> pipeline continues"
  local since key eid data good
  since=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  key="99$((RUN % 10000))3"; eid="demo-after-poison-$RUN"
  step "Publish a poison message, then a valid one with the SAME key (same partition, right behind it)"
  produce application.status_changed "$key" 'this is not json {'
  data="{\"application_id\":$key,\"job_id\":1,\"student_id\":1,\"company_id\":1,\"old_status\":\"Pending\",\"new_status\":\"Declined\"}"
  good=$(envelope "$eid" application.status_changed "$key" "$data")
  produce application.status_changed "$key" "$good"
  echo "published poison + valid message"
  wait_for_log p17-application-worker "$since" "$eid written" 60
  step "Application worker log"
  worker_logs p17-application-worker "$since"
  step "Dead-letter topic application.status_changed.dlq (headers carry the failure)"
  docker exec p17-kafka /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 \
    --topic application.status_changed.dlq --from-beginning --timeout-ms 8000 \
    --property print.key=true --property print.headers=true 2>/dev/null | grep "$key"
  step "MongoDB: the valid message after the poison was processed"
  mongo "print(EJSON.stringify(db.notifications.findOne({_id: '$eid'}, {message: 1})))"
  group p17-application-worker
}

cases=${1:-0 1 2 3}
for c in $cases; do "case_$c"; done
