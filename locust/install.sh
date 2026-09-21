#!/usr/bin/env bash
# Locust 부하테스트 서버 설치 스크립트
# 대상: Proxmox 위에서 생성한 Ubuntu/Debian VM (root 또는 sudo 권한 필요)
set -euo pipefail

LOCUST_USER="locust"
LOCUST_HOME="/opt/locust"
LOCUST_PORT="${LOCUST_PORT:-8089}"

echo ">>> 패키지 업데이트 및 python3-venv 설치"
apt-get update -y
apt-get install -y python3 python3-venv python3-pip

echo ">>> locust 전용 시스템 사용자 생성"
if ! id "$LOCUST_USER" &>/dev/null; then
    useradd --system --create-home --home-dir "$LOCUST_HOME" --shell /usr/sbin/nologin "$LOCUST_USER"
fi

echo ">>> 가상환경 생성 및 locust 설치"
mkdir -p "$LOCUST_HOME"
python3 -m venv "$LOCUST_HOME/venv"
"$LOCUST_HOME/venv/bin/pip" install --upgrade pip
"$LOCUST_HOME/venv/bin/pip" install -r "$(dirname "$0")/requirements.txt"

echo ">>> locustfile.py 배치"
cp "$(dirname "$0")/locustfile.py" "$LOCUST_HOME/locustfile.py"
chown -R "$LOCUST_USER":"$LOCUST_USER" "$LOCUST_HOME"

echo ">>> systemd 서비스 등록"
sed "s|{{LOCUST_HOME}}|$LOCUST_HOME|g; s|{{LOCUST_USER}}|$LOCUST_USER|g; s|{{LOCUST_PORT}}|$LOCUST_PORT|g" \
    "$(dirname "$0")/locust.service.template" > /etc/systemd/system/locust.service

systemctl daemon-reload
systemctl enable --now locust

echo ">>> UFW 방화벽에 포트 개방 (설치되어 있는 경우)"
if command -v ufw &>/dev/null; then
    ufw allow "$LOCUST_PORT"/tcp || true
fi

echo ">>> 완료. 상태 확인: systemctl status locust"
echo ">>> 웹 UI: http://<VM_IP>:${LOCUST_PORT}"
