import random
from locust import HttpUser, TaskSet, task, between
from core.locust.common import get_csrf_token
from core.environment.host import get_host_for_locust_testing


class DatasetBehavior(TaskSet):
    def on_start(self):
        """Acción que se ejecuta al inicio del test."""
        self.dataset_upload()

    @task
    def dataset_upload(self):
        """Simula la carga de la página de subida de datasets."""
        response = self.client.get("/dataset/upload")
        get_csrf_token(response)
        
        
class CommitDatasetBehavior(TaskSet):
    def on_start(self):
        """Simulate user login before running the commit task."""
        self.ensure_logged_in()

    def ensure_logged_in(self):
        """Ensure the user is authenticated."""
        response = self.client.get("/login")
        csrf_token = get_csrf_token(response)

        response = self.client.post("/login", data={
            "email": 'user1@example.com',
            "password": '1234',
            "csrf_token": csrf_token
        })

        if response.status_code != 200:
            print(f"Login failed: {response.status_code}, {response.text}")
        else:
            print("User successfully logged in.")

    @task
    def commit_dataset(self):
        dataset_id = random.randint(1, 5)
        response = self.client.post(f"/dataset/commit/{dataset_id}", json={})
        
        if response.status_code == 200:
            print(f"Dataset {dataset_id} committed successfully: {response.text}")
        elif response.status_code == 404:
            print(f"Dataset {dataset_id} not found: {response.status_code}")
        elif response.status_code == 500:
            print(f"Server error for dataset {dataset_id}: {response.status_code} - {response.text}")
        else:
            print(f"Unexpected status for dataset {dataset_id}: {response.status_code} - {response.text}")



class CommitFileBehavior(TaskSet):
    def on_start(self):
        """Simulate user login before running the commit task."""
        self.ensure_logged_in()

    def ensure_logged_in(self):
        """Ensure the user is authenticated."""
        response = self.client.get("/login")
        csrf_token = get_csrf_token(response)

        response = self.client.post("/login", data={
            "email": 'user1@example.com',
            "password": '1234',
            "csrf_token": csrf_token
        })

        if response.status_code != 200:
            print(f"Login failed: {response.status_code}, {response.text}")
        else:
            print("User successfully logged in.")
            
            
    @task
    def commit_dataset(self):
        file_id = random.randint(1, 5)  
        response = self.client.post(f"/dataset/commit_file/{file_id}", json={})
        
        if response.status_code == 200:
            print(f"File {file_id} committed successfully: {response.text}")
        elif response.status_code == 404:
            print(f"File {file_id} not found: {response.status_code}")
        elif response.status_code == 500:
            print(f"Server error for File {file_id}: {response.status_code} - {response.text}")
        else:
            print(f"Unexpected status for File {file_id}: {response.status_code} - {response.text}")
            
         

class DatasetUser(HttpUser):
    tasks = [DatasetBehavior, CommitDatasetBehavior, CommitFileBehavior]
    wait_time = between(5, 9)
    host = get_host_for_locust_testing()