#!/usr/bin/env bash
# Evidence that the platform runs on MongoDB: collections, sample documents, bcrypt,
# server-side sessions with expiry, logout revocation, saved items, and the activity log.
#
#   scripts/mongo_demo.sh
set -uo pipefail
cd "$(dirname "$0")/.."
WEB=${WEB:-http://localhost:9170}
MONGO_PW=${P17_MONGO_PASSWORD:-p17_mongo_pass}
mongo() { docker exec p17-mongodb mongosh -u p17_admin -p "$MONGO_PW" --authenticationDatabase admin --quiet p17_handshake --eval "$1"; }
section() { printf '\n== %s\n' "$*"; }

section "1. Collections and document counts (MongoDB is the system of record)"
mongo '
for (const c of ["accounts","students","companies","company_members","preferences","sessions","jobs","applications",
                 "events","registrations","saved_items","message_threads","messages","activity_logs",
                 "assistant_rules","student_memory","conversations","counters"])
  print(c.padEnd(18), String(db[c].countDocuments({})).padStart(6));'

section "2. Student account + profile (bcrypt hash, integer _id kept from MySQL)"
mongo '
const a = db.accounts.findOne({email: "student001@seed.p17.example"});
print(EJSON.stringify({_id: a._id, email: a.email, role: a.role, password_hash: a.password_hash.slice(0, 7) + "...(bcrypt, 60 chars)"}));
print(EJSON.stringify(db.students.findOne({_id: a._id}, {name: 1, college_name: 1, major: 1, city: 1, cgpa: 1, date_of_birth: 1})));'

section "3. Job posting and application with resume metadata"
mongo '
print(EJSON.stringify(db.jobs.findOne({}, {title: 1, company_id: 1, company_name: 1, salary: 1, posting_date: 1, deadline: 1})));
print(EJSON.stringify(db.applications.findOne({"resume.sha256": {$ne: null}}, {student_id: 1, job_id: 1, company_id: 1, status: 1, resume: 1})
      || db.applications.findOne({}, {student_id: 1, job_id: 1, status: 1, resume: 1})));'

section "4. Event and registration"
mongo '
print(EJSON.stringify(db.events.findOne({}, {name: 1, event_date: 1, event_time: 1, eligibility: 1, company_name: 1})));
print(EJSON.stringify(db.registrations.findOne({}, {student_id: 1, event_id: 1, company_id: 1, registered_at: 1})));'

section "5. Secure sessions: login creates a session, logout revokes it"
TOKEN=$(curl -s -X POST "$WEB/api/auth/login" -H 'Content-Type: application/json' \
  -d '{"email":"student001@seed.p17.example","password":"SeedPass17!"}' | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')
printf 'JWT claims: '; python3 -c "import base64,json,sys; p=sys.argv[1].split('.')[1]; p+='='*(-len(p)%4); c=json.loads(base64.urlsafe_b64decode(p)); c['sid']=c['sid'][:8]+'...'; print(c)" "$TOKEN"
mongo '
const s = db.sessions.find({account_id: db.accounts.findOne({email: "student001@seed.p17.example"})._id}).sort({created_at: -1}).limit(1).next();
print("stored session:", EJSON.stringify({_id: s._id.slice(0, 16) + "... (SHA-256 of sid)", expires_at: s.expires_at, revoked_at: s.revoked_at}));
print("TTL index:", EJSON.stringify(db.sessions.getIndexes().find(i => i.expireAfterSeconds === 0)));'
printf 'GET /api/students/me with the token          -> HTTP %s\n' "$(curl -s -o /dev/null -w '%{http_code}' "$WEB/api/students/me" -H "Authorization: Bearer $TOKEN")"
printf 'POST /api/auth/logout                         -> HTTP %s\n' "$(curl -s -o /dev/null -w '%{http_code}' -X POST "$WEB/api/auth/logout" -H "Authorization: Bearer $TOKEN")"
printf 'GET /api/students/me with the same token     -> HTTP %s  ' "$(curl -s -o /tmp/p17-me.json -w '%{http_code}' "$WEB/api/students/me" -H "Authorization: Bearer $TOKEN")"; cat /tmp/p17-me.json; echo

section "6. Saved jobs/events and preferences"
TOKEN=$(curl -s -X POST "$WEB/api/auth/login" -H 'Content-Type: application/json' \
  -d '{"email":"student002@seed.p17.example","password":"SeedPass17!"}' | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')
curl -s -o /dev/null -X PUT "$WEB/api/student/preferences" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"preferred_categories":"internship","preferred_cities":"Palo Alto","min_salary":45000,"preferred_skills":"Python","remote_ok":true}'
docker exec p17-assistant-service python -c "
from app.assistant.tools.save_job_or_event import save_job_or_event
from app.assistant.tools.schemas import AssistantContext
from app.mongo import get_database
db = get_database(); sid = db.accounts.find_one({'email': 'student002@seed.p17.example'})['_id']
job = db.jobs.find_one({'deadline': {'\$gte': '2026-11-14'}}, {'_id': 1})['_id']
print('save tool:', save_job_or_event(AssistantContext(account_id=sid, role='student', db=db), {'item_type': 'job', 'item_id': job}))"
mongo '
const id = db.accounts.findOne({email: "student002@seed.p17.example"})._id;
print(EJSON.stringify(db.preferences.findOne({_id: id})));
db.saved_items.find({student_id: id}).forEach(d => print(EJSON.stringify(d)));'

section "7. Activity log (latest 8)"
mongo 'db.activity_logs.find({}, {_id: 0, account_id: 1, action: 1, entity_type: 1, entity_id: 1, at: 1}).sort({at: -1}).limit(8).forEach(d => print(EJSON.stringify(d)))'
