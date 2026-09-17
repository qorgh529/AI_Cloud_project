#!/usr/bin/env bash
#
# Rocky Linux 9 + JDK 17 + Tomcat 9 환경에서
# https://github.com/bespin-nova/WAS (Spring Framework Petclinic) 을
# clone -> build(Maven) -> Tomcat 배포/실행 까지 수행하는 스크립트.
#
# 사전 조건:
#   - JDK 17, Tomcat 9 가 이미 설치되어 있어야 함
#     (/opt/tomcat 에 설치되고 systemd 서비스명이 tomcat 이라고 가정. 다르면 아래 변수 수정)
#   - Cloud SQL(MySQL) 접속 정보를 환경변수(DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASS)로 주입해야 함.
#     비밀번호를 이 파일이나 git에 직접 남기지 않기 위해, 같은 디렉터리의
#     deploy_petclinic.local.env (git-ignore 대상) 파일이 있으면 자동으로 읽어들인다.
#
# 사용법:
#   sudo -E ./deploy_petclinic.sh
#   (또는) sudo DB_HOST=... DB_NAME=... DB_USER=... DB_PASS=... ./deploy_petclinic.sh
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCAL_ENV_FILE="${SCRIPT_DIR}/deploy_petclinic.local.env"

# ── 환경 변수 (필요시 수정) ─────────────────────────────
REPO_URL="https://github.com/bespin-nova/WAS.git"
APP_NAME="petclinic"
WORKDIR="/opt/build/${APP_NAME}"
CATALINA_HOME="/opt/tomcat"
TOMCAT_SERVICE="tomcat"
TOMCAT_USER="tomcat"
JAVA_HOME_DIR="$(dirname "$(dirname "$(readlink -f "$(command -v java)")")")"
# ────────────────────────────────────────────────────

log() { echo -e "\n\033[1;32m[INFO]\033[0m $*"; }
err() { echo -e "\n\033[1;31m[ERROR]\033[0m $*" >&2; }

if [[ $EUID -ne 0 ]]; then
  err "root 권한으로 실행해야 합니다. (sudo -E ./deploy_petclinic.sh)"
  exit 1
fi

# Cloud SQL(MySQL) 연결 정보: 로컬 설정 파일(있는 경우) -> 환경변수 순으로 채움
if [[ -f "$LOCAL_ENV_FILE" ]]; then
  log "로컬 DB 설정 파일 로드: ${LOCAL_ENV_FILE}"
  set -a
  # shellcheck disable=SC1090
  source "$LOCAL_ENV_FILE"
  set +a
fi

DB_HOST="${DB_HOST:-}"
DB_PORT="${DB_PORT:-3306}"
DB_NAME="${DB_NAME:-petclinic}"
DB_USER="${DB_USER:-}"
DB_PASS="${DB_PASS:-}"

if [[ -z "$DB_HOST" || -z "$DB_USER" || -z "$DB_PASS" ]]; then
  err "DB_HOST/DB_USER/DB_PASS 가 설정되지 않았습니다."
  err "  1) ${LOCAL_ENV_FILE} 파일을 만들어 DB_HOST=... 형태로 정의하거나"
  err "  2) sudo DB_HOST=... DB_USER=... DB_PASS=... ./deploy_petclinic.sh 로 실행하세요."
  exit 1
fi

# 1) 사전 조건 확인 ------------------------------------------------
log "JDK / Tomcat 설치 여부 확인"

if ! command -v java >/dev/null 2>&1; then
  err "java 명령을 찾을 수 없습니다. 먼저 JDK 17을 설치하세요."
  exit 1
fi
java -version

if [[ ! -d "$CATALINA_HOME" ]]; then
  err "$CATALINA_HOME 디렉터리가 없습니다. Tomcat 9 설치를 먼저 진행하세요."
  exit 1
fi

if ! systemctl list-unit-files | grep -q "^${TOMCAT_SERVICE}.service"; then
  err "${TOMCAT_SERVICE}.service systemd 유닛을 찾을 수 없습니다."
  exit 1
fi

# git / 필수 패키지 설치
if ! command -v git >/dev/null 2>&1; then
  log "git 설치"
  dnf install -y git
fi

# 2) 소스 clone ------------------------------------------------------
log "소스 clone: ${REPO_URL}"
mkdir -p "$(dirname "$WORKDIR")"

if [[ -d "$WORKDIR/.git" ]]; then
  log "이미 clone 된 디렉터리 발견, git pull로 업데이트"
  git -C "$WORKDIR" fetch --all
  git -C "$WORKDIR" reset --hard origin/HEAD
else
  rm -rf "$WORKDIR"
  git clone "$REPO_URL" "$WORKDIR"
fi

cd "$WORKDIR"
chmod +x mvnw

# 3) 빌드 (Maven Wrapper 사용, JDK 17 지정, MySQL(Cloud SQL) 프로필 활성화) ---
log "Maven 빌드 시작 (JAVA_HOME=${JAVA_HOME_DIR}, DB=${DB_HOST}:${DB_PORT}/${DB_NAME})"
export JAVA_HOME="$JAVA_HOME_DIR"
export PATH="$JAVA_HOME/bin:$PATH"

# MySQL 프로필 활성화(mysql-connector-java 의존성 포함) +
# data-access.properties 의 ${MYSQL_URL}/${MYSQL_USER}/${MYSQL_PASS} 플레이스홀더를
# 빌드 시점에 리소스 필터링으로 치환
./mvnw -B clean package -DskipTests -P MySQL \
  -DMYSQL_URL="jdbc:mysql://${DB_HOST}:${DB_PORT}/${DB_NAME}?useUnicode=true" \
  -DMYSQL_USER="${DB_USER}" \
  -DMYSQL_PASS="${DB_PASS}"

WAR_FILE=$(find target -maxdepth 1 -name "*.war" | head -n1)
if [[ -z "$WAR_FILE" ]]; then
  err "빌드된 WAR 파일을 찾지 못했습니다. target/ 디렉터리를 확인하세요."
  exit 1
fi
log "빌드 완료: $WAR_FILE"

# 4) 기존 배포 정리 및 WAR 배포 ---------------------------------------
log "Tomcat 중지"
systemctl stop "$TOMCAT_SERVICE"

log "기존 배포본 제거 (있는 경우)"
rm -rf "${CATALINA_HOME}/webapps/${APP_NAME}" "${CATALINA_HOME}/webapps/${APP_NAME}.war"

log "새 WAR 배포: ${APP_NAME}.war"
cp "$WAR_FILE" "${CATALINA_HOME}/webapps/${APP_NAME}.war"
chown "${TOMCAT_USER}:${TOMCAT_USER}" "${CATALINA_HOME}/webapps/${APP_NAME}.war"

log "Tomcat 시작"
systemctl start "$TOMCAT_SERVICE"

# 5) 배포 확인 (자동 압축 해제 대기) -----------------------------------
log "애플리케이션 기동 대기 중..."
DEPLOYED=false
for i in $(seq 1 30); do
  if [[ -d "${CATALINA_HOME}/webapps/${APP_NAME}" ]]; then
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8080/${APP_NAME}/" || true)
    if [[ "$STATUS" == "200" ]]; then
      DEPLOYED=true
      break
    fi
  fi
  sleep 2
done

if [[ "$DEPLOYED" == "true" ]]; then
  log "배포 성공! 접속 확인: http://<서버IP>:8080/${APP_NAME}/"
else
  err "배포 확인 실패. 로그를 확인하세요: ${CATALINA_HOME}/logs/catalina.out"
  tail -n 50 "${CATALINA_HOME}/logs/catalina.out" || true
  exit 1
fi

log "완료되었습니다."
