from locust import HttpUser, TaskSet, task
import requests
from core.locust.common import get_csrf_token, fake
from core.environment.host import get_host_for_locust_testing


class SignupBehavior(TaskSet):
    def on_start(self):
        self.signup()

    @task
    def signup(self):
        response = self.client.get("/signup")
        csrf_token = get_csrf_token(response)

        response = self.client.post("/signup", data={
            "email": fake.email(),
            "password": fake.password(),
            "csrf_token": csrf_token
        })
        if response.status_code != 200:
            print(f"Signup failed: {response.status_code}")


class LoginBehavior(TaskSet):
    def on_start(self):
        self.ensure_logged_out()
        self.login()

    @task
    def ensure_logged_out(self):
        response = self.client.get("/logout")
        if response.status_code != 200:
            print(f"Logout failed or no active session: {response.status_code}")

    @task
    def login(self):
        response = self.client.get("/login")
        if response.status_code != 200 or "Login" not in response.text:
            print("Already logged in or unexpected response, redirecting to logout")
            self.ensure_logged_out()
            response = self.client.get("/login")

        csrf_token = get_csrf_token(response)

        response = self.client.post("/login", data={
            "email": 'user1@example.com',
            "password": '1234',
            "csrf_token": csrf_token
        })
        if response.status_code != 200:
            print(f"Login failed: {response.status_code}")


class InviteBehavior(TaskSet):
    def on_start(self):
        self.ensure_logged_in()

    def ensure_logged_in(self):
        response = self.client.get("/login")
        csrf_token = get_csrf_token(response)

        response = self.client.post("/login", data={
            "email": 'user1@example.com',
            "password": '1234',
            "csrf_token": csrf_token
        })
        if response.status_code != 200:
            print(f"Login failed: {response.status_code}")
        else:
            print("User successfully logged in.")

    @task
    def invite_user(self):
        github_user_response = requests.get("https://api.github.com/user", headers={
            "Authorization": "token example_valid_token",
            "Accept": "application/vnd.github.v3+json"
        })

        if github_user_response.status_code != 200:
            print(f"Failed to fetch GitHub user info: {github_user_response.status_code}")

        username = github_user_response.json().get("login")
        if not username:
            print("Failed to fetch GitHub username.")

        response = self.client.post("/invite", json={
            "github_username": username
        })
        
        if response.status_code == 201:
            print(f"Invitation sent successfully to {username}.")
        elif response.status_code == 404:
            print(f"GitHub user {username} not found.")
        elif response.status_code == 422:
            print(f"User {username} already belongs to the organization.")
        else:
            print(f"Invitation failed with status: {response.status_code} - {response.text}")




class AuthUser(HttpUser):
    tasks = [SignupBehavior, LoginBehavior, InviteBehavior]
    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()
    
    
