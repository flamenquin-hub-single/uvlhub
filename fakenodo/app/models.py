class Creator:
    def __init__(self, name: str, id: int = None, deposition_id: int = None):
        self.id = id
        self.name = name
        self.deposition_id = deposition_id

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'deposition_id': self.deposition_id
        }


class File:
    _id_counter = 1

    def __init__(self, name: str, size: int, checksum, deposition_id: str):
        self.id = File._id_counter
        File._id_counter += 1
        self.name = name
        self.size = size
        self.checksum = checksum
        self.deposition_id = deposition_id

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "size": self.size,
            "checksum": self.checksum
        }


class Deposition:
    _id_counter = 1

    def __init__(self, title=None, upload_type=None, publication_type=None, description=None,
                 creators=None, keywords=None, access_right=None, license=None, doi=None, published=False, files=None):
        self.id = Deposition._id_counter
        Deposition._id_counter += 1

        self.title = title
        self.upload_type = upload_type
        self.publication_type = publication_type
        self.description = description
        self.creators = creators
        self.keywords = keywords
        self.access_right = access_right
        self.license = license
        self.doi = doi
        self.published = published
        self.files = files
        self.conceptrecid = self.id - 1

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "upload_type": self.upload_type,
            "publication_type": self.publication_type,
            "description": self.description,
            "creators": self.creators,
            "keywords": self.keywords,
            "access_right": self.access_right,
            "license": self.license,
            "doi": self.doi,
            "published": self.published,
            "files": self.files,
            "conceptrecid": self.conceptrecid
        }
