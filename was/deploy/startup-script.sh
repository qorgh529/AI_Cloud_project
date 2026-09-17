#!/usr/bin/env bash
# GCE instance-template startup-script for the WAS Managed Instance Group.
#
# Responsibilities:
#   1. Install a JRE.
#   2. Fetch the PetClinic REST jar (from the artifact bucket built by CI).
#   3. Pull DB credentials out of Secret Manager and materialize them as an
#      env file for systemd (never baked into the image or committed to git).
#   4. Install/refresh the systemd unit and (re)start the service.
#
# Expected instance metadata (set on the instance template):
#   artifact-bucket   gs://<bucket>/petclinic/app.jar path, e.g. gs://nova-petclinic-artifacts/was/app.jar
#   db-secret-name    Secret Manager secret name holding DB connection JSON, e.g. petclinic-db-credentials
#   gcp-project-id    Project ID to read the secret from (defaults to the instance's own project)
#
# The DB secret is expected to be a small JSON blob:
#   {"url": "jdbc:mysql://<CLOUD_SQL_PRIVATE_IP>:3306/petclinic", "username": "petclinic", "password": "..."}
set -euo pipefail

log() { echo "[startup-script] $*"; }

PROJECT_ID="$(curl -sf -H 'Metadata-Flavor: Google' \
  'http://metadata.google.internal/computeMetadata/v1/project/project-id')"
ARTIFACT_BUCKET_PATH="$(curl -sf -H 'Metadata-Flavor: Google' \
  'http://metadata.google.internal/computeMetadata/v1/instance/attributes/artifact-bucket')"
DB_SECRET_NAME="$(curl -sf -H 'Metadata-Flavor: Google' \
  'http://metadata.google.internal/computeMetadata/v1/instance/attributes/db-secret-name')"

log "project=${PROJECT_ID} artifact=${ARTIFACT_BUCKET_PATH} secret=${DB_SECRET_NAME}"

# --- 1. Runtime ---------------------------------------------------------
if ! command -v java >/dev/null 2>&1; then
  log "installing OpenJDK 21"
  apt-get update -y
  apt-get install -y openjdk-21-jre-headless
fi

id -u petclinic >/dev/null 2>&1 || useradd --system --no-create-home --shell /usr/sbin/nologin petclinic

mkdir -p /opt/petclinic /etc/petclinic

# --- 2. Application artifact --------------------------------------------
log "fetching application jar from ${ARTIFACT_BUCKET_PATH}"
gsutil cp "${ARTIFACT_BUCKET_PATH}" /opt/petclinic/app.jar
chown -R petclinic:petclinic /opt/petclinic

# --- 3. DB credentials from Secret Manager ------------------------------
log "reading DB credentials from Secret Manager secret ${DB_SECRET_NAME}"
DB_SECRET_JSON="$(gcloud secrets versions access latest \
  --secret="${DB_SECRET_NAME}" --project="${PROJECT_ID}")"

DB_URL="$(echo "${DB_SECRET_JSON}" | python3 -c 'import json,sys; print(json.load(sys.stdin)["url"])')"
DB_USER="$(echo "${DB_SECRET_JSON}" | python3 -c 'import json,sys; print(json.load(sys.stdin)["username"])')"
DB_PASS="$(echo "${DB_SECRET_JSON}" | python3 -c 'import json,sys; print(json.load(sys.stdin)["password"])')"

cat > /etc/petclinic/petclinic.env <<EOF
SPRING_PROFILES_ACTIVE=mysql,spring-data-jpa
MYSQL_URL=${DB_URL}
MYSQL_USER=${DB_USER}
MYSQL_PASS=${DB_PASS}
PETCLINIC_SECURITY_ENABLE=true
EOF
chmod 600 /etc/petclinic/petclinic.env
chown petclinic:petclinic /etc/petclinic/petclinic.env

# --- 4. systemd unit -----------------------------------------------------
# petclinic.service is baked into the instance image alongside this script;
# if it ever needs to be fetched instead, pull it from the same artifact
# bucket next to app.jar.
if [ ! -f /etc/systemd/system/petclinic.service ]; then
  log "petclinic.service unit not found on image — see was/deploy/petclinic.service in the repo"
  exit 1
fi

systemctl daemon-reload
systemctl enable petclinic.service
systemctl restart petclinic.service

log "done"
