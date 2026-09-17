# WAS — PetClinic REST 배포 준비

담당: WAS (Compute Engine/MIG, Secret Manager)
애플리케이션: [spring-petclinic/spring-petclinic-rest](https://github.com/spring-petclinic/spring-petclinic-rest)
(`was/app`에 소스 보관 — 업스트림 `.git` 이력은 제거하고 이 저장소에 직접 커밋)

## 디렉터리 구성

```
was/
├── app/            PetClinic REST 애플리케이션 소스 (Maven, Spring Boot)
└── deploy/
    ├── petclinic.service     systemd 유닛 (인스턴스 이미지에 포함)
    └── startup-script.sh     MIG 인스턴스 템플릿의 startup-script
```

## `app`에 적용한 변경 사항

- `BasicAuthenticationConfig`: `/actuator/health`를 인증 없이 통과하도록 `permitAll()` 추가.
  Internal LB Health Check는 자격증명을 보내지 않으므로, `petclinic.security.enable=true`
  상태에서도 헬스체크 경로만은 예외 처리해야 함. (로컬에서 200/401 응답 확인 완료)

## 빌드 확인 완료

```bash
cd was/app
./mvnw -DskipTests clean package
# → target/spring-petclinic-rest-<version>.jar
```

로컬 스모크 테스트 결과:
- `GET /petclinic/actuator/health` → `200` (인증 없이)
- `GET /petclinic/api/owners` → `401` (Basic Auth 필요, 정상 보호됨)

## 진행 체크리스트 (Notion 문서 "기능별 구현 작업 범위" 기준)

- [x] PetClinic REST 소스 확보 및 빌드 검증
- [x] Health Check 엔드포인트가 Internal LB에서 인증 없이 통과하도록 패치
- [x] systemd 유닛 / MIG startup-script 초안 작성
- [ ] **DB 연동**: DB 담당에게서 Cloud SQL Private IP 전달받아 `MYSQL_URL` 확정 (DB 담당과 협업)
- [ ] **Secret Manager**: DB 계정 정보를 담을 Secret 생성 (`petclinic-db-credentials` JSON:
      `{"url","username","password"}`) 및 WAS 서비스 계정에 `Secret Manager Secret Accessor` 권한 부여
- [ ] **인스턴스 이미지/템플릿**: 커스텀 이미지 빌드 또는 base image + startup-script 방식 확정,
      인스턴스 템플릿 metadata(`artifact-bucket`, `db-secret-name`) 설정
- [ ] **MIG 생성**: 인스턴스 템플릿 기반 Managed Instance Group 생성 (2대 이상, 리전 분산 여부 결정)
- [ ] **Internal LB 연동**: NETWORK 담당과 협의해 Health Check(`/petclinic/actuator/health`,
      포트 9966) 및 backend service 연결
- [ ] **사용자 인증 연동 (미결정 — 아래 "논의 필요" 참고)**
- [ ] **Monitoring/Logging**: WAS 인스턴스를 Cloud Monitoring 대상에 포함, journald → Cloud Logging
      에이전트 연동 확인
- [ ] **장애 시나리오 검증**: WAS 인스턴스 1대 강제 중지 → Health Check 실패 → Internal LB가
      나머지 인스턴스로 우회하는지 확인

## 논의가 필요한 사항

### 1. 사용자 인증 방식 — Identity Platform(JWT) vs. 내장 Basic Auth
Notion 문서의 "역할 분담"에는 WAS가 "Token 검증"을 담당한다고 되어 있고, "구현 대상"에는
Identity Platform 기반 JWT를 명시하고 있습니다. 하지만 `spring-petclinic-rest`는 JWT 검증 로직이
없고, **DB에 저장된 사용자 계정으로 HTTP Basic 인증**만 지원합니다(`petclinic.security.enable=true`
시 `users`/`roles` 테이블 기반, 기본 계정 `admin`/`admin`).

두 가지 선택지가 있습니다.

| 옵션 | 설명 | 추가 작업 |
|---|---|---|
| A. 내장 Basic Auth 사용 (권장, 현재 일정상 최소 변경) | WEB이 Identity Platform으로 로그인 UI/세션을 처리하고, WEB→WAS 내부 구간은 VPC 내부 통신 + Internal LB로만 접근 제한. WAS는 기존 Basic Auth 그대로 사용하거나 필요 시 비활성화(`petclinic.security.enable=false`) | 거의 없음 — DB에 users/roles 시드 데이터 준비만 필요 |
| B. Identity Platform JWT 검증 필터 신규 구현 | WAS에 Spring Security 커스텀 필터를 추가해 Identity Platform이 발급한 ID 토큰을 Google JWKS로 검증하고, 클레임을 OWNER_ADMIN/VET_ADMIN/ADMIN 롤에 매핑 | 신규 코드 필요 (JWKS 조회, 토큰 검증, 역할 매핑) — 일정 영향 있음 |

Notion 문서 6번 섹션에서도 "핵심 3-Tier/HA/데이터 안정성 완성을 우선"하라고 명시하므로,
**우선 옵션 A로 진행하고 시간이 남으면 옵션 B로 확장**하는 것을 제안합니다. WEB/NETWORK 담당과
확정 후 이 문서를 업데이트하세요.

### 2. 인스턴스 이미지 배포 방식
`startup-script.sh`는 base image + Cloud Storage에서 jar를 내려받는 방식을 가정합니다. 커스텀
이미지(Packer 등)로 굽는 방식으로 바꾸면 시작 시간이 빨라지지만 이미지 빌드 파이프라인이
추가로 필요합니다. 우선 base image 방식으로 진행 준비.
