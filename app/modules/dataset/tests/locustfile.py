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

    @task(4)
    def download_dataset_glencoe(self):
        """Simula la descarga del dataset en formato Glencoe."""
        dataset_id = 4  # Ajusta el ID del dataset si es necesario
        self.client.get(f"/dataset/download/{dataset_id}/glencoe", name="/dataset/download/glencoe")

    @task(3)
    def download_dataset_splot(self):
        """Simula la descarga del dataset en formato SPLOT."""
        dataset_id = 4
        self.client.get(f"/dataset/download/{dataset_id}/splot", name="/dataset/download/splot")

    @task(2)
    def download_dataset_dimacs(self):
        """Simula la descarga del dataset en formato DIMACS."""
        dataset_id = 4
        self.client.get(f"/dataset/download/{dataset_id}/dimacs", name="/dataset/download/dimacs")

    @task(1)
    def download_dataset_zip(self):
        """Simula la descarga del dataset en formato ZIP."""
        dataset_id = 4
        self.client.get(f"/dataset/download/{dataset_id}/zip", name="/dataset/download/zip")


class DatasetUser(HttpUser):
    """Clase principal que define los usuarios y su comportamiento."""
    tasks = [DatasetBehavior]
    wait_time = between(5, 9)  # Espera entre 5 y 9 segundos entre tareas
    host = get_host_for_locust_testing()