# Proxmox VM에 Locust 설치 및 외부 접속 가이드

Proxmox 위에 만든 VM에 [Locust](https://locust.io) 부하테스트 도구를 설치하고,
사내망 밖(외부)에서 웹 UI(기본 8089 포트)에 접속할 수 있도록 구성하는 절차입니다.

## 구성 개요

```
[외부 사용자] --https/http--> [공유기/라우터 포트포워딩]
                                        |
                                   [Proxmox 호스트]
                                        |
                               [Locust VM: vmbr0 브리지]
                                    (nginx :80/443 -> locust :8089)
```

## 1. Proxmox에서 VM 생성 및 네트워크 구성

1. Proxmox 웹 UI에서 VM 생성 (Ubuntu 22.04/Debian 12 권장, 2 vCPU / 2~4GB RAM 이상).
2. VM의 네트워크 장치를 **`vmbr0`** (물리 NIC과 브리지된 인터페이스)에 연결.
   - 외부에서 직접 붙는 구조를 원하면 VM에 공인 대역과 같은 서브넷의 IP를 부여하거나,
     라우터에서 해당 VM의 사설 IP로 포트포워딩을 설정.
3. VM 부팅 후 고정 IP 설정 (DHCP reservation 또는 netplan static IP 권장) — 외부 접속 경로가
   바뀌지 않도록.
4. Proxmox 호스트 방화벽(Datacenter/Node/VM 레벨)을 쓰는 경우, 해당 VM에 대해
   8089(TCP), 필요 시 80/443(TCP)을 허용.

## 2. Locust 설치 (VM 내부에서 실행)

이 디렉터리를 VM으로 복사한 뒤 실행합니다.

```bash
scp -r locust/ user@<VM_IP>:/tmp/locust-setup
ssh user@<VM_IP>
cd /tmp/locust-setup
sudo bash install.sh
```

`install.sh`가 하는 일:
- python3-venv 설치, `locust` 시스템 계정 생성
- `/opt/locust/venv`에 가상환경 생성 후 `requirements.txt`(locust) 설치
- 샘플 `locustfile.py` 배치 (테스트 대상 URL에 맞게 직접 수정 필요)
- `locust.service` systemd 유닛 등록 (`--web-host 0.0.0.0 --web-port 8089`로 기동 → 모든 인터페이스에서 접근 가능)
- `ufw`가 설치돼 있으면 8089/tcp 자동 허용

설치 후 확인:

```bash
systemctl status locust
curl -I http://localhost:8089
```

`locustfile.py`는 실제 테스트할 서비스에 맞춰 수정하세요 (`self.client.get("/")` 부분 등).
수정 후에는 `sudo cp locustfile.py /opt/locust/locustfile.py && sudo systemctl restart locust`.

## 3. 외부 접속 열기

### 옵션 A — 사설망/VPN에서만 접속 (권장, 가장 안전)

방화벽에서 8089를 신뢰할 수 있는 IP 대역(회사 VPN, 특정 사무실 IP 등)에만 허용하고
바로 `http://<VM_IP>:8089`로 접속.

### 옵션 B — 인터넷에 공개 (nginx 리버스 프록시 + 인증 + TLS)

Locust 웹 UI는 기본적으로 인증이 없어, 맨 포트를 그대로 인터넷에 열면 누구나
부하테스트를 시작/조작할 수 있습니다. 외부에 공개하려면 반드시 인증을 앞단에 둡니다.

```bash
sudo apt-get install -y nginx apache2-utils
sudo htpasswd -c /etc/nginx/.locust_htpasswd <원하는 계정명>
sudo cp nginx-locust.conf.example /etc/nginx/sites-available/locust
sudo ln -s /etc/nginx/sites-available/locust /etc/nginx/sites-enabled/locust
sudo nginx -t && sudo systemctl reload nginx
```

- 라우터/공유기에서 80(및 443)을 이 VM의 사설 IP로 포트포워딩.
- 도메인이 있다면 `nginx-locust.conf.example`의 `server_name`을 도메인으로 바꾸고
  `certbot --nginx`로 TLS 인증서 발급.
- Locust 웹소켓(실시간 통계)이 동작하려면 `Upgrade`/`Connection` 헤더 프록시 설정이
  필요합니다 (예시 파일에 이미 포함).
- 이 구성을 쓰면 8089는 `127.0.0.1`(로컬)에서만 열려 있어도 되므로,
  `locust.service.template`의 `--web-host` 를 `127.0.0.1`로 바꾸고
  외부 노출은 nginx만 담당하도록 하는 것이 더 안전합니다.

## 4. 분산 부하테스트 (여러 VM에서 트래픽 생성)

부하량이 커서 VM 한 대로 부족하면 master/worker 구조를 씁니다.

```bash
# master (웹 UI를 띄우는 VM)
locust -f locustfile.py --master --web-host 0.0.0.0

# worker (추가 VM, 여러 대 가능)
locust -f locustfile.py --worker --master-host <MASTER_VM_IP>
```

worker → master 통신을 위해 5557/5558(TCP) 포트를 master VM 방화벽에서 열어줘야 합니다
(외부 공개가 아니라 내부망/VPN에서만 열면 충분합니다).

## 5. 보안 체크리스트

- [ ] 8089를 인증 없이 인터넷에 직접 노출하지 않았는가 (옵션 A 또는 B 사용)
- [ ] 테스트 대상(`--host`)이 본인/조직이 소유·허가받은 시스템인가 (무단 부하테스트 금지)
- [ ] TLS(HTTPS) 적용했는가 (옵션 B)
- [ ] 사용하지 않을 때는 `systemctl stop locust` 또는 방화벽 포트를 닫아두었는가
