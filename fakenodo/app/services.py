import hashlib
import logging
from random import randint
from typing import List
from fakenodo.app.models import Deposition, File
from dotenv import load_dotenv
from core.services.BaseService import BaseService

logger = logging.getLogger(__name__)

load_dotenv()

depositions = []

class Service(BaseService):
    def __init__(self):
        self.headers = {"Content-Type": "application/json"}

    def get_all_depositions(self) -> list:
        return [deposition.to_dict() for deposition in depositions]

    def create_new_deposition(self, deposition: Deposition) -> dict:
        depositions.append(deposition)
        return deposition.to_dict()

    def upload_file(self, file, deposition_id) -> None:
        try:
            # Read file content
            file_data = file.read()

            # Create the file instance
            file_instance = File(
                name=file.filename,
                size=len(file_data),
                checksum=hashlib.md5(file_data).hexdigest(),
                deposition_id=deposition_id
            )

            target_deposition = self.get_deposition(deposition_id)
            if target_deposition is None:
                raise FileNotFoundError("Deposition not found")
            if target_deposition.files is None:
                target_deposition.files = [file_instance.to_dict()]
            else:
                target_deposition.files.append(file_instance.to_dict())

        except Exception as e:
            print(f"Error en la subida del archivo: {e}")

    def publish_deposition(self, deposition: Deposition) -> dict:
        if deposition.doi!=None:
            deposition.published = True
        return deposition.to_dict()

    def delete_deposition(self, deposition: Deposition) -> None:
        depositions.remove(deposition)

    def get_deposition(self, deposition_id: int) -> Deposition | None:
        return [deposition for deposition in depositions if deposition_id == deposition.id][0]

    def get_doi(self, deposition_id: int) -> str:
        return self.get_deposition(deposition_id).doi

    def generate_doi_id():
        identifier = randint(10000,1000000)
        while True:
            yield identifier
            identifier+=1

    doi_generator = generate_doi_id()

    def generate_doi(self,deposition_id):
        deposition = self.get_deposition(deposition_id)
        doi_id = next(self.doi_generator)
        deposition.doi = str(doi_id)+"/dataset."+str(doi_id)
