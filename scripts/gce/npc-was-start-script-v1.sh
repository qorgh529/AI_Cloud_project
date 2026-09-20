#!/usr/bin/env bash
# =============================================================================
# npc-was-start-script-v1.sh — GCE 인스턴스 startup-script (단일 파일 버전)
#
# - 대상 이미지: Rocky Linux 9, Tomcat9 + JDK17 사전 설치
# - 동작 순서
#   1) GCS 버킷(gs://npc-bucket-nova/releases/petclinic.war)에서 war를 내려받아
#      Tomcat webapps에 직접 배포
#   2) Cloud SQL(MySQL) 연결 설정 및 PetClinic 스키마/초기데이터 적재
#   3) Tomcat 재시작
#
# 이 파일 전체를 인스턴스 메타데이터의 "startup-script"(또는
# startup-script-url이 가리키는 파일)로 등록해서 사용한다.
# war 배포용 별도 파일을 만들지 않고 이 스크립트 안에서 바로 처리한다.
# =============================================================================

set -Eeuo pipefail

trap 'echo "[startup][ERROR] line=${LINENO}, command=${BASH_COMMAND}" >&2' ERR
exec > >(tee -a /var/log/startup-script.log) 2>&1

echo "[startup] $(date -Iseconds) 시작"

# =============================================================================
# 1. GCS 버킷에서 petclinic.war 다운로드 및 배포
# =============================================================================

WAR_BUCKET_URI="gs://npc-bucket-nova/releases/petclinic.war"
APP_NAME="petclinic"

TOMCAT_HOME="/opt/tomcat"
WEBAPPS_DIR="${TOMCAT_HOME}/webapps"
WAR_FILE="${WEBAPPS_DIR}/${APP_NAME}.war"
APP_DIR="${WEBAPPS_DIR}/${APP_NAME}"

TOMCAT_USER="tomcat"
TOMCAT_GROUP="tomcat"

if command -v gcloud >/dev/null 2>&1; then
    GCS_COPY_CMD=(gcloud storage cp)
elif command -v gsutil >/dev/null 2>&1; then
    GCS_COPY_CMD=(gsutil cp)
else
    echo "[startup][ERROR] gcloud 또는 gsutil을 찾을 수 없습니다." >&2
    exit 1
fi

WAR_DOWNLOAD_TMP="$(mktemp /tmp/petclinic.XXXXXX.war)"

echo "[startup] ${WAR_BUCKET_URI} 다운로드 시작"

if ! "${GCS_COPY_CMD[@]}" "${WAR_BUCKET_URI}" "${WAR_DOWNLOAD_TMP}"; then
    echo "[startup][ERROR] war 다운로드 실패: ${WAR_BUCKET_URI}" >&2
    rm -f "${WAR_DOWNLOAD_TMP}"
    exit 1
fi

if [ ! -s "${WAR_DOWNLOAD_TMP}" ]; then
    echo "[startup][ERROR] 다운로드된 war 파일이 비어 있습니다." >&2
    rm -f "${WAR_DOWNLOAD_TMP}"
    exit 1
fi

echo "[startup] 다운로드 완료: $(du -h "${WAR_DOWNLOAD_TMP}" | cut -f1)"

if systemctl list-unit-files --type=service | grep -q '^tomcat.service'; then
    if systemctl is-active --quiet tomcat; then
        echo "[startup] 배포 전 Tomcat 중지"
        systemctl stop tomcat
    fi
fi

mkdir -p "${WEBAPPS_DIR}"

echo "[startup] 기존 배포본 정리: ${WAR_FILE}, ${APP_DIR}"
rm -f "${WAR_FILE}"
rm -rf "${APP_DIR}"

echo "[startup] 신규 war 배치: ${WAR_FILE}"
mv "${WAR_DOWNLOAD_TMP}" "${WAR_FILE}"
chown "${TOMCAT_USER}:${TOMCAT_GROUP}" "${WAR_FILE}"
chmod 640 "${WAR_FILE}"

echo "[startup] war 압축 해제: ${APP_DIR}"
mkdir -p "${APP_DIR}"

if command -v unzip >/dev/null 2>&1; then
    unzip -q "${WAR_FILE}" -d "${APP_DIR}"
else
    echo "[startup] unzip 미설치, jar 명령으로 압축 해제"
    ( cd "${APP_DIR}" && jar -xf "${WAR_FILE}" )
fi

chown -R "${TOMCAT_USER}:${TOMCAT_GROUP}" "${APP_DIR}"

echo "[startup] war 배포 완료"

# =============================================================================
# 2. Cloud SQL(MySQL) 연결 설정
# =============================================================================

DB_PRIVATE_IP="192.168.32.14"
DB_PORT="3306"
DB_NAME="petclinic"
DB_USER="petclinic"

# Secret Manager에 저장된 DB 비밀번호 Secret 이름
DB_SECRET_NAME="petclinic-db-password"

if [ -z "${DB_PRIVATE_IP}" ]; then
    echo "[startup][ERROR] DB_PRIVATE_IP가 설정되지 않았습니다." >&2
    exit 1
fi

echo "[startup] Secret Manager에서 DB 비밀번호 조회"

METADATA_URL="http://metadata.google.internal/computeMetadata/v1"
METADATA_HEADER="Metadata-Flavor: Google"

PROJECT_ID="$(curl -fsS \
    -H "${METADATA_HEADER}" \
    "${METADATA_URL}/project/project-id")"

ACCESS_TOKEN="$(curl -fsS \
    -H "${METADATA_HEADER}" \
    "${METADATA_URL}/instance/service-accounts/default/token" \
    | python3 -c '
import json
import sys
print(json.load(sys.stdin)["access_token"])
')"

SECRET_RESPONSE="$(curl -fsS \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    "https://secretmanager.googleapis.com/v1/projects/${PROJECT_ID}/secrets/${DB_SECRET_NAME}/versions/latest:access")"

DB_PASSWORD="$(printf '%s' "${SECRET_RESPONSE}" \
    | python3 -c '
import base64
import json
import sys

response = json.load(sys.stdin)
encoded = response["payload"]["data"]
print(base64.b64decode(encoded).decode("utf-8"), end="")
')"

if [ -z "${DB_PASSWORD}" ]; then
    echo "[startup][ERROR] Secret Manager에서 DB 비밀번호를 가져오지 못했습니다." >&2
    exit 1
fi

echo "[startup] DB Secret 조회 성공"

MYSQL_URL="jdbc:mysql://${DB_PRIVATE_IP}:${DB_PORT}/${DB_NAME}"
MYSQL_USER="${DB_USER}"
MYSQL_PASS="${DB_PASSWORD}"

{
    echo '#!/usr/bin/env bash'
    printf 'export MYSQL_URL=%q\n' "${MYSQL_URL}"
    printf 'export MYSQL_USER=%q\n' "${MYSQL_USER}"
    printf 'export MYSQL_PASS=%q\n' "${MYSQL_PASS}"
} > /opt/tomcat/bin/setenv.sh

chown tomcat:tomcat /opt/tomcat/bin/setenv.sh
chmod 600 /opt/tomcat/bin/setenv.sh

echo "[startup] MYSQL_URL=${MYSQL_URL}"
echo "[startup] MYSQL_USER=${MYSQL_USER}"
echo "[startup] DB Password는 로그에 출력하지 않습니다."

echo "[startup] Cloud SQL 연결 확인"

if timeout 5 bash -c "</dev/tcp/${DB_PRIVATE_IP}/${DB_PORT}"; then
    echo "[startup] Cloud SQL ${DB_PRIVATE_IP}:${DB_PORT} TCP 연결 성공"
else
    echo "[startup][ERROR] Cloud SQL ${DB_PRIVATE_IP}:${DB_PORT} TCP 연결 실패" >&2
    exit 1
fi

if ! command -v mysql >/dev/null 2>&1; then
    echo "[startup] MySQL 클라이언트 설치"
    dnf -y install mysql
fi

echo "[startup] Cloud SQL 사용자 인증 및 DB 접속 확인"

MYSQL_PWD="${DB_PASSWORD}" mysql \
    --connect-timeout=5 \
    --host="${DB_PRIVATE_IP}" \
    --port="${DB_PORT}" \
    --user="${DB_USER}" \
    --database="${DB_NAME}" \
    --execute="
        SELECT
            DATABASE() AS database_name,
            CURRENT_USER() AS authenticated_user;
    "

echo "[startup] Cloud SQL 로그인 성공"

TABLE_COUNT="$(MYSQL_PWD="${DB_PASSWORD}" mysql \
    --batch \
    --skip-column-names \
    --host="${DB_PRIVATE_IP}" \
    --port="${DB_PORT}" \
    --user="${DB_USER}" \
    --database="${DB_NAME}" \
    --execute="
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema='${DB_NAME}';
    ")"

echo "[startup] ${DB_NAME} 데이터베이스 현재 테이블 수: ${TABLE_COUNT}"

# =============================================================================
# 3. PetClinic 스키마 및 초기 데이터 구성
#    (war 압축 해제가 위 1단계에서 완료되어 있어야 함)
# =============================================================================

SCHEMA_FILE="/opt/tomcat/webapps/petclinic/WEB-INF/classes/db/mysql/schema.sql"
DATA_FILE="/opt/tomcat/webapps/petclinic/WEB-INF/classes/db/mysql/data.sql"

if [ "${TABLE_COUNT}" -eq 0 ]; then
    echo "[startup] 테이블이 없어 PetClinic DB 초기화를 시작합니다."

    if [ ! -f "${SCHEMA_FILE}" ]; then
        echo "[startup][ERROR] schema.sql을 찾을 수 없습니다: ${SCHEMA_FILE}" >&2
        exit 1
    fi

    if [ ! -f "${DATA_FILE}" ]; then
        echo "[startup][ERROR] data.sql을 찾을 수 없습니다: ${DATA_FILE}" >&2
        exit 1
    fi

    echo "[startup] PetClinic 테이블 생성"

    MYSQL_PWD="${DB_PASSWORD}" mysql \
        --host="${DB_PRIVATE_IP}" \
        --port="${DB_PORT}" \
        --user="${DB_USER}" \
        --database="${DB_NAME}" \
        < "${SCHEMA_FILE}"

    echo "[startup] PetClinic 초기 데이터 입력"

    MYSQL_PWD="${DB_PASSWORD}" mysql \
        --host="${DB_PRIVATE_IP}" \
        --port="${DB_PORT}" \
        --user="${DB_USER}" \
        --database="${DB_NAME}" \
        < "${DATA_FILE}"

    echo "[startup] PetClinic DB 초기화 완료"
else
    echo "[startup] 기존 테이블이 존재하므로 스키마 초기화를 건너뜁니다."
fi

echo "[startup] 최종 테이블 목록"

MYSQL_PWD="${DB_PASSWORD}" mysql \
    --host="${DB_PRIVATE_IP}" \
    --port="${DB_PORT}" \
    --user="${DB_USER}" \
    --database="${DB_NAME}" \
    --execute="SHOW TABLES;"

# =============================================================================
# 4. Tomcat (재)시작
# =============================================================================

if systemctl list-unit-files --type=service | grep -q '^tomcat.service'; then
    echo "[startup] war 배포 및 DB 설정 반영을 위해 Tomcat 시작"

    systemctl enable tomcat
    systemctl restart tomcat

    if systemctl is-active --quiet tomcat; then
        echo "[startup] Tomcat 정상 실행 확인"
    else
        echo "[startup][ERROR] Tomcat 실행 실패" >&2
        systemctl status tomcat --no-pager || true
        exit 1
    fi
else
    echo "[startup][ERROR] tomcat.service를 찾을 수 없습니다." >&2
    exit 1
fi

# =============================================================================
# 5. 완료
# =============================================================================

unset DB_PASSWORD MYSQL_PASS ACCESS_TOKEN SECRET_RESPONSE

echo "[startup] $(date -Iseconds) 전체 배포/DB 설정 완료"
