#!/usr/bin/env bash
# =============================================================================
# GCS 버킷의 petclinic.war를 내려받아 Tomcat9에 배포하는 스크립트
#
# - 실행 대상: Rocky Linux 9 / Tomcat9 + JDK17 사전 설치된 이미지
# - 이 파일은 startup-script.sh 에서 별도 파일로 생성/호출된다.
#   (독립 실행도 가능: sudo bash deploy-petclinic-war.sh)
# =============================================================================

set -Eeuo pipefail

trap 'echo "[war-deploy][ERROR] line=${LINENO}, command=${BASH_COMMAND}" >&2' ERR
exec > >(tee -a /var/log/war-deploy.log) 2>&1

echo "[war-deploy] $(date -Iseconds) 시작"

# =============================================================================
# 1. 설정값
# =============================================================================

WAR_BUCKET_URI="gs://npc-bucket-nova/releases/petclinic.war"
APP_NAME="petclinic"

TOMCAT_HOME="/opt/tomcat"
WEBAPPS_DIR="${TOMCAT_HOME}/webapps"
WAR_FILE="${WEBAPPS_DIR}/${APP_NAME}.war"
APP_DIR="${WEBAPPS_DIR}/${APP_NAME}"

TOMCAT_USER="tomcat"
TOMCAT_GROUP="tomcat"

DOWNLOAD_TMP="$(mktemp /tmp/petclinic.XXXXXX.war)"

# =============================================================================
# 2. gcloud / gsutil 확인
# =============================================================================

if command -v gcloud >/dev/null 2>&1; then
    GCS_COPY_CMD=(gcloud storage cp)
elif command -v gsutil >/dev/null 2>&1; then
    GCS_COPY_CMD=(gsutil cp)
else
    echo "[war-deploy][ERROR] gcloud 또는 gsutil을 찾을 수 없습니다." >&2
    exit 1
fi

# =============================================================================
# 3. GCS 버킷에서 war 다운로드
# =============================================================================

echo "[war-deploy] ${WAR_BUCKET_URI} 다운로드 시작"

if ! "${GCS_COPY_CMD[@]}" "${WAR_BUCKET_URI}" "${DOWNLOAD_TMP}"; then
    echo "[war-deploy][ERROR] war 다운로드 실패: ${WAR_BUCKET_URI}" >&2
    rm -f "${DOWNLOAD_TMP}"
    exit 1
fi

if [ ! -s "${DOWNLOAD_TMP}" ]; then
    echo "[war-deploy][ERROR] 다운로드된 war 파일이 비어 있습니다." >&2
    rm -f "${DOWNLOAD_TMP}"
    exit 1
fi

echo "[war-deploy] 다운로드 완료: $(du -h "${DOWNLOAD_TMP}" | cut -f1)"

# =============================================================================
# 4. Tomcat 중지 (기존 배포본 정리 중 충돌 방지)
# =============================================================================

if systemctl list-unit-files --type=service | grep -q '^tomcat.service'; then
    if systemctl is-active --quiet tomcat; then
        echo "[war-deploy] 배포 전 Tomcat 중지"
        systemctl stop tomcat
    fi
fi

# =============================================================================
# 5. 기존 배포본 제거 후 새 war 배치
# =============================================================================

mkdir -p "${WEBAPPS_DIR}"

echo "[war-deploy] 기존 배포본 정리: ${WAR_FILE}, ${APP_DIR}"
rm -f "${WAR_FILE}"
rm -rf "${APP_DIR}"

echo "[war-deploy] 신규 war 배치: ${WAR_FILE}"
mv "${DOWNLOAD_TMP}" "${WAR_FILE}"
chown "${TOMCAT_USER}:${TOMCAT_GROUP}" "${WAR_FILE}"
chmod 640 "${WAR_FILE}"

# =============================================================================
# 6. war 압축 해제 (Tomcat 기동 전에 WEB-INF 리소스가 필요하므로 직접 풀어둔다)
# =============================================================================

echo "[war-deploy] war 압축 해제: ${APP_DIR}"
mkdir -p "${APP_DIR}"

if command -v unzip >/dev/null 2>&1; then
    unzip -q "${WAR_FILE}" -d "${APP_DIR}"
else
    echo "[war-deploy] unzip 미설치, jar 명령으로 압축 해제"
    ( cd "${APP_DIR}" && jar -xf "${WAR_FILE}" )
fi

chown -R "${TOMCAT_USER}:${TOMCAT_GROUP}" "${APP_DIR}"

echo "[war-deploy] $(date -Iseconds) 배포 완료"
