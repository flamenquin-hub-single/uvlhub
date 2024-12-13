from flask import json
from locust import HttpUser, TaskSet, task
from core.locust.common import get_csrf_token, fake
from core.environment.host import get_host_for_locust_testing


class ExploreBehavior(TaskSet):

    @task
    def explore(self):
        response = self.client.get("/explore")
        if response.status_code != 200:
            print(f"Explore failed: {response.status_code}")

        csrf_token = get_csrf_token(response)

        response = self.client.post("/explore",
                                    headers={"Content-Type": "application/json"},
                                    data=json.dumps({
                                        "min_files": fake.random_int(min=1, max=5),
                                        "max_files": fake.random_int(min=2, max=6),
                                        "max_depth": fake.random_int(min=0, max=3),
                                        "min_depth": fake.random_int(min=2, max=6),
                                        "min_leaf_count": fake.random_int(min=0, max=10),
                                        "max_leaf_count": fake.random_int(min=5, max=15),
                                        "min_av_branching_factor": fake.random_int(min=0, max=2),
                                        "max_av_branching_factor": fake.random_int(min=1, max=4),
                                        "csrf_token": csrf_token
                                    }))
        if response.status_code != 200:
            print(f"Filtering failed: {response.status_code}")


class ExploreUser(HttpUser):
    tasks = [ExploreBehavior]
    min_wait = 3000
    max_wait = 7000
    host = get_host_for_locust_testing()
