# -*- coding: utf-8 -*-
from lib import Page, BLUE, RED, YEL, GRN, GREY, INK

GREEN_S, GREEN_F = '#34A853', '#F2FBF5'
BLUE_F, YEL_F, RED_F, GREY_F = '#F5F9FF', '#FFFBF0', '#FEF4F3', '#F8F9FA'


def build():
    p = Page('① 전체 아키텍처 (3-Tier Overview)', 2300, 1840)

    # ---------------------------------------------------------------- header
    p.text('t1', 50, 18, 1800, 34,
           'GCP 3-Tier Architecture — Spring PetClinic', fs=24, bold=1, align='left')
    p.text('t2', 50, 54, 1900, 22,
           'Team NOVA (GCP 1팀)  ·  Region: asia-northeast3 (Seoul)  ·  '
           'WEB: Apache 2.4  |  WAS: Tomcat 9 + OpenJDK 17  |  DB: Cloud SQL for MySQL 8.0',
           fs=13, color=GREY, align='left')
    p.note('t3', 50, 82, 2200, 30,
           '<b>Service Flow</b>&nbsp; User → Cloud DNS → Cloud Armor → External HTTPS LB (+Cloud CDN) → '
           '<b>WEB</b> Apache 2.4 (mod_proxy) → Internal Application LB → '
           '<b>WAS</b> Tomcat + PetClinic → <b>DB</b> Cloud SQL MySQL (Private IP)',
           fill='#E8F0FE', stroke=BLUE, fs=13)

    # ------------------------------------------------------------------ edge
    p.box('edge', 50, 130, 1420, 190, '① Global Edge  —  Google Front End (Premium Network Tier)',
          stroke=BLUE, fill=BLUE_F)
    ex = [130, 345, 570, 800, 1030, 1290]
    p.icon('i_user', 'User', ex[0], 190, '사용자 / 브라우저\nHTTPS :443', lw=190)
    p.icon('i_dns', 'Cloud DNS', ex[1], 190,
           'Cloud DNS\npetclinic.nova-gcp.kr\n(Public Zone · A record)', lw=205)
    p.icon('i_gip', 'Cloud External IP Addresses', ex[2], 190,
           'Global Anycast IP\n(고정 공인 IP · Forwarding Rule)', lw=215)
    p.icon('i_armor', 'CloudArmor', ex[3], 190,
           'Cloud Armor\nWAF(OWASP CRS) · L7 DDoS\nGeo 제한(KR) · Rate Limit', lw=215)
    p.icon('i_cdn', 'Cloud CDN', ex[4], 190,
           'Cloud CDN\n정적 콘텐츠 캐싱\n(index.html · css/js/img)', lw=205)
    p.icon('i_elb', 'Cloud Load Balancing', ex[5], 190,
           'External Application LB\nGlobal · Google-managed SSL\nHTTP→HTTPS Redirect', lw=225)

    for i, (a, b, lb) in enumerate([
            ('i_user', 'i_dns', '도메인 질의'), ('i_dns', 'i_gip', 'A 레코드 응답'),
            ('i_gip', 'i_armor', ''), ('i_armor', 'i_cdn', '정책 통과'),
            ('i_cdn', 'i_elb', 'Cache Miss')]):
        p.edge(f'e_edge{i}', a, b, lb, exit=(1, 0.5), entry=(0, 0.5))

    # legend of added services
    p.note('lg', 1500, 130, 750, 190,
           '<b style="font-size:13px;color:#202124">설계 원칙 (MSP Design Principles)</b>'
           '<br/>• <b>필수 요구사항</b> — 3-Tier 분리 / External·Internal LB / Apache mod_proxy / Cloud SQL Private IP'
           '<br/>• <b>공인 IP 최소화</b> — 모든 VM은 External IP 미할당, 외부 통신은 Cloud NAT 경유'
           '<br/>• <b>Zero Trust 관리 접근</b> — SSH 22 포트 인터넷 개방 금지, IAP TCP Forwarding + Bastion'
           '<br/>• <b>Stateless WAS</b> — Memorystore Redis 세션 외부화로 MIG 스케일 아웃/인 안전'
           '<br/>• <b>Regional MIG</b> — 3개 Zone 분산 배치로 Zone 장애에도 서비스 지속 (99.99%)'
           '<br/>• <b>최소 권한</b> — Network Tag 기반 방화벽, IAM 역할 분리, Secret Manager 자격증명 분리'
           '<br/>• <b>관측 가능성</b> — Ops Agent 전면 배포, SLO 기반 알림 (단순 임계치 알림 지양)',
           fill='#FFFFFF', stroke=GREY, fs=11)

    # --------------------------------------------------------------- project
    p.box('proj', 50, 350, 2200, 880,
          'Google Cloud Project:  nova-petclinic-prd      (Org Policy · VPC Service Controls 적용)',
          stroke=GREY, fill=GREY_F, dashed=0, fs=14, fc=INK)
    p.icon('i_vpcic', 'Virtual Private Cloud', 96, 392, '', ih=30)
    p.box('vpc', 78, 410, 1580, 800,
          '        VPC: petclinic-vpc  (Custom Mode)  ·  asia-northeast3  ·  MTU 1460  ·  Private Google Access 사용',
          stroke=BLUE, fill='#FFFFFF', dashed=1, fs=13)

    # ---- WEB tier
    p.box('sn_web', 104, 468, 1020, 205,
          '② WEB Tier  —  web-subnet  10.10.10.0/24   (External IP 없음)',
          stroke=GREEN_S, fill=GREEN_F, fs=12)
    p.box('mig_web', 132, 512, 830, 145,
          'Regional MIG: web-mig  ·  Zone a/b/c 분산  ·  Autoscale 2~6  ·  CPU 60% / LB 사용률',
          stroke=YEL, fill='none', fs=11, fc='#8A6D00')
    for i, (cx, z) in enumerate([(245, 'a'), (547, 'b'), (849, 'c')]):
        p.icon(f'i_web{i}', 'Compute Engine', cx, 548,
               f'web-vm-0{i+1}  (zone {z})\nApache 2.4 + mod_proxy\ne2-medium · Shielded VM', lw=250)
    p.icon('i_as1', 'Modifiers - Autoscaling', 1045, 528,
           'Autoscaler\n+ Health Check\nHTTP GET /health', lw=140, lfs=10)

    # ---- management subnet
    p.box('sn_mgmt', 1148, 468, 488, 205,
          '④ 관리 —  mgmt-subnet  10.10.40.0/24', stroke=GREY, fill='#FFFFFF', fs=12, fc=GREY)
    for i, (cx, ic, lb) in enumerate([
            (1210, 'BeyondCorp', 'IAP\nTCP Forwarding'),
            (1330, 'Compute Engine', 'Bastion\n(OS Login+MFA)'),
            (1455, 'Cloud NAT', 'Cloud NAT\n아웃바운드 전용'),
            (1575, 'Cloud Router', 'Cloud Router\n동적 라우팅')]):
        p.icon(f'i_mg{i}', ic, cx, 522, lb, lw=120, lfs=10)

    # ---- internal LB
    p.icon('i_ilb', 'Cloud Load Balancing', 547, 700,
           'Internal Application LB (L7)  ·  10.10.10.100  ·  Least Request  ·  Session Affinity: NONE',
           lw=560, lfs=11, lbold=1)

    # ---- WAS tier
    p.box('sn_was', 104, 790, 1020, 205,
          '③ WAS Tier  —  was-subnet  10.10.20.0/24   (Private)',
          stroke=GREEN_S, fill=GREEN_F, fs=12)
    p.box('mig_was', 132, 834, 830, 145,
          'Regional MIG: was-mig  ·  Zone a/b/c 분산  ·  Autoscale 2~8  ·  CPU 60%',
          stroke=YEL, fill='none', fs=11, fc='#8A6D00')
    for i, (cx, z) in enumerate([(245, 'a'), (547, 'b'), (849, 'c')]):
        p.icon(f'i_was{i}', 'Compute Engine', cx, 870,
               f'was-vm-0{i+1}  (zone {z})\nTomcat 9 + OpenJDK 17\npetclinic.war · :8080', lw=250)

    p.box('sn_redis', 1148, 790, 488, 205,
          '세션 클러스터링 (Stateless WAS)', stroke=GREY, fill='#FFFFFF', fs=12, fc=GREY)
    p.icon('i_redis', 'MemoryStore', 1392, 846,
           'Memorystore for Redis (Standard HA)\nTomcat Session Store  ·  :6379\nMIG 스케일 시 세션 유실 방지', lw=300)

    # ---- DB tier
    p.box('sn_db', 104, 1020, 1532, 170,
          '⑤ DB Tier  —  db-subnet  10.10.30.0/24  ·  Private Service Access (VPC Peering)  ·  Public IP 미할당',
          stroke=GREEN_S, fill=GREEN_F, fs=12)
    p.icon('i_sql1', 'Cloud SQL', 330, 1062,
           'Cloud SQL for MySQL 8.0  —  Primary\nRegional HA · CMEK · DB: petclinic', lw=320, lbold=1)
    p.icon('i_sql2', 'Cloud SQL', 820, 1062,
           'Standby  (다른 Zone)\n동기 복제 · 자동 Failover', lw=280)
    p.icon('i_sql3', 'Cloud SQL', 1330, 1062,
           'Read Replica\n읽기 분산 · 백업 오프로드', lw=280)

    # ------------------------------------------------- shared managed services
    p.box('shared', 1688, 410, 540, 800,
          '공용 관리형 서비스   ←   WEB/WAS VM 이 Private Google Access 로 호출\n'
          '      (비밀 조회 · WAR/정적자산 Pull · 로그 전송 — 인터넷 미경유)',
          stroke=BLUE, fill=BLUE_F, fs=12)
    shared = [
        (1815, 470, 'Secret Manager', 'Secret Manager\nDB 계정·JDBC 비밀\n코드/이미지에 평문 저장 금지'),
        (2095, 470, 'Cloud Storage', 'Cloud Storage\npetclinic.war · 정적자산\n백업 아카이브 버킷'),
        (1815, 650, 'Artifact Registry', 'Artifact Registry\nWAR/컨테이너 아티팩트\n버전 관리'),
        (2095, 650, 'Cloud Build', 'Cloud Build\nWAR 빌드 → MIG 롤링 업데이트'),
        (1815, 830, 'Key Management Service', 'Cloud KMS (CMEK)\nPD · GCS · Cloud SQL 암호화\n키 순환 90일'),
        (2095, 830, 'Cloud Source Repositories', 'Source Repo / GitHub\nTerraform IaC · 스크립트'),
        (1815, 1010, 'Cloud IAM', 'Cloud IAM\n역할 분리(서버/네트워크/보안)\n최소권한 · 서비스 계정'),
        (2095, 1010, 'Cloud Console', 'Cloud Console / gcloud\n운영자 관리 진입점'),
    ]
    for i, (cx, y, ic, lb) in enumerate(shared):
        p.icon(f'i_sh{i}', ic, cx, y, lb, lw=250, lfs=10)

    # ------------------------------------------------------------- flow edges
    p.edge('f1', 'i_elb', 'mig_web', 'HTTP :80  ·  Backend Service (web-mig)  ·  Health Check',
           exit=(0.5, 1), entry=(0.75, 0), sw=3)
    p.edge('f2', 'mig_web', 'i_ilb', 'mod_proxy  →  HTTP', exit=(0.5, 1), entry=(0.5, 0), sw=3)
    p.edge('f3', 'i_ilb', 'mig_was', 'HTTP :8080  ·  Backend Service (was-mig)', exit=(0.5, 1),
           entry=(0.5, 0), sw=3)
    p.edge('f4', 'mig_was', 'i_sql1', 'JDBC :3306  (Private IP)', exit=(0.25, 1), entry=(0.5, 0), sw=3)
    p.edge('f5', 'mig_was', 'i_redis', 'Redis :6379  (세션)', exit=(1, 0.5), entry=(0, 0.5), sw=2)
    p.edge('f6', 'i_sql1', 'i_sql2', '동기 복제', exit=(1, 0.5), entry=(0, 0.5), sw=2, color=GREEN_S)
    p.edge('f7', 'i_sql2', 'i_sql3', '비동기 복제', exit=(1, 0.5), entry=(0, 0.5), sw=2, color=GREEN_S)
    p.edge('f8', 'vpc', 'shared', '', exit=(1, 0.28), entry=(0, 0.28), dashed=1, sw=2, color=GREY)
    p.edge('f9', 'vpc', 'shared', '', exit=(1, 0.62), entry=(0, 0.62), dashed=1, sw=2, color=GREY)
    p.edge('f10', 'i_mg0', 'sn_web', 'IAP :22', exit=(0, 0.5), entry=(1, 0.86), dashed=1, sw=1,
           color=GREY)
    p.edge('f11', 'i_mg2', 'sn_was', '아웃바운드 (패치/apt)', exit=(0.5, 1), entry=(1, 0.2),
           dashed=1, sw=1, color=GREY)

    # ------------------------------------------------------------- ops panels
    panels = [
        ('pa', 50, 1258, 710, '⑥ 모니터링 · 옵저버빌리티  (Cloud Operations Suite)', BLUE, BLUE_F,
         [('Cloud Monitoring', 130, 'Cloud Monitoring'), ('Cloud Logging', 300, 'Cloud Logging'),
          ('Trace', 470, 'Cloud Trace'), ('Error Reporting', 650, 'Error Reporting')],
         '• <b>Ops Agent</b> 전 VM 배포 → CPU/메모리/디스크/프로세스 + <b>Apache·Tomcat·MySQL</b> 플러그인 메트릭'
         '<br/>• <b>Uptime Check</b> (다중 리전) + <b>SLO</b> 99.9% 가용성 / p95 &lt; 500ms → Burn-rate 알림'
         '<br/>• <b>알림 채널</b>: Email · Google Chat · Slack · SMS  (Sev1 즉시 / Sev2 15분 집계)'
         '<br/>• <b>Log Router</b> → GCS(장기 보관 365일) · BigQuery(분석) · Log-based Metric(5xx 비율)'
         '<br/>• <b>Trace / Profiler / Error Reporting</b> 으로 WAS 지연·예외 근본 원인 분석'),
        ('pb', 786, 1258, 710, '⑦ 백업 · 복구  (Backup & Recovery)', GRN, '#F2FBF5',
         [('Persistent Disk', 866, 'PD Snapshot'), ('Cloud Scheduler', 1036, 'Cloud Scheduler'),
          ('Cloud Functions', 1206, 'Cloud Functions'), ('Cloud Storage', 1386, 'Cloud Storage')],
         '• <b>VM</b>: Snapshot Schedule 매일 03:00 KST (일 7 / 주 4 / 월 12 보존) + Machine Image(골든)'
         '<br/>• <b>DB</b>: Cloud SQL 자동 백업 03:30 KST + <b>PITR</b>(binlog 7일) + 월 1회 온디맨드'
         '<br/>• <b>파일 반출</b>: Cloud Scheduler → Pub/Sub → Cloud Functions → Cloud SQL <b>Export</b> → GCS'
         '<br/>• <b>GCS 정책</b>: Dual-region · Object Versioning · Retention Lock · Lifecycle'
         '<br/>&nbsp;&nbsp;&nbsp;Standard → Nearline(30d) → Coldline(90d) → Archive(365d)'
         '<br/>• <b>복구 훈련</b>: 분기 1회 스냅샷 복원 + DB PITR 리허설 (복구 절차 문서화)'),
        ('pc', 1522, 1258, 728, '⑧ 보안 · 거버넌스  (Security & Governance)', RED, RED_F,
         [('Cloud Firewall Rules', 1602, 'VPC Firewall'), ('Cloud IAM', 1772, 'Cloud IAM'),
          ('BeyondCorp', 1942, 'IAP / OS Login'),
          ('Security Command Center', 2130, 'Security Command Center')],
         '• <b>방화벽</b>: Network Tag 기반 최소 허용, 마지막 규칙 <b>0.0.0.0/0 DENY</b> (우선순위 65534)'
         '<br/>• <b>Cloud Armor</b>: OWASP 사전구성 WAF(sqli/xss/lfi) · KR 외 차단 · Adaptive Protection'
         '<br/>• <b>IAM</b>: 서버/네트워크/보안 담당 역할 분리, 사용자 MFA, VM은 전용 서비스 계정'
         '<br/>• <b>암호화</b>: 전송 TLS 1.2+ · 저장 CMEK(Cloud KMS) · 비밀값 Secret Manager'
         '<br/>• <b>탐지</b>: Security Command Center 취약점/구성오류, Cloud Audit Logs 불변 보관'),
    ]
    for pid, px, py, pw, title, sc, fc2, icons, body in panels:
        p.box(pid, px, py, pw, 320, title, stroke=sc, fill=fc2, dashed=0, fs=13)
        for j, (ic, cx, lb) in enumerate(icons):
            p.icon(f'{pid}_i{j}', ic, cx, 1300, lb, ih=42, lw=160, lfs=10)
        p.note(f'{pid}_n', px + 18, 1400, pw - 36, 162, body, fill='#FFFFFF', stroke='#DADCE0', fs=11)

    # ------------------------------------------------------------------- DR
    p.box('dr', 50, 1604, 2200, 180,
          '⑨ 재해복구 (DR)  —  asia-northeast1 (Tokyo)  ·  목표 RTO ≤ 4시간 / RPO ≤ 15분  ·  Warm Standby(Pilot Light)',
          stroke=YEL, fill=YEL_F, dashed=0, fs=13, fc='#8A6D00')
    dr = [(230, 'Cloud SQL', 'Cross-region Read Replica\n장애 시 독립 인스턴스로 승격'),
          (640, 'Cloud Storage', 'Dual-region Bucket\n스냅샷·Export 자동 복제'),
          (1050, 'Compute Engine', 'Pilot-light MIG (size 0)\n동일 Instance Template 사전 등록'),
          (1460, 'Cloud DNS', 'DNS 전환\n평시 TTL 300s → 전환 시 30s'),
          (1900, 'Cloud VPN', 'HA VPN → 온프레미스\nMySQL 복제 · rsync 파일 백업')]
    for i, (cx, ic, lb) in enumerate(dr):
        p.icon(f'i_dr{i}', ic, cx, 1656, lb, ih=42, lw=330, lfs=11)
    for i in range(4):
        p.edge(f'e_dr{i}', f'i_dr{i}', f'i_dr{i+1}', '', color=YEL, dashed=1, sw=1,
               exit=(1, 0.5), entry=(0, 0.5))
    return p
