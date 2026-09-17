# -*- coding: utf-8 -*-
from lib import Page, BLUE, RED, YEL, GRN, GREY, INK

BLUE_F, GRN_F, YEL_F, RED_F = '#F5F9FF', '#F2FBF5', '#FFFBF0', '#FEF4F3'


def build():
    p = Page('② 모니터링 · 로깅 상세', 2180, 1080)
    p.text('t1', 50, 18, 1600, 32, '모니터링 · 로깅 상세 설계  (Cloud Operations Suite)',
           fs=23, bold=1, align='left')
    p.text('t2', 50, 54, 1900, 22,
           '수집(Ops Agent) → 저장·분석(Monitoring · Logging) → 판단(SLO · 알림 정책) → 전달(알림 채널 · 장기보관) → 조치',
           fs=13, color=GREY, align='left')

    # ── ① sources ────────────────────────────────────────────────────────────
    p.box('src', 50, 100, 500, 600, '① 수집 대상 (Data Source)', stroke=GRN, fill=GRN_F,
          dashed=0, fs=13)
    srcs = [('Compute Engine', 150, 'WEB VM  (Apache 2.4)\naccess/error log · mod_status'),
            ('Compute Engine', 258, 'WAS VM  (Tomcat 9)\ncatalina.out · JVM Heap/GC · thread'),
            ('Cloud SQL', 366, 'Cloud SQL (MySQL)\nslow query · connection · replication lag'),
            ('Cloud Load Balancing', 474, 'External / Internal LB\n요청수 · 5xx · 백엔드 지연')]
    for i, (ic, y, lb) in enumerate(srcs):
        p.icon(f's{i}', ic, 175, y, lb, ih=42, lw=300, lfs=11)
    p.note('src_n', 68, 578, 464, 110,
           '<b>Ops Agent</b> (구 Monitoring + Logging Agent 통합)를 <b>Instance Template</b> 의 '
           'startup-script 에 포함해 MIG 신규 VM 에 자동 설치.<br/>'
           '<code>/etc/google-cloud-ops-agent/config.yaml</code> 에 Apache · Tomcat(JVM) receiver '
           '를 등록하여 <b>애플리케이션 메트릭</b>까지 수집한다.', fs=11)

    # ── ② platform ───────────────────────────────────────────────────────────
    p.box('plat', 600, 100, 470, 600, '② 저장 · 분석 (Managed Platform)', stroke=BLUE,
          fill=BLUE_F, dashed=0, fs=13)
    p.icon('m_mon', 'Cloud Monitoring', 835, 160,
           'Cloud Monitoring\n시계열 메트릭 · Metrics Explorer · 대시보드 · Uptime Check',
           ih=48, lw=390)
    p.icon('m_log', 'Cloud Logging', 835, 290,
           'Cloud Logging\n_Default / _Required 버킷 · Log Explorer · Log-based Metrics',
           ih=48, lw=390)
    p.icon('m_apm', 'Trace', 725, 430, 'Cloud Trace\n분산 추적 · p50/p95/p99', ih=42, lw=200)
    p.icon('m_prof', 'Profiler', 945, 430, 'Cloud Profiler\nCPU / Heap 프로파일', ih=42, lw=200)
    p.icon('m_err', 'Error Reporting', 835, 560,
           'Error Reporting  —  예외 그룹핑 · 신규 오류 즉시 알림', ih=40, lw=420)

    # ── ③ decision / routing ─────────────────────────────────────────────────
    p.box('out', 1120, 100, 500, 600, '③ 판단 · 라우팅', stroke=YEL, fill=YEL_F, dashed=0, fs=13,
          fc='#8A6D00')
    p.icon('o_slo', 'Cloud Monitoring', 1250, 150, 'SLO / SLI 정의\n가용성 99.9% · p95 500ms',
           ih=42, lw=225)
    p.icon('o_alert', 'Error Reporting', 1490, 150, 'Alerting Policy\nBurn-rate 기반', ih=42, lw=195)
    p.note('o_tbl', 1140, 255, 460, 285,
           '<b>주요 알림 정책 (Alerting Policy)</b>'
           '<table style="font-size:10.5px;border-collapse:collapse;width:100%;margin-top:4px">'
           '<tr style="background:#F1F3F4"><th align="left">지표</th><th align="left">임계</th>'
           '<th align="left">등급</th></tr>'
           '<tr><td>LB 5xx 비율</td><td>&gt; 1% (5분)</td><td>Sev1</td></tr>'
           '<tr><td>Uptime Check 실패</td><td>2회 연속</td><td>Sev1</td></tr>'
           '<tr><td>MIG 정상 인스턴스</td><td>&lt; 2대</td><td>Sev1</td></tr>'
           '<tr><td>Cloud SQL CPU</td><td>&gt; 80% (10분)</td><td>Sev2</td></tr>'
           '<tr><td>복제 지연 (replica lag)</td><td>&gt; 60초</td><td>Sev2</td></tr>'
           '<tr><td>VM 메모리 / 디스크</td><td>&gt; 85%</td><td>Sev2</td></tr>'
           '<tr><td>Tomcat JVM Old Gen</td><td>&gt; 85%</td><td>Sev2</td></tr>'
           '<tr><td>스냅샷 / 백업 Job 실패</td><td>1회</td><td>Sev2</td></tr>'
           '<tr><td>Cloud Armor 차단 급증</td><td>기준선 5배</td><td>Sev3</td></tr></table>', fs=11)
    p.icon('o_sink', 'Cloud Logging', 1370, 580,
           'Log Router (Sink)  —  포함 / 제외 필터로 비용 최적화', ih=40, lw=430)

    # ── ④ destinations ───────────────────────────────────────────────────────
    p.box('dst', 1670, 100, 460, 600, '④ 전달 · 장기보관', stroke=RED, fill=RED_F, dashed=0, fs=13)
    dsts = [('Cloud Console', 150, '알림 채널\nEmail · Google Chat · Slack · SMS · Mobile App'),
            ('Cloud Monitoring', 285, '통합 관제 대시보드\n3-Tier 를 한 화면에서 관제'),
            ('BigQuery', 420, 'BigQuery\n로그 SQL 분석 · 주간 리포트'),
            ('Cloud Storage', 555, 'GCS 로그 아카이브\n365일 보관 (감사 대응)')]
    for i, (ic, y, lb) in enumerate(dsts):
        p.icon(f'd{i}', ic, 1900, y, lb, ih=42, lw=300, lfs=11)

    for i in range(4):
        p.edge(f'e_s{i}', f's{i}', 'plat', '', exit=(1, 0.5), entry=(0, 0.2 + i * 0.2), sw=2)
    p.edge('e_p1', 'm_mon', 'o_slo', '메트릭', exit=(1, 0.5), entry=(0, 0.5))
    p.edge('e_p2', 'm_log', 'o_sink', '로그', exit=(1, 0.5), entry=(0, 0.5))
    p.edge('e_p3', 'o_slo', 'o_alert', '위반 감지', exit=(1, 0.5), entry=(0, 0.5))
    p.edge('e_p4', 'o_alert', 'd0', '알림 발송', exit=(1, 0.5), entry=(0, 0.5), color=RED)
    p.edge('e_p5', 'o_slo', 'd1', '지표 시각화', exit=(0.5, 1), entry=(0, 0.5), dashed=1, color=GREY)
    p.edge('e_p6', 'o_sink', 'd2', 'BigQuery 내보내기', exit=(1, 0.5), entry=(0, 0.5), dashed=1,
           color=GREY)
    p.edge('e_p7', 'o_sink', 'd3', 'GCS 내보내기', exit=(1, 0.5), entry=(0, 0.5), dashed=1,
           color=GREY)

    # ── bottom strip ─────────────────────────────────────────────────────────
    p.note('flow', 50, 730, 2080, 82,
           '<b style="font-size:13px">트러블슈팅 시나리오 — 사용자 "페이지가 느려요"</b><br/>'
           '① Monitoring 대시보드에서 <b>LB 백엔드 지연 p95 급증</b> 확인 → ② Cloud Trace 로 느린 구간이 '
           '<b>WAS → Cloud SQL</b> 임을 특정 → ③ Cloud SQL 메트릭에서 <b>slow query · 커넥션 포화</b> 확인 → '
           '④ Cloud Logging 에서 해당 시간대 <code>catalina.out</code> 의 커넥션 풀 고갈 로그 확인 → '
           '⑤ 인덱스 추가 · HikariCP 풀 튜닝 · Read Replica 로 조회 분산 → ⑥ SLO 회복 확인 후 알림 종료',
           fill='#E8F0FE', stroke=BLUE, fs=12)

    p.note('dash', 50, 838, 690, 205,
           '<b style="font-size:13px">운영 관제 대시보드 구성</b>'
           '<br/>• <b>Row 1 — 서비스</b>: 요청수(RPS) · 지연 p50/p95/p99 · 2xx/4xx/5xx 비율'
           '<br/>• <b>Row 2 — WEB</b>: MIG 인스턴스 수 · CPU · Apache 활성 커넥션'
           '<br/>• <b>Row 3 — WAS</b>: JVM Heap/GC · Tomcat thread pool · 활성 세션(Redis)'
           '<br/>• <b>Row 4 — DB</b>: Cloud SQL CPU/Mem · 커넥션 수 · slow query · 복제 지연'
           '<br/>• <b>Row 5 — 보안</b>: Cloud Armor 차단 건수 · IAP 접속 이력'
           '<br/><br/><b>Audit Logs</b> 는 <code>_Required</code> 버킷에 400일 불변 보관 (삭제 불가).',
           fs=11)
    p.note('cost', 766, 838, 660, 205,
           '<b style="font-size:13px">비용 최적화 (관측 비용도 운영 비용이다)</b>'
           '<br/>• Cloud Logging 은 <b>수집량 과금</b> — Log Router <b>제외 필터</b>로 LB 헬스체크 로그·'
           'Apache 정적자산 200 응답 등 저가치 로그를 사전 제외'
           '<br/>• <code>_Default</code> 버킷 보존 30일 유지, 감사·규제 대상 로그만 GCS Archive 로 이관'
           '<br/>• 대량 원시 로그는 BigQuery 로 보내고 <b>파티션 만료</b> 설정'
           '<br/>• Uptime Check 는 필요한 리전만 선택 (전 리전 체크는 불필요한 비용)'
           '<br/>• 커스텀 메트릭은 <b>라벨 카디널리티</b> 주의 — VM ID 라벨 남발 시 시계열 폭증', fs=11)
    p.note('why', 1452, 838, 678, 205,
           '<b style="font-size:13px">왜 이 구성인가 (설계 근거)</b>'
           '<br/>• <b>Ops Agent 필수</b> — GCP 기본 메트릭은 CPU · 네트워크 · 디스크 IOPS 뿐이다. '
           '<b>메모리 · 디스크 사용률 · 프로세스 · JVM</b> 은 에이전트 없이는 볼 수 없다.'
           '<br/>• <b>SLO 기반 알림</b> — 단순 "CPU 80%" 알림은 오탐이 많아 알림 피로를 유발한다. '
           '사용자 체감 지표의 <b>오류 예산 소진 속도</b>로 알리면 진짜 장애만 울린다.'
           '<br/>• <b>Uptime Check 별도 운영</b> — LB 헬스체크는 백엔드 생존만 본다. '
           '외부 관점의 종단 확인(DNS · 인증서 · Cloud Armor 포함)은 Uptime Check 가 담당한다.'
           '<br/>• <b>헬스체크는 포트가 아닌 HTTP 응답 확인</b> — Tomcat 은 살아있는데 DB 연결이 끊긴 '
           '상태를 걸러내려면 실제 페이지 응답을 검사해야 한다.', fs=11)
    return p
