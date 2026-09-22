"""
Locust 부하 테스트 스크립트

실행 방법 (Windows PowerShell):
    locust -f locustfile.py

실행 후 브라우저에서 http://localhost:8089 접속하면 웹 UI에서
가상 사용자 수(Number of users), 초당 증가 수(Ramp up), 대상 호스트(Host)를
입력하고 테스트를 시작/중지하며 실시간 그래프와 통계를 볼 수 있습니다.

host는 웹 UI에서 입력하거나, --host 옵션 또는 아래 host 값으로 지정할 수 있습니다.
지금은 예시로 공개 테스트 서버(httpbin.org)를 사용합니다.
실제 테스트할 서버가 생기면 host 값 또는 실행 시 --host 옵션을 그 주소로 바꾸세요.
"""

from locust import HttpUser, task, between


class WebsiteUser(HttpUser):
    # 요청 사이 대기 시간 (초 단위, 1~3초 랜덤)
    wait_time = between(1, 3)

    # 웹 UI에서 host를 직접 입력하지 않을 경우 사용할 기본 대상
    host = "https://httpbin.org"

    @task(3)
    def get_root(self):
        self.client.get("/get")

    @task(1)
    def post_data(self):
        self.client.post("/post", json={"key": "value"})
