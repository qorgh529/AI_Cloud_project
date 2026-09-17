# -*- coding: utf-8 -*-
from lib import Page, BLUE, RED, YEL, GRN, GREY, INK

BLUE_F, GRN_F, YEL_F, RED_F = '#F5F9FF', '#F2FBF5', '#FFFBF0', '#FEF4F3'


def build():
    p = Page('③ 백업 · 재해복구(DR) 상세', 2180, 1290)
    p.text('t1', 50, 20, 1600, 32, '백업 · 재해복구(DR) 상세 설계', fs=23, bold=1, align='left')
    p.text('t2', 50, 56, 1900, 22,
           '"백업은 받는 것이 아니라 복구되는 것이다" — 모든 백업은 분기 1회 복원 훈련으로 유효성을 검증한다.',
           fs=13, color=GREY, align='left')

    # ---------- track 1 : VM
    p.box('b1', 50, 100, 1020, 290, '① VM 백업  —  Compute Engine', stroke=GRN, fill=GRN_F,
          dashed=0, fs=13)
    t1 = [(160, 'Compute Engine', 'WEB / WAS VM\nBoot Disk + Data Disk'),
          (400, 'Persistent Disk', 'Snapshot Schedule\n매일 03:00 KST · 증분'),
          (650, 'Cloud Storage', '스냅샷 저장소\n(멀티리전 · 자동 관리)'),
          (900, 'Cloud Deployment Manager', 'Machine Image\n골든 이미지 → Template')]
    for i, (cx, ic, lb) in enumerate(t1):
        p.icon(f'v{i}', ic, cx, 160, lb, ih=44, lw=230, lfs=11)
    for i in range(3):
        p.edge(f'ev{i}', f'v{i}', f'v{i+1}', '', exit=(1, 0.5), entry=(0, 0.5), color=GRN)
    p.note('b1n', 70, 268, 980, 108,
           '<b>보존 정책</b>: 일 7개 · 주 4개 · 월 12개 (자동 삭제)  |  <b>위치</b>: asia (멀티리전) — '
           '리전 장애에도 스냅샷 생존<br/>'
           '<b>복구 절차</b>: 스냅샷 → 디스크 생성 → 인스턴스 연결 (단일 VM) / '
           '스냅샷 → 이미지 → <b>Instance Template 교체 → MIG 롤링 업데이트</b> (전체 Tier)<br/>'
           '<b>핵심</b>: MIG 환경의 VM은 <b>일회용(Cattle)</b> 이다. 개별 VM 복구보다 '
           '<b>검증된 골든 이미지로 재생성</b>하는 편이 빠르고 안전하다 — 스냅샷은 데이터 디스크 보호용.',
           fs=11)

    # ---------- track 2 : DB
    p.box('b2', 1110, 100, 1020, 290, '② DB 백업  —  Cloud SQL for MySQL', stroke=BLUE,
          fill=BLUE_F, dashed=0, fs=13)
    t2 = [(1220, 'Cloud SQL', 'Cloud SQL Primary\nDB: petclinic'),
          (1450, 'Persistent Disk', '자동 백업\n매일 03:30 KST · 7일 보존'),
          (1690, 'Cloud SQL', 'PITR (binlog)\n7일 내 임의 시점 복구'),
          (1950, 'Cloud SQL', 'Read Replica\n백업 부하 오프로드')]
    for i, (cx, ic, lb) in enumerate(t2):
        p.icon(f'd{i}', ic, cx, 160, lb, ih=44, lw=230, lfs=11)
    for i in range(3):
        p.edge(f'ed{i}', f'd{i}', f'd{i+1}', '', exit=(1, 0.5), entry=(0, 0.5), color=BLUE)
    p.note('b2n', 1130, 268, 980, 108,
           '<b>왜 자동 백업만으로 부족한가</b> — Cloud SQL 자동 백업은 <b>인스턴스에 종속</b>된다. '
           '인스턴스가 삭제되면 백업도 함께 사라지고, 다른 프로젝트·리전·온프레미스로 옮길 수 없다.<br/>'
           '따라서 요구사항의 <b>"별도 파일로 최종 보관"</b> 을 만족하려면 아래 ③ Export 파이프라인이 '
           '반드시 필요하다.<br/>'
           '<b>운영 주의</b>: Export 는 인스턴스에 부하를 준다 → <b>Read Replica 대상</b>으로 수행하고 '
           '사용량이 가장 적은 새벽 시간대에 실행한다.', fs=11)

    # ---------- track 3 : export pipeline
    p.box('b3', 50, 420, 2080, 300,
          '③ 파일 백업 파이프라인  —  "매일 사용량이 적은 시간대에 실행, 별도 파일로 최종 보관" 요구사항 충족',
          stroke=YEL, fill=YEL_F, dashed=0, fs=13, fc='#8A6D00')
    t3 = [(160, 'Cloud Scheduler', 'Cloud Scheduler\ncron: 0 4 * * * (KST)'),
          (420, 'Pub Sub', 'Pub/Sub Topic\nsql-export-trigger'),
          (690, 'Cloud Functions', 'Cloud Functions\nsqladmin.export API 호출'),
          (960, 'Cloud SQL', 'Cloud SQL Export\n.sql.gz / CSV 덤프'),
          (1240, 'Cloud Storage', 'GCS 백업 버킷\nDual-region (KR+JP)'),
          (1520, 'Key Management Service', 'CMEK 암호화\n+ Retention Lock'),
          (1810, 'Cloud VPN', 'HA VPN → 온프레미스\nrsync / MySQL 복제'),
          (2040, 'Cloud Monitoring', '실패 알림\nSev2')]
    for i, (cx, ic, lb) in enumerate(t3):
        p.icon(f'x{i}', ic, cx, 480, lb, ih=42, lw=240, lfs=10)
    for i in range(6):
        p.edge(f'ex{i}', f'x{i}', f'x{i+1}', '', exit=(1, 0.5), entry=(0, 0.5), color='#8A6D00')
    p.edge('ex_al', 'x2', 'x7', '실패 시', exit=(0.5, 0), entry=(0.5, 0), dashed=1, color=RED, sw=1)
    p.note('b3n', 70, 600, 2040, 100,
           '<b>GCS 수명주기 (Lifecycle) — 비용과 보관기간의 균형</b>&nbsp;&nbsp;'
           'Standard <span style="color:#5F6368">(0~30일, 즉시 복구용)</span> → '
           '<b>Nearline</b> <span style="color:#5F6368">(30일~, 월 1회 접근)</span> → '
           '<b>Coldline</b> <span style="color:#5F6368">(90일~, 분기 1회)</span> → '
           '<b>Archive</b> <span style="color:#5F6368">(365일~, 법정 보관)</span> → 2,555일(7년) 후 삭제<br/>'
           '<b>랜섬웨어·실수 삭제 대비</b>: Object Versioning 활성화 + <b>Bucket Lock(보존 정책)</b> 으로 '
           '관리자조차 보존기간 내 삭제 불가하게 설정. 백업 버킷은 <b>별도 서비스 계정</b>만 쓰기 가능하고, '
           '운영 VM의 서비스 계정에는 <code>objectCreator</code> 만 부여해 기존 백업 덮어쓰기를 차단한다.',
           fs=11)

    # ---------- DR
    p.box('b4', 50, 750, 1380, 380,
          '④ 재해복구 (DR)  —  asia-northeast1 (Tokyo)  ·  Warm Standby / Pilot Light',
          stroke=RED, fill=RED_F, dashed=0, fs=13)
    t4 = [(180, 'Cloud SQL', 'Cross-region\nRead Replica'),
          (430, 'Cloud Storage', 'Dual-region Bucket\n자동 복제'),
          (680, 'Compute Engine', 'Pilot-light MIG\n(target size 0)'),
          (930, 'Cloud Load Balancing', 'LB / 방화벽\n사전 생성'),
          (1230, 'Cloud DNS', 'Cloud DNS\n평시 TTL 300s')]
    for i, (cx, ic, lb) in enumerate(t4):
        p.icon(f'r{i}', ic, cx, 810, lb, ih=42, lw=220, lfs=10)
    p.note('b4n', 70, 930, 1340, 185,
           '<b>DR 전환 절차 (목표 RTO 4시간 이내)</b>'
           '<br/>① <b>장애 인지</b> — Uptime Check 연속 실패 + 리전 상태 대시보드 확인 (0~10분)'
           '<br/>② <b>전환 의사결정</b> — 사전 정의된 판단 기준(리전 장애 30분 이상 지속)에 따라 선언 (10~20분)'
           '<br/>③ <b>DB 승격</b> — Tokyo Read Replica 를 독립 Primary 로 <b>Promote</b> (20~40분)'
           '<br/>④ <b>애플리케이션 기동</b> — Pilot-light MIG 크기를 0 → 2 로 조정, 골든 이미지로 자동 부팅 (40~70분)'
           '<br/>⑤ <b>DNS 전환</b> — A 레코드를 Tokyo LB IP 로 변경, TTL 을 30초로 하향 (70~90분)'
           '<br/>⑥ <b>검증</b> — PetClinic 로그인·조회·등록 기능 및 DB 쓰기 확인 후 서비스 재개 선언 (~120분)'
           '<br/><b>사전 준비가 RTO 를 결정한다</b> — VPC·서브넷·방화벽·LB·Instance Template 을 '
           '평시에 Terraform 으로 <b>미리 생성</b>해 두면, 장애 시에는 "크기 조정 + DNS 변경"만 남는다.',
           fs=11)

    # ---------- RPO/RTO table
    p.note('rpo', 1470, 750, 660, 380,
           '<b style="font-size:13px">복구 목표 (RPO / RTO) 정의</b>'
           '<table style="font-size:11px;border-collapse:collapse;width:100%;margin-top:6px">'
           '<tr style="background:#F1F3F4"><th align="left">장애 시나리오</th>'
           '<th align="left">RPO</th><th align="left">RTO</th><th align="left">복구 수단</th></tr>'
           '<tr><td>VM 1대 장애</td><td>0</td><td>~3분</td><td>MIG 자동 복구 + LB 제외</td></tr>'
           '<tr><td>Zone 장애</td><td>0</td><td>~5분</td><td>Regional MIG + Cloud SQL HA Failover</td></tr>'
           '<tr><td>애플리케이션 배포 실패</td><td>0</td><td>~10분</td><td>MIG 롤링 <b>Rollback</b></td></tr>'
           '<tr><td>DB 논리적 손상<br/>(잘못된 UPDATE/DELETE)</td><td>~1분</td><td>~1시간</td>'
           '<td>Cloud SQL <b>PITR</b> (시점 복구)</td></tr>'
           '<tr><td>DB 인스턴스 삭제</td><td>~24시간</td><td>~2시간</td>'
           '<td>GCS Export 파일 → 신규 인스턴스 Import</td></tr>'
           '<tr><td>OS/디스크 손상</td><td>~24시간</td><td>~30분</td><td>PD 스냅샷 복원</td></tr>'
           '<tr><td><b>리전 전체 장애</b></td><td>~15분</td><td><b>~4시간</b></td>'
           '<td>Tokyo Replica 승격 + Pilot-light + DNS</td></tr>'
           '<tr><td>랜섬웨어 / 내부자 삭제</td><td>~24시간</td><td>~4시간</td>'
           '<td>Versioning + Bucket Lock 백업 복원</td></tr></table>'
           '<br/><b>검증 계획</b> — 분기 1회 DR 훈련일을 지정해 ③~⑥ 절차를 실제 수행하고, '
           '측정된 RTO 를 기록해 목표와의 차이를 개선한다. <b>훈련하지 않은 DR 은 DR 이 아니다.</b>',
           fs=11)

    p.note('warn', 50, 1160, 2080, 90,
           '<b style="font-size:13px;color:#EA4335">⚠ 흔한 실수 (Anti-pattern) — 발표 질의응답 대비</b>'
           '<br/>• <b>"HA 구성했으니 백업은 필요 없다"</b> → HA 는 <b>인프라 장애</b> 대비이고 백업은 '
           '<b>데이터 손상·실수·랜섬웨어</b> 대비다. 잘못된 DELETE 는 Standby 에도 즉시 복제된다.'
           '<br/>• <b>"스냅샷을 받았으니 안전하다"</b> → 스냅샷은 같은 프로젝트에 있다. 프로젝트 자체가 '
           '삭제되면 함께 사라지므로, 별도 버킷(+Bucket Lock)으로의 <b>파일 반출</b>이 최종 방어선이다.'
           '<br/>• <b>"복구 테스트는 나중에"</b> → 백업 파일 손상·권한 누락·스키마 불일치는 '
           '실제 복구를 시도해야만 드러난다.', fill='#FEF4F3', stroke=RED, fs=11)
    return p
