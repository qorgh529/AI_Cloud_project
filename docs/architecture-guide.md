# GCP 3-Tier PetClinic 아키텍처 설계서

> 팀: **NOVA (GCP 1팀)** · 리전: **asia-northeast3 (Seoul)**
> 다이어그램: [`architecture/gcp-3tier-petclinic-architecture.drawio`](../architecture/gcp-3tier-petclinic-architecture.drawio)

---

## 1. 요구사항 ↔ 설계 매핑

중간프로젝트 OT(p.29~32)의 **필수 요구사항**이 아키텍처 어디에서 충족되는지 정리한다.

| # | 필수 요구사항 | 설계 반영 | 다이어그램 위치 |
|---|---|---|---|
| 1 | WEB Server 구축 (Apache v2.4~) + 정적 페이지 | `web-mig` 3대, Apache 2.4 + `index.html` | ① ② WEB Tier |
| 2 | WAS Server 구축 (Tomcat / OpenJDK) | `was-mig` 3대, Tomcat 9 + OpenJDK 17 + `petclinic.war` | ① ③ WAS Tier |
| 3 | WEB–WAS 연동 (Proxy 또는 mod_jk) | **Apache `mod_proxy` → HTTP** | ① `mod_proxy → HTTP` 간선 |
| 4 | DB 구축 및 PetClinic 연동 | Cloud SQL for MySQL 8.0, **Private IP 전용** | ① ⑤ DB Tier |
| 5 | External LB (단일 외부 진입점) | External Application LB (Global) + Managed SSL | ① Global Edge |
| 6 | **Internal LB 필수** | Internal Application LB (L7), 10.10.10.100 | ① 중앙 |
| 7 | Health Check | LB HTTP 엔드포인트 검사 + MIG Auto-healing | ① Autoscaler 블록 |
| 8 | 서비스 흐름 검증 | User → ELB → WEB → ILB → WAS → Cloud SQL | ① 상단 Service Flow |

**확장 기능(선택)** 은 3장에서 별도로 정리한다.

---

## 2. 계층별 구성

### 2.1 네트워크 (VPC / Subnet)

Custom Mode VPC `petclinic-vpc` 하나에 역할별 서브넷을 분리한다.

| 서브넷 | CIDR | 용도 | 외부 IP |
|---|---|---|---|
| `web-subnet` | 10.10.10.0/24 | Apache WEB 계층 (Regional MIG) | 없음 |
| `was-subnet` | 10.10.20.0/24 | Tomcat WAS 계층 (Regional MIG) | 없음 |
| `db-subnet` | 10.10.30.0/24 | Cloud SQL (Private Service Access) | 없음 |
| `mgmt-subnet` | 10.10.40.0/24 | Bastion · Cloud NAT · Cloud Router | 없음 |

- **모든 VM에 공인 IP를 부여하지 않는다.** 외부로 나가는 통신(패치, apt)은 Cloud NAT 경유(아웃바운드 전용).
- **Private Google Access** 를 서브넷에 활성화하여 Cloud Storage / Secret Manager / Logging 호출이 인터넷을 거치지 않게 한다.
- **Private Service Access** (VPC Peering) 로 Cloud SQL 비공개 IP를 할당한다.

### 2.2 WEB Tier

- Apache 2.4, `mod_proxy` + `mod_proxy_http` 로 Internal LB 로 리버스 프록시.
- 정적 콘텐츠(`index.html`, css/js/img)는 WEB에서 직접 처리하고, 동적 요청만 WAS 로 전달한다 → **WEB 계층을 두는 실질적 이유**를 만든다.
- Regional MIG (zone a/b/c), Autoscale 2~6, CPU 60% 기준.

```apache
# /etc/apache2/sites-available/petclinic.conf
ProxyPreserveHost On
ProxyPass        /petclinic  http://10.10.10.100:8080/petclinic
ProxyPassReverse /petclinic  http://10.10.10.100:8080/petclinic
# 정적 자산은 프록시하지 않고 Apache 가 직접 응답
ProxyPass /static !
```

### 2.3 WAS Tier

- Tomcat 9 + OpenJDK 17, `petclinic.war` 를 `$CATALINA_HOME/webapps/` 에 배포.
- **Stateless** 로 운영하고 세션은 Memorystore for Redis 에 외부화한다.
- Regional MIG (zone a/b/c), Autoscale 2~8.

### 2.4 DB Tier

- Cloud SQL for MySQL 8.0, **Regional HA**(동기 복제 Standby) + **Read Replica**.
- Public IP 미할당, `db` 스키마: `petclinic`.

PetClinic 연결 방식은 두 가지가 있으며, 본 아키텍처는 **(A) Private IP 직접 연결**을 채택한다.

```properties
# (A) 채택 — VPC 내부 Private IP 직접 연결 (Cloud SQL Proxy 불필요)
spring.datasource.url=jdbc:mysql://10.10.30.3:3306/petclinic?useSSL=true&serverTimezone=Asia/Seoul
spring.datasource.username=petclinic
spring.datasource.password=${DB_PASSWORD}   # Secret Manager 에서 주입
spring.profiles.active=mysql

# (B) 대안 — Cloud SQL Java Connector (SocketFactory). Codelab 방식.
#     VPC 밖(로컬/Cloud Shell)에서 접속하거나 IAM 인증을 쓸 때 유리하다.
# spring.datasource.url=jdbc:mysql:///petclinic?cloudSqlInstance=PROJECT:asia-northeast3:petclinic-db\
#   &socketFactory=com.google.cloud.sql.mysql.SocketFactory
```

> (A)를 택한 이유: WAS 가 이미 같은 VPC 안에 있어 Proxy/SocketFactory 계층이 불필요하고,
> 의존성과 장애 지점이 하나 줄어든다. 스키마는 PetClinic 의 `db/mysql/schema.sql`, `data.sql` 로 초기화한다.

---

## 3. 추가 제안 서비스 (클라우드 엔지니어 관점)

필수 요구사항 외에 **왜 넣는지**를 함께 정리했다. 11일 일정을 고려해 우선순위를 나눴다.

### 3.1 반드시 넣기를 권함 (Must)

| 서비스 | 목적 | 넣지 않으면 생기는 문제 |
|---|---|---|
| **Regional MIG + Autoscaler** | 3개 Zone 분산, 자동 복구, 롤링 업데이트 | 개별 VM은 장애 시 수동 복구, Zone 장애에 무방비 |
| **Cloud NAT + Cloud Router** | 공인 IP 없이 아웃바운드 | VM마다 공인 IP → 공격 표면 증가 |
| **IAP (TCP Forwarding)** | 공인 IP/22 포트 없이 SSH | Bastion 공인 IP가 무차별 대입 공격 대상 |
| **Secret Manager** | DB 자격증명 분리 | 비밀번호가 startup-script·이미지에 평문 잔존 |
| **Cloud Monitoring + Logging (Ops Agent)** | 메모리·디스크·JVM 가시성 | 기본 메트릭엔 메모리가 없어 장애 원인 분석 불가 |
| **PD Snapshot Schedule / Cloud SQL 자동 백업** | 데이터 보호 | 실수 삭제·손상 시 복구 수단 없음 |
| **Cloud Armor** | WAF · DDoS · 지역 제한 | LB가 전 세계에 그대로 노출 |

### 3.2 넣으면 좋음 (Should)

| 서비스 | 목적 |
|---|---|
| **Memorystore for Redis** | Tomcat 세션 클러스터링. GCP VPC는 **멀티캐스트 미지원**이라 Tomcat 기본 세션 복제가 동작하지 않는다 |
| **Cloud DNS + Google-managed SSL** | 도메인 접속 및 인증서 자동 갱신 |
| **Cloud CDN** | 정적 콘텐츠 캐싱 → WEB 부하·응답시간 감소 |
| **Cloud SQL Read Replica** | 읽기 분산 + 백업/Export 부하 오프로드 |
| **Cloud KMS (CMEK)** | PD·GCS·Cloud SQL 고객 관리 키 암호화 |
| **Cloud Storage (버전 관리 + Lifecycle)** | WAR 아티팩트, 백업 아카이브 |
| **Cloud Scheduler + Pub/Sub + Cloud Functions** | DB Export 자동화 (별도 파일 보관 요구사항) |
| **Cloud Trace / Profiler / Error Reporting** | WAS 지연·예외 근본 원인 분석 |

### 3.3 여유가 되면 (Could)

| 서비스 | 목적 |
|---|---|
| **Security Command Center** | 구성 오류·취약점 상시 탐지 |
| **Cloud Build + Artifact Registry** | WAR 빌드 → MIG 롤링 업데이트 자동화 |
| **Terraform (IaC)** | 인프라 재현성 확보, DR 구축 시간 단축 |
| **Cross-region Read Replica (Tokyo)** | 리전 장애 대비 DR |
| **Cloud VPN (HA VPN)** | 온프레미스 MySQL 복제 / 파일 백업 |
| **VPC Service Controls** | 데이터 반출 경계 설정 |

---

## 4. 백업 설계

### 4.1 대상별 백업 정책

| 대상 | 방식 | 주기 | 보존 | 저장 위치 |
|---|---|---|---|---|
| VM 디스크 | PD Snapshot Schedule | 매일 03:00 KST (증분) | 일 7 / 주 4 / 월 12 | asia (멀티리전) |
| VM 구성 | Machine Image → Instance Template | 변경 시 | 최근 3개 | 프로젝트 |
| DB | Cloud SQL 자동 백업 | 매일 03:30 KST | 7일 | Cloud SQL 관리 |
| DB (시점 복구) | PITR (binary log) | 연속 | 7일 | Cloud SQL 관리 |
| **DB (파일 반출)** | **Cloud SQL Export → GCS** | **매일 04:00 KST** | **7년** | **Dual-region 버킷** |
| 애플리케이션 로그 | Log Router Sink → GCS | 연속 | 365일 | GCS Archive |
| 온프레미스 사본 | MySQL Replication + rsync (HA VPN) | 연속 / 매일 | 사이트 정책 | 온프레미스 |

### 4.2 GCS 수명주기 (Lifecycle)

```
Standard (0~30일)  →  Nearline (30일~)  →  Coldline (90일~)  →  Archive (365일~)  →  2,555일 후 삭제
```

- **Object Versioning** 활성화 — 덮어쓰기/삭제 시 이전 버전 보존
- **Bucket Lock (보존 정책)** — 보존기간 내에는 관리자도 삭제 불가 → 랜섬웨어·내부자 위협 방어
- 운영 VM의 서비스 계정에는 `roles/storage.objectCreator` 만 부여 (기존 백업 덮어쓰기 차단)

### 4.3 RPO / RTO

| 장애 시나리오 | RPO | RTO | 복구 수단 |
|---|---|---|---|
| VM 1대 장애 | 0 | ~3분 | MIG Auto-healing + LB 제외 |
| Zone 장애 | 0 | ~5분 | Regional MIG + Cloud SQL HA Failover |
| 배포 실패 | 0 | ~10분 | MIG 롤링 Rollback |
| DB 논리적 손상 | ~1분 | ~1시간 | Cloud SQL **PITR** |
| DB 인스턴스 삭제 | ~24시간 | ~2시간 | GCS Export 파일 → 신규 인스턴스 Import |
| OS/디스크 손상 | ~24시간 | ~30분 | PD 스냅샷 복원 |
| **리전 전체 장애** | ~15분 | **~4시간** | Tokyo Replica 승격 + Pilot-light + DNS 전환 |
| 랜섬웨어 / 내부자 삭제 | ~24시간 | ~4시간 | Versioning + Bucket Lock 백업 복원 |

> **HA ≠ 백업.** HA는 인프라 장애 대비이고, 백업은 데이터 손상·실수·랜섬웨어 대비다.
> 잘못된 `DELETE` 는 Standby 에도 즉시 복제된다.

### 4.4 DR 전환 절차 (목표 RTO 4시간)

1. **장애 인지** — Uptime Check 연속 실패 + 리전 상태 확인 (0~10분)
2. **전환 의사결정** — 리전 장애 30분 이상 지속 시 선언 (10~20분)
3. **DB 승격** — Tokyo Read Replica 를 독립 Primary 로 Promote (20~40분)
4. **애플리케이션 기동** — Pilot-light MIG 크기 0 → 2 (40~70분)
5. **DNS 전환** — A 레코드를 Tokyo LB IP로, TTL 30초로 하향 (70~90분)
6. **검증** — PetClinic 조회·등록 및 DB 쓰기 확인 후 서비스 재개 (~120분)

VPC·서브넷·방화벽·LB·Instance Template 을 **평시에 Terraform 으로 미리 생성**해 두면 장애 시에는 "크기 조정 + DNS 변경"만 남는다.

---

## 5. 모니터링 설계

### 5.1 수집

- **Ops Agent** 를 Instance Template 의 startup-script 에 포함 → MIG 신규 VM에 자동 설치
- `/etc/google-cloud-ops-agent/config.yaml` 에 Apache · Tomcat(JVM) receiver 등록

```yaml
metrics:
  receivers:
    apache:  { type: apache,  server_status_url: http://localhost/server-status?auto }
    tomcat:  { type: tomcat,  endpoint: localhost:8050 }
  service:
    pipelines:
      default: { receivers: [hostmetrics, apache, tomcat] }
```

### 5.2 알림 정책

| 지표 | 임계 | 등급 | 채널 |
|---|---|---|---|
| LB 5xx 비율 | > 1% (5분) | Sev1 | SMS + Slack + Email |
| Uptime Check 실패 | 2회 연속 | Sev1 | SMS + Slack + Email |
| MIG 정상 인스턴스 | < 2대 | Sev1 | SMS + Slack |
| Cloud SQL CPU | > 80% (10분) | Sev2 | Slack + Email |
| 복제 지연 (replica lag) | > 60초 | Sev2 | Slack + Email |
| VM 메모리 / 디스크 | > 85% | Sev2 | Slack |
| Tomcat JVM Old Gen | > 85% | Sev2 | Slack |
| 스냅샷 / 백업 Job 실패 | 1회 | Sev2 | Slack + Email |
| Cloud Armor 차단 급증 | 기준선 5배 | Sev3 | Email |

**SLO**: 가용성 99.9%, 지연 p95 < 500ms. 오류 예산 **소진 속도(burn-rate)** 기반으로 알린다
— 단순 "CPU 80%" 알림은 오탐이 많아 알림 피로를 유발한다.

### 5.3 로그

- `_Default` 버킷 30일 보존, 감사 대상은 GCS Archive 365일 이관
- **제외 필터**로 LB 헬스체크 로그·정적자산 200 응답 제거 (Logging 은 수집량 과금)
- `_Required` 버킷의 Audit Logs 는 400일 불변 보관 (삭제 불가)

---

## 6. 보안 설계

### 6.1 방화벽 규칙 (Network Tag 기반, 최소 권한)

| 우선순위 | 규칙명 | 소스 | 대상 태그 | 프로토콜/포트 | 동작 |
|---|---|---|---|---|---|
| 100 | `allow-lb-to-web` | 130.211.0.0/22, 35.191.0.0/16 | `web` | tcp:80 | 허용 |
| 110 | `allow-web-to-was` | tag:`web`, 130.211.0.0/22, 35.191.0.0/16 | `was` | tcp:8080 | 허용 |
| 120 | `allow-was-to-sql` | tag:`was` | (PSA 대역) | tcp:3306 | 허용 |
| 130 | `allow-was-to-redis` | tag:`was` | (Memorystore) | tcp:6379 | 허용 |
| 200 | `allow-iap-ssh` | **35.235.240.0/20** | `web`,`was`,`bastion` | tcp:22 | 허용 |
| 300 | `allow-bastion-ssh` | tag:`bastion` | `web`,`was` | tcp:22 | 허용 |
| 1000 | `allow-onprem-vpn` | 192.168.0.0/16 | `was` | tcp:3306 | 허용 |
| **65534** | **`deny-all-ingress`** | 0.0.0.0/0 | (전체) | all | **거부** |

- `130.211.0.0/22`, `35.191.0.0/16` 은 **Google 헬스체크 프로버 대역**이다. 누락하면 백엔드가 전부 UNHEALTHY 가 된다.
- `35.235.240.0/20` 은 **IAP TCP Forwarding 대역**이다.
- Tag 기반으로 설계해야 오토스케일로 인스턴스가 늘어나도 규칙 수정이 필요 없다.
- GCP 방화벽은 **상태 저장(stateful)** 이므로 응답 트래픽용 아웃바운드 규칙은 불필요하다.

### 6.2 IAM 역할 분리

| 담당 | 부여 역할 |
|---|---|
| 서버 담당 | `roles/compute.instanceAdmin.v1` |
| 네트워크 담당 | `roles/compute.networkAdmin`, `roles/compute.loadBalancerAdmin` |
| 보안 담당 | `roles/compute.securityAdmin` |
| WAS VM 서비스 계정 | `roles/secretmanager.secretAccessor`, `roles/storage.objectViewer`, `roles/logging.logWriter`, `roles/monitoring.metricWriter` |

- 기본 서비스 계정(Compute Engine default SA)은 사용하지 않는다 — 권한이 과도하다.
- 사용자 계정 전원 **MFA(2단계 인증)** 강제, **OS Login** 활성화.

### 6.3 Cloud Armor 정책

```
rule 1000: origin.region_code != "KR"                                  → deny(403)
rule 2000: evaluatePreconfiguredExpr('sqli-v33-stable')                → deny(403)
rule 2100: evaluatePreconfiguredExpr('xss-v33-stable')                 → deny(403)
rule 2200: evaluatePreconfiguredExpr('lfi-v33-stable')                 → deny(403)
rule 3000: rate_limit  (IP당 100 req/min 초과)                          → throttle(429)
default:   allow
```

- WAF 규칙은 **정책·규칙당 과금**되므로 필요한 것부터 단계적으로 적용한다.
- 처음에는 `preview` 모드로 배포해 정상 트래픽이 차단되지 않는지 확인한 뒤 enforce 로 전환한다.
- Adaptive Protection 은 L7 DDoS를 머신러닝으로 학습 후 규칙을 제안한다.

---

## 7. 기술 의사결정 요약 (발표 Q&A 대비)

| 쟁점 | 선택 | 근거 |
|---|---|---|
| WEB–WAS 연동 | **mod_proxy (HTTP)** | AJP는 Tomcat 9에서 기본 비활성 + Ghostcat(CVE-2020-1938) 이력. mod_jk는 별도 커넥터 설치·설정 필요. HTTP는 Internal **L7** LB와 그대로 호환된다 |
| Internal LB 종류 | **Internal Application LB (L7)** | URL 기반 라우팅과 **HTTP 응답 본문 헬스체크**가 가능. L4 Network LB는 TCP 포트 생존만 확인하므로 "프로세스는 살아있고 앱은 죽은" 상태를 걸러내지 못한다 |
| 세션 관리 | **Stateless + Redis** | Sticky Session은 부하가 쏠리고 축소 시 세션이 유실된다. Tomcat 기본 세션 클러스터링은 **멀티캐스트(45564)** 기반인데 GCP VPC는 유니캐스트만 지원한다 |
| WEB/WAS 이중화 | **Regional MIG** | 개별 VM은 장애 시 수동 복구 필요. Regional MIG는 3 Zone 분산 + Auto-healing + 오토스케일 + 롤링 업데이트/롤백을 모두 제공 |
| DB 접근 | **Private IP 전용** | Public IP 부여 시 승인 네트워크 설정 실수 한 번으로 DB가 인터넷에 노출. Private Service Access는 공인 IP 자체를 만들지 않는다 |
| SSL 종료 위치 | **External LB** | Google-managed 인증서로 갱신 자동화, 백엔드 VM의 SSL 연산 부담 제거, 인증서를 VM 이미지에 넣지 않아도 되어 관리 지점이 하나로 모인다 |
| 헬스체크 기준 | **HTTP 엔드포인트** | 포트 확인만으로는 DB 연결이 끊긴 WAS를 정상으로 판단한다. PetClinic 응답 본문까지 검사한다 |

---

## 8. 구축 순서 (11일 일정 매핑)

| 일차 | 작업 | 산출물 |
|---|---|---|
| 1 | 요구사항 분석 · 아키텍처 확정 | 본 설계서 + draw.io |
| 2 | VPC / Subnet / 방화벽 / Cloud NAT / IAP | 네트워크 기반 |
| 3 | WEB Tier — Apache 2.4 + index.html, 골든 이미지 | WEB 단독 테스트 |
| 4 | WAS Tier — OpenJDK + Tomcat + test.jsp | WAS 단독 테스트 |
| 5 | Cloud SQL 구축 + Private IP + PetClinic 스키마 | DB 연동 검증 |
| 6 | mod_proxy 설정 + Internal LB 구성 | WEB↔WAS 연동 |
| 7 | External LB + Health Check + MIG 이중화 | 전체 Flow 연결 |
| 8 | **Cloud Armor · Secret Manager · Ops Agent · 백업 · Redis** | 확장 기능 |
| 9 | 통합/부하/장애 테스트, Failover 검증, 시연 영상 | 구축 Freeze |
| 10 | 발표 PPT 1차 제출 + 리허설 | 초안 |
| 11 | 최종 PPT 제출 + 시연 | 최종 |

> 8일차의 확장 기능은 **Must → Should → Could** 순으로 적용한다.
> 시간이 부족하면 Could 항목을 "향후 개선 과제"로 발표에 포함시키는 편이,
> 절반만 구현해 동작하지 않는 것보다 낫다.

---

## 9. 비용 고려 사항

- **Cloud Armor**: 정책당 + 규칙당 + 요청당 과금. 필요한 WAF 규칙만 선별 적용.
- **Cloud Logging**: 수집량 과금. 제외 필터가 가장 효과적인 절감 수단.
- **Cloud SQL HA**: 비용이 약 2배. 발표 시연용이라면 구축·검증 후 단일 인스턴스로 되돌리는 것도 방법.
- **Memorystore**: Standard(HA) 대신 Basic 티어로도 세션 외부화 목적은 달성 가능.
- **미사용 리소스**: 고정 IP 미사용분, 오래된 스냅샷, 중지된 VM의 디스크는 계속 과금된다. 매일 점검한다.

---

## 10. 다이어그램 파일 구성

`architecture/gcp-3tier-petclinic-architecture.drawio` — 4개 페이지

| 페이지 | 내용 |
|---|---|
| ① 전체 아키텍처 | 3-Tier 전체 흐름 + 모니터링/백업/보안/DR 요약 |
| ② 모니터링 · 로깅 상세 | 수집 → 분석 → 판단 → 전달 파이프라인, 알림 정책 |
| ③ 백업 · 재해복구(DR) 상세 | VM/DB/파일 백업 경로, GCS 수명주기, RPO/RTO |
| ④ 보안 · 네트워크 상세 | 5계층 방어, 방화벽 규칙표, 관리자 접근 경로 |

[app.diagrams.net](https://app.diagrams.net) 에서 **File → Open From → Device** 로 연다.
아이콘은 draw.io 에 내장된 **공식 Google Cloud 제품 아이콘**(SVG)을 그대로 사용했으므로 별도 라이브러리 설치가 필요 없다.
