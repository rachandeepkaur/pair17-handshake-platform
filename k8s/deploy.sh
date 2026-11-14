#!/usr/bin/env bash
# Deploys the Pair 17 Handshake platform to the current kubectl context.
#
#   k8s/deploy.sh            # create secrets (first run), apply manifests, wait for rollout
#   k8s/deploy.sh --seed     # also run the demo-data seed Job
#
# Secrets never live in committed manifests: they are read from k8s/secrets.env
# (git-ignored). On first run that file is generated with random values.
set -euo pipefail
cd "$(dirname "$0")/.."

NS=p17-handshake
SECRETS_FILE=k8s/secrets.env

if [[ ! -f $SECRETS_FILE ]]; then
  umask 077
  {
    echo "MYSQL_ROOT_PASSWORD=$(openssl rand -hex 16)"
    echo "DB_PASSWORD=$(openssl rand -hex 16)"
    echo "MONGO_PASSWORD=$(openssl rand -hex 16)"
    echo "JWT_SECRET=$(openssl rand -hex 32)"
  } > "$SECRETS_FILE"
  echo "Generated $SECRETS_FILE with random values (git-ignored)."
fi

kubectl apply -f k8s/base/namespace.yaml

# Created imperatively (dry-run | apply keeps it idempotent) so no value lands in git.
kubectl -n "$NS" create secret generic p17-handshake-secrets \
  --from-env-file="$SECRETS_FILE" --dry-run=client -o yaml | kubectl apply -f -

# kustomize cannot read files outside k8s/, so the schema ConfigMap is built here.
kubectl -n "$NS" create configmap p17-mysql-init \
  --from-file=01-schema.sql=backend/db/schema.sql --dry-run=client -o yaml | kubectl apply -f -

kubectl apply -k k8s/base

echo "Waiting for data stores..."
for sts in p17-mysql p17-mongodb p17-kafka; do
  kubectl -n "$NS" rollout status "statefulset/$sts" --timeout=300s
done
kubectl -n "$NS" wait --for=condition=complete job/p17-kafka-topics --timeout=300s
echo "Waiting for services and workers..."
for deploy in p17-student-service p17-company-service p17-job-service p17-application-service \
              p17-event-service p17-assistant-service p17-frontend \
              p17-application-worker p17-event-worker p17-job-worker; do
  kubectl -n "$NS" rollout status "deployment/$deploy" --timeout=300s
done

if [[ ${1:-} == --seed ]]; then
  kubectl -n "$NS" delete job p17-db-seed --ignore-not-found
  kubectl apply -f k8s/jobs/p17-db-seed.yaml
  kubectl -n "$NS" wait --for=condition=complete job/p17-db-seed --timeout=300s
  kubectl -n "$NS" logs job/p17-db-seed | tail -8
fi

kubectl -n "$NS" get pods,svc,hpa
