from locust import HttpUser, TaskSet, task, between
import re

class DownloadDatasetFormats(TaskSet):
    """Simula la descarga de datasets con rutas dinámicas."""

    def on_start(self):
        """Obtiene un ID válido para el dataset. Evita fallos si la petición falla."""
        try:
            self.dataset_id = self.get_valid_dataset_id()
        except Exception as e:
            print(f"⚠️ Error obteniendo el ID: {e}. Usando 53 por defecto.")
            self.dataset_id = 53  # Valor por defecto si la petición falla
        self.base_zip_url = f"/dataset/download/{self.dataset_id}"
        self.base_export_url = f"/flamapy/export_dataset/{self.dataset_id}"

    def get_valid_dataset_id(self):
        """Obtiene un ID válido consultando la página principal."""
        response = self.client.get("/doi/10.1234/", name="Get Dataset ID")
        if response.status_code == 200:
            match = re.search(r'/dataset/download/(\d+)', response.text)
            if match:
                print(f"✅ ID encontrado: {match.group(1)}")
                return match.group(1)  # Retorna el primer ID encontrado
        raise Exception("No se pudo obtener un ID válido")

    @task
    def download_zip(self):
        """Descarga el dataset en formato ZIP."""
        self.client.get(self.base_zip_url, name="Download ZIP")

    @task
    def download_glencoe(self):
        """Descarga el dataset en formato Glencoe."""
        self.client.get(f"{self.base_export_url}/glencoe", name="Download Glencoe")

    @task
    def download_dimacs(self):
        """Descarga el dataset en formato DIMACS."""
        self.client.get(f"{self.base_export_url}/dimacs", name="Download DIMACS")

    @task
    def download_splot(self):
        """Descarga el dataset en formato SPLOT."""
        self.client.get(f"{self.base_export_url}/splot", name="Download SPLOT")

class DatasetUser(HttpUser):
    """Simula un usuario que descarga datasets con rutas adaptadas."""
    tasks = [DownloadDatasetFormats]
    wait_time = between(1, 2)
    host = "http://localhost:5000"
