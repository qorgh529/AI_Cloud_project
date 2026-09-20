# GCE Startup Script — PetClinic WAR 배포 + Cloud SQL 연동

대상: Rocky Linux 9, Tomcat9 + JDK17이 사전 설치된 GCE 이미지

## 파일 구성

- `startup-script.sh`
  - GCE 인스턴스 메타데이터 `startup-script`로 등록하는 **단일 파일**.
  - 부팅 시 자기 안에서 바로 `gs://npc-bucket-nova/releases/petclinic.war`를
    내려받아 `/opt/tomcat/webapps/petclinic`에 배포하고, 이어서 Cloud
    SQL(MySQL) 연결 설정 및 PetClinic 스키마/초기데이터를 적재한 뒤
    Tomcat을 (재)시작한다. 별도 파일을 생성/호출하지 않는다.
- `deploy-petclinic-war.sh`
  - war 다운로드/배포 로직만 떼어낸 독립 스크립트(참고용/수동 재실행용).
  - `startup-script.sh`가 실행 중 이 파일을 만들거나 호출하지는 않는다.
    war 배포만 다시 하고 싶을 때 인스턴스에 SSH로 접속해 직접
    `sudo bash deploy-petclinic-war.sh`로 실행할 수 있도록 남겨둔 참고
    스크립트다. 필요 없으면 삭제해도 `startup-script.sh` 동작에는 영향이
    없다.

## 사용 방법

```bash
gcloud compute instances create petclinic-was \
  --image-family=rocky-linux-9-tomcat9-jdk17 \
  --image-project=<YOUR_PROJECT> \
  --metadata-from-file=startup-script=scripts/gce/startup-script.sh \
  --service-account=<서비스 계정> \
  --scopes=cloud-platform
```

또는 기존 인스턴스에 적용:

```bash
gcloud compute instances add-metadata petclinic-was \
  --zone=<ZONE> \
  --metadata-from-file=startup-script=scripts/gce/startup-script.sh
```

## 사전 요구사항

- 인스턴스 서비스 계정에 다음 권한 필요
  - `roles/storage.objectViewer` (또는 버킷 단위 IAM) — `gs://npc-bucket-nova` 읽기
  - `roles/secretmanager.secretAccessor` — `petclinic-db-password` 시크릿 조회
- Cloud SQL(MySQL) 프라이빗 IP(`192.168.32.14:3306`)로 네트워크 접근 가능해야 함
  (VPC 피어링/방화벽 규칙 확인)
- 이미지에 `gcloud` 또는 `gsutil` CLI가 포함되어 있어야 함 (Google 제공 이미지는 기본 포함)

## 로그

- 전체 startup-script 로그(war 배포 포함): `/var/log/startup-script.log`
- `deploy-petclinic-war.sh`를 수동으로 단독 실행한 경우: `/var/log/war-deploy.log`
