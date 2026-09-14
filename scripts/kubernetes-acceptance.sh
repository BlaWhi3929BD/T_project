#!/usr/bin/env bash
set -Eeuo pipefail

NAMESPACE="${NAMESPACE:-trades-dashboard}"
TAG="${TAG:-$(git rev-parse --short HEAD)}"
INGRESS_PORT="${INGRESS_PORT:-18080}"
RESET_NAMESPACE="${RESET_NAMESPACE:-false}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCAL_OVERLAY="$ROOT_DIR/k8s/overlays/local/kustomization.yaml"
BACKUP_FILE="$(mktemp)"
PORT_FORWARD_PID=""

cleanup() {
    if [[ -n "$PORT_FORWARD_PID" ]]; then
        kill "$PORT_FORWARD_PID" 2>/dev/null || true
        wait "$PORT_FORWARD_PID" 2>/dev/null || true
    fi
    cp "$BACKUP_FILE" "$LOCAL_OVERLAY"
    rm -f "$BACKUP_FILE"
}
trap cleanup EXIT

require_command() {
    command -v "$1" >/dev/null 2>&1 || {
        printf 'Required command is missing: %s\n' "$1" >&2
        exit 1
    }
}

for command in docker git kubectl minikube curl; do
    require_command "$command"
done

if [[ "$RESET_NAMESPACE" == "true" ]]; then
    kubectl delete namespace "$NAMESPACE" --ignore-not-found --wait=true
fi

if ! minikube status --format='{{.Host}}' 2>/dev/null | grep -qx Running; then
    printf 'minikube is not running. Start it with: minikube start --driver=docker\n' >&2
    exit 1
fi

cp "$LOCAL_OVERLAY" "$BACKUP_FILE"
sed -i -E "s/(newTag: ).*/\\1$TAG/" "$LOCAL_OVERLAY"

docker build --no-cache --tag "trades-backend:$TAG" -f "$ROOT_DIR/solution/backend/Dockerfile" "$ROOT_DIR"
docker build --no-cache --tag "trades-frontend:$TAG" -f "$ROOT_DIR/solution/frontend/Dockerfile" "$ROOT_DIR/solution/frontend"
minikube image load "trades-backend:$TAG"
minikube image load "trades-frontend:$TAG"

kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
database_url="postgresql://trades_user:${POSTGRES_PASSWORD:-acceptance-only-password}@postgres:5432/trades_db"
kubectl -n "$NAMESPACE" create secret generic postgres-secret \
    --from-literal=POSTGRES_DB=trades_db \
    --from-literal=POSTGRES_USER=trades_user \
    --from-literal=POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-acceptance-only-password}" \
    --from-literal=DATABASE_URL="$database_url" \
    --dry-run=client -o yaml | kubectl apply -f -

minikube addons enable ingress
kubectl apply -k "$ROOT_DIR/k8s/"
if ! kubectl wait --for=condition=ready pod --all -n "$NAMESPACE" --timeout=5m; then
    kubectl get pods -n "$NAMESPACE" -o wide
    kubectl get events -n "$NAMESPACE" --sort-by=.lastTimestamp | tail -40
    kubectl logs -n "$NAMESPACE" -l app.kubernetes.io/component=backend --tail=80 || true
    kubectl logs -n "$NAMESPACE" -l app.kubernetes.io/component=frontend --tail=80 || true
    kubectl logs -n "$NAMESPACE" -l app.kubernetes.io/component=database --tail=80 || true
    exit 1
fi

backend_uid="$(kubectl -n "$NAMESPACE" get deployment/backend -o jsonpath='{.spec.template.spec.containers[0].securityContext.runAsUser}')"
backend_readonly="$(kubectl -n "$NAMESPACE" get deployment/backend -o jsonpath='{.spec.template.spec.containers[0].securityContext.readOnlyRootFilesystem}')"
frontend_uid="$(kubectl -n "$NAMESPACE" get deployment/frontend -o jsonpath='{.spec.template.spec.containers[0].securityContext.runAsUser}')"
frontend_readonly="$(kubectl -n "$NAMESPACE" get deployment/frontend -o jsonpath='{.spec.template.spec.containers[0].securityContext.readOnlyRootFilesystem}')"
postgres_uid="$(kubectl -n "$NAMESPACE" get statefulset/postgres -o jsonpath='{.spec.template.spec.securityContext.runAsUser}')"
postgres_readonly="$(kubectl -n "$NAMESPACE" get statefulset/postgres -o jsonpath='{.spec.template.spec.containers[0].securityContext.readOnlyRootFilesystem}')"
test "$backend_uid" != "0" && test "$backend_readonly" = "true"
test "$frontend_uid" != "0" && test "$frontend_readonly" = "true"
test "$postgres_uid" != "0" && test "$postgres_readonly" = "true"

kubectl -n ingress-nginx port-forward service/ingress-nginx-controller "$INGRESS_PORT:80" >/tmp/trades-ingress-port-forward.log 2>&1 &
PORT_FORWARD_PID=$!
for attempt in $(seq 1 30); do
    if curl --silent --fail -H 'Host: trades.local' "http://127.0.0.1:$INGRESS_PORT/health" >/tmp/trades-health.json; then
        break
    fi
    sleep 2
done
curl --silent --fail -H 'Host: trades.local' "http://127.0.0.1:$INGRESS_PORT/" | grep -q '<div id="root">'
curl --silent --fail -H 'Host: trades.local' "http://127.0.0.1:$INGRESS_PORT/ready" | grep -q '"status":"ready"'
curl --silent --fail -H 'Host: trades.local' "http://127.0.0.1:$INGRESS_PORT/api/stats" >/tmp/trades-k8s-stats.json

python3 - <<'PY'
import json
from pathlib import Path

stats = json.loads(Path("/tmp/trades-k8s-stats.json").read_text())
assert stats["trades_count"] == 100000
assert stats["net_pnl"] == "20373.96"
PY

backend_pod="$(kubectl -n "$NAMESPACE" get pod -l app.kubernetes.io/component=backend -o jsonpath='{.items[0].metadata.name}')"
kubectl -n "$NAMESPACE" delete pod "$backend_pod" --wait=true
kubectl -n "$NAMESPACE" wait --for=condition=ready pod -l app.kubernetes.io/component=backend --timeout=15m
curl --silent --fail -H 'Host: trades.local' "http://127.0.0.1:$INGRESS_PORT/api/stats" >/tmp/trades-k8s-backend-recovery.json

postgres_pod="$(kubectl -n "$NAMESPACE" get pod -l app.kubernetes.io/component=database -o jsonpath='{.items[0].metadata.name}')"
kubectl -n "$NAMESPACE" delete pod "$postgres_pod" --wait=true
kubectl -n "$NAMESPACE" wait --for=condition=ready pod -l app.kubernetes.io/component=database --timeout=15m
kubectl -n "$NAMESPACE" wait --for=condition=ready pod -l app.kubernetes.io/component=backend --timeout=15m
curl --silent --fail -H 'Host: trades.local' "http://127.0.0.1:$INGRESS_PORT/api/stats" >/tmp/trades-k8s-postgres-recovery.json

python3 - <<'PY'
import json
from pathlib import Path

for path in (
    "/tmp/trades-k8s-backend-recovery.json",
    "/tmp/trades-k8s-postgres-recovery.json",
):
    stats = json.loads(Path(path).read_text())
    assert stats["trades_count"] == 100000
    assert stats["net_pnl"] == "20373.96"
PY

printf 'Kubernetes acceptance passed for tag %s\n' "$TAG"
