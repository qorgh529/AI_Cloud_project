import os
from locust import HttpUser, task, between


class WebsiteUser(HttpUser):
    """Sample load test. Point TARGET_HOST at the system under test
    (e.g. `locust -f locustfile.py --host=https://your-api.example.com`)."""

    wait_time = between(1, 3)

    @task
    def index(self):
        self.client.get("/")
