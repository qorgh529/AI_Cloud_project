# -*- coding: utf-8 -*-
from lib import Page, BLUE, RED, YEL, GRN, GREY, INK

BLUE_F, GRN_F, YEL_F, RED_F = '#F5F9FF', '#F2FBF5', '#FFFBF0', '#FEF4F3'


def build():
    p = Page('④ 보안 · 네트워크 상세', 2180, 1210)
    p.text('t1', 50, 20, 1600, 32, '보안 · 네트워크 상세 설계  (Defense in Depth)', fs=23, bold=1,
           align='left')
    p.text('t2', 50, 56, 1900, 22,
           '경계(Cloud Armor) → 네트워크(VPC/방화벽) → 신원(IAM/IAP) → 데이터(KMS/Secret Manager) → 탐지(SCC/Audit Log)',
           fs=13, color=GREY, align='left')

    # ---- layers
    layers = [
        ('L1', 50, 100, 400, '① 경계 보안 (Edge)', RED, RED_F,
         [('CloudArmor', 150, 'Cloud Armor'), ('Cloud CDN', 340, 'Cloud CDN')],
         '• <b>Geo 제한</b>: <code>origin.region_code == "KR"</code> 외 전부 403 차단'
         '<br/>&nbsp;&nbsp;(한국 전용 서비스 요구사항 반영)'
         '<br/>• <b>WAF</b>: 사전 구성 규칙 <code>sqli-v33</code>, <code>xss-v33</code>,'
         '<br/>&nbsp;&nbsp;<code>lfi-v33</code>, <code>rce-v33</code> — 민감도 단계적 상향'
         '<br/>• <b>L3/L4 DDoS</b>: Global LB 사용 시 기본 제공(SYN/ICMP flood)'
         '<br/>• <b>L7 DDoS</b>: Adaptive Protection 으로 이상 트래픽 학습·제안'
         '<br/>• <b>Rate Limit</b>: IP당 100 req/min 초과 시 429'
         '<br/>• <b>SSL</b>: Google-managed 인증서, LB 에서 SSL Offload,'
         '<br/>&nbsp;&nbsp;TLS 1.2+ 정책, HTTP→HTTPS 301 리다이렉트'),
        ('L2', 480, 100, 420, '② 네트워크 보안', GRN, GRN_F,
         [('Cloud Firewall Rules', 580, 'VPC Firewall'), ('Cloud NAT', 790, 'Cloud NAT')],
         '• <b>Custom Mode VPC</b> — 기본 VPC 미사용, 서브넷 수동 설계'
         '<br/>• <b>Network Tag 기반</b> 규칙 (IP 하드코딩 최소화)'
         '<br/>• <b>공인 IP 0개</b> — 모든 VM External IP 미할당'
         '<br/>• <b>Cloud NAT</b> — 아웃바운드 전용(인바운드 불가),'
         '<br/>&nbsp;&nbsp;패치·apt 업데이트 경로. 로깅 활성화'
         '<br/>• <b>Private Google Access</b> — GCS/Secret Manager 를'
         '<br/>&nbsp;&nbsp;인터넷 경유 없이 내부 경로로 호출'
         '<br/>• <b>Private Service Access</b> — Cloud SQL 비공개 IP'
         '<br/>&nbsp;&nbsp;(VPC Peering, Public IP 완전 미할당)'
         '<br/>• <b>Flow Logs</b> — 서브넷별 활성화(샘플링 0.5)'),
        ('L3', 930, 100, 420, '③ 신원 · 접근 제어', BLUE, BLUE_F,
         [('Cloud IAM', 1030, 'Cloud IAM'), ('BeyondCorp', 1240, 'IAP / OS Login')],
         '• <b>IAM 역할 분리</b> (요구사항 반영)'
         '<br/>&nbsp;&nbsp;- 서버 담당: <code>compute.instanceAdmin</code>'
         '<br/>&nbsp;&nbsp;- 네트워크: <code>compute.networkAdmin</code> +'
         '<br/>&nbsp;&nbsp;&nbsp;&nbsp;<code>compute.loadBalancerAdmin</code>'
         '<br/>&nbsp;&nbsp;- 보안: <code>compute.securityAdmin</code>'
         '<br/>• <b>기본 서비스 계정 미사용</b> — VM별 전용 SA에'
         '<br/>&nbsp;&nbsp;필요 권한만 부여 (secretAccessor, objectViewer)'
         '<br/>• <b>IAP TCP Forwarding</b> — SSH 22 를 인터넷에'
         '<br/>&nbsp;&nbsp;열지 않고 <code>35.235.240.0/20</code> 만 허용'
         '<br/>• <b>OS Login + 2단계 인증(MFA)</b> 강제'
         '<br/>• <b>Bastion</b> — 회사/승인 IP 만 접속, 별도 포트'),
        ('L4', 1380, 100, 380, '④ 데이터 보호', YEL, YEL_F,
         [('Key Management Service', 1470, 'Cloud KMS'), ('Secret Manager', 1670, 'Secret Manager')],
         '• <b>전송 중 암호화</b> — 외부 TLS 1.2+,'
         '<br/>&nbsp;&nbsp;내부 VPC 구간도 Google 기본 암호화'
         '<br/>• <b>저장 데이터 암호화</b> — CMEK 적용'
         '<br/>&nbsp;&nbsp;(Persistent Disk · GCS · Cloud SQL)'
         '<br/>• <b>키 순환</b> 90일 자동, 키 삭제 보호'
         '<br/>• <b>Secret Manager</b> — DB 비밀번호를'
         '<br/>&nbsp;&nbsp;startup-script/코드/이미지에 평문 저장 금지'
         '<br/>&nbsp;&nbsp;VM 부팅 시 SA 권한으로 런타임 조회'
         '<br/>• <b>버전 관리</b> — 비밀 교체 시 무중단 롤아웃'),
        ('L5', 1790, 100, 340, '⑤ 탐지 · 감사', GREY, '#F8F9FA',
         [('Security Command Center', 1880, 'SCC'), ('Data Loss Prevention API', 2050, 'DLP')],
         '• <b>Security Command Center</b>'
         '<br/>&nbsp;&nbsp;구성 오류 · 취약점 · 공개 리소스 탐지'
         '<br/>• <b>Cloud Audit Logs</b>'
         '<br/>&nbsp;&nbsp;Admin Activity 는 기본 활성 · 삭제 불가'
         '<br/>&nbsp;&nbsp;Data Access 로그 선택 활성화'
         '<br/>• <b>Org Policy</b> — 공인 IP 생성 금지,'
         '<br/>&nbsp;&nbsp;SA 키 생성 금지, 특정 리전만 허용'
         '<br/>• <b>DLP</b> — 로그/백업 내 개인정보 스캔'
         '<br/>• <b>Cloud Security Scanner</b> — 웹 취약점 점검'),
    ]
    for lid, x, y, w, title, sc, fc2, icons, body in layers:
        p.box(lid, x, y, w, 420, title, stroke=sc, fill=fc2, dashed=0, fs=13)
        for j, (ic, cx, lb) in enumerate(icons):
            p.icon(f'{lid}_i{j}', ic, cx, y + 48, lb, ih=40, lw=170, lfs=10)
        p.note(f'{lid}_n', x + 16, y + 144, w - 32, 262, body, fs=10.5)

    # ---- firewall matrix
    p.note('fw', 50, 552, 1290, 356,
           '<b style="font-size:14px">VPC 방화벽 규칙 설계 (최소 권한 · Network Tag 기반)</b>'
           '<table style="font-size:11px;border-collapse:collapse;width:100%;margin-top:8px">'
           '<tr style="background:#F1F3F4">'
           '<th align="left">우선순위</th><th align="left">규칙명</th><th align="left">소스</th>'
           '<th align="left">대상 태그</th><th align="left">프로토콜/포트</th>'
           '<th align="left">동작</th><th align="left">목적</th></tr>'
           '<tr><td>100</td><td>allow-lb-to-web</td><td>130.211.0.0/22<br/>35.191.0.0/16</td>'
           '<td>web</td><td>tcp:80</td><td style="color:#34A853"><b>허용</b></td>'
           '<td>External LB → WEB (+헬스체크)</td></tr>'
           '<tr style="background:#FAFAFA"><td>110</td><td>allow-web-to-was</td>'
           '<td>tag: <b>web</b><br/>130.211.0.0/22, 35.191.0.0/16</td>'
           '<td>was</td><td>tcp:8080</td><td style="color:#34A853"><b>허용</b></td>'
           '<td>Internal LB → WAS (+헬스체크)</td></tr>'
           '<tr><td>120</td><td>allow-was-to-sql</td><td>tag: <b>was</b></td>'
           '<td>(PSA 대역)</td><td>tcp:3306</td><td style="color:#34A853"><b>허용</b></td>'
           '<td>WAS → Cloud SQL (JDBC)</td></tr>'
           '<tr style="background:#FAFAFA"><td>130</td><td>allow-was-to-redis</td>'
           '<td>tag: <b>was</b></td><td>(Memorystore)</td><td>tcp:6379</td>'
           '<td style="color:#34A853"><b>허용</b></td><td>WAS → Redis 세션</td></tr>'
           '<tr><td>200</td><td>allow-iap-ssh</td><td><b>35.235.240.0/20</b></td>'
           '<td>web, was, bastion</td><td>tcp:22</td><td style="color:#34A853"><b>허용</b></td>'
           '<td>IAP TCP Forwarding 관리 접속</td></tr>'
           '<tr style="background:#FAFAFA"><td>300</td><td>allow-bastion-ssh</td>'
           '<td>tag: <b>bastion</b></td><td>web, was</td><td>tcp:22</td>'
           '<td style="color:#34A853"><b>허용</b></td><td>Bastion → 내부 서버</td></tr>'
           '<tr><td>1000</td><td>allow-onprem-vpn</td><td>192.168.0.0/16</td>'
           '<td>was</td><td>tcp:3306</td><td style="color:#34A853"><b>허용</b></td>'
           '<td>온프레미스 MySQL 복제 (HA VPN)</td></tr>'
           '<tr style="background:#FEF4F3"><td><b>65534</b></td><td><b>deny-all-ingress</b></td>'
           '<td>0.0.0.0/0</td><td>(전체)</td><td>all</td>'
           '<td style="color:#EA4335"><b>거부</b></td>'
           '<td><b>명시 허용 외 모든 인바운드 차단</b></td></tr></table>'
           '<br/>※ <b>Tag 기반 설계 이유</b> — IP 대역을 직접 쓰면 서브넷 변경·오토스케일 시 규칙을 '
           '매번 수정해야 한다. Network Tag(또는 Service Account)를 대상으로 삼으면 '
           '<b>인스턴스가 늘어나도 규칙은 그대로</b> 유지된다.'
           '<br/>※ GCP 방화벽은 <b>상태 저장(stateful)</b> 이므로 응답 트래픽을 위한 아웃바운드 규칙은 '
           '별도로 필요하지 않다. 아웃바운드는 기본 허용이며, 필요 시 Egress 규칙으로 추가 제한한다.',
           fs=11)

    # ---- admin access path
    p.box('ap', 1380, 552, 750, 356, '관리자 접근 경로 (Zero Trust)', stroke=BLUE, fill=BLUE_F,
          dashed=0, fs=13)
    ap = [(1480, 604, 'Cloud Console', '관리자\n(회사 / 승인 재택 IP)'),
          (1690, 604, 'Cloud IAM', 'Google 계정\n+ MFA (2단계)'),
          (1930, 604, 'BeyondCorp', 'IAP TCP Forwarding\ngcloud compute ssh --tunnel'),
          (1590, 724, 'Compute Engine', 'Bastion (mgmt-subnet)\nOS Login · 세션 로깅'),
          (1900, 724, 'Compute Engine', 'WEB / WAS VM\n(공인 IP 없음)')]
    for i, (cx, y, ic, lb) in enumerate(ap):
        p.icon(f'ap{i}', ic, cx, y, lb, ih=40, lw=240, lfs=10)
    p.edge('ea0', 'ap0', 'ap1', '', exit=(1, 0.5), entry=(0, 0.5))
    p.edge('ea1', 'ap1', 'ap2', '인증/인가', exit=(1, 0.5), entry=(0, 0.5))
    p.edge('ea2', 'ap2', 'ap3', ':22 터널', exit=(0.5, 1), entry=(0.5, 0))
    p.edge('ea3', 'ap3', 'ap4', '', exit=(1, 0.5), entry=(0, 0.5))
    p.note('apn', 1398, 818, 714, 78,
           '<b>IAP 를 쓰는 이유</b> — Bastion 에 공인 IP + 22 포트를 열면 전 세계 스캐너의 '
           '무차별 대입 공격 대상이 된다. IAP 는 Google 인증을 통과한 사용자에게만 터널을 열어주므로 '
           '<b>공인 IP 자체가 불필요</b>하고, 모든 접속이 Audit Log 에 남아 추적 가능하다.', fs=11)

    p.note('res', 50, 936, 2080, 250,
           '<b style="font-size:13px">기술 의사결정 요약 (발표 Q&amp;A 대비)</b>'
           '<table style="font-size:11px;border-collapse:collapse;width:100%;margin-top:6px">'
           '<tr style="background:#F1F3F4"><th align="left">쟁점</th><th align="left">선택</th>'
           '<th align="left">근거</th></tr>'
           '<tr><td>WEB–WAS 연동</td><td><b>mod_proxy (HTTP)</b></td>'
           '<td>AJP 는 Tomcat 9 에서 기본 비활성 + Ghostcat(CVE-2020-1938) 이력. '
           'mod_jk 는 별도 커넥터 설치·설정 필요. HTTP 는 Internal <b>L7</b> LB 와 그대로 호환된다.</td></tr>'
           '<tr style="background:#FAFAFA"><td>Internal LB 종류</td>'
           '<td><b>Internal Application LB (L7)</b></td>'
           '<td>URL 기반 라우팅과 <b>HTTP 응답 본문 헬스체크</b>가 가능하다. L4 Network LB 는 '
           'TCP 포트 생존만 확인하므로 "프로세스는 살아있고 앱은 죽은" 상태를 걸러내지 못한다.</td></tr>'
           '<tr><td>세션 관리</td><td><b>Stateless + Redis</b></td>'
           '<td>Sticky Session 은 특정 WAS 에 부하가 쏠리고, 오토스케일 축소 시 세션이 유실된다. '
           'Tomcat 기본 세션 클러스터링은 <b>멀티캐스트</b> 기반인데 GCP VPC 는 유니캐스트만 지원한다.</td></tr>'
           '<tr style="background:#FAFAFA"><td>WEB/WAS 이중화</td><td><b>Regional MIG</b></td>'
           '<td>개별 VM 은 장애 시 수동 복구가 필요하다. Regional MIG 는 3개 Zone 분산 + 자동 복구 + '
           '오토스케일 + 롤링 업데이트/롤백을 모두 제공한다.</td></tr>'
           '<tr><td>DB 접근</td><td><b>Private IP 전용</b></td>'
           '<td>Public IP 를 부여하면 승인 네트워크 설정 실수 한 번으로 DB 가 인터넷에 노출된다. '
           'Private Service Access 는 공인 IP 자체를 만들지 않는다.</td></tr>'
           '<tr style="background:#FAFAFA"><td>SSL 종료 위치</td><td><b>External LB</b></td>'
           '<td>Google-managed 인증서로 갱신이 자동화되고, 백엔드 VM 의 CPU 부담(SSL 연산)이 줄며, '
           '인증서를 VM 이미지에 넣지 않아도 되어 관리 지점이 하나로 모인다.</td></tr></table>',
           fill='#FFFFFF', stroke=GREY, fs=11)
    return p
