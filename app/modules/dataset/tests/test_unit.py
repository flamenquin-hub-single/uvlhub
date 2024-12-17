import pytest
from flask import url_for
import io
import shutil
import json

@pytest.fixture(scope="module")
def test_client(test_client):
    """
    Extiende la fixture test_client para el módulo dataset.
    """
    with test_client.application.app_context():
        pass

    yield test_client


def test_download_glencoe_redirect(test_client):
    """
    Testea la redirección para el formato Glencoe.
    """
    response = test_client.get("/dataset/download/4/glencoe")
    assert response.status_code == 302
    assert url_for("flamapy.export_dataset", dataset_id=4, format="glencoe") in response.location


def test_download_splot_redirect(test_client):
    """
    Testea la redirección para el formato SPLOT.
    """
    response = test_client.get("/dataset/download/4/splot")
    assert response.status_code == 302
    assert url_for("flamapy.export_dataset", dataset_id=4, format="splot") in response.location


def test_download_dimacs_redirect(test_client):
    """
    Testea la redirección para el formato DIMACS.
    """
    response = test_client.get("/dataset/download/4/dimacs")
    assert response.status_code == 302
    assert url_for("flamapy.export_dataset", dataset_id=4, format="dimacs") in response.location


def test_download_zip_redirect(test_client):
    """
    Testea la redirección para el formato ZIP.
    """
    response = test_client.get("/dataset/download/4/zip")
    assert response.status_code == 302
    assert url_for("flamapy.export_dataset", dataset_id=4, format="zip") in response.location

def aux_upload_errors(file,error,test_client):
    """
    Reutilizar código
    """
    response = test_client.get(url_for('dataset.check_dataset'))
    assert response.status_code == 200
    data = {'name': 'file', 'filename': 'test_file.uvl'}
    data['file'] = file
    response = test_client.post(
        url_for('dataset.upload_check'), data=data, follow_redirects=True,
        content_type='multipart/form-data'
    )
    assert response.status_code == 200
    response = test_client.post(url_for('dataset.check_dataset'))
    assert response.status_code==400
    assert response.json['error']==error

def test_upload_file_bad_indent(test_client):
    """
    Testea la subida de ficheros con errores de sintaxis al Dropbox en dataset/upload
    """
    test_client.post(
        "/login", data=dict(email="test@example.com", password="test1234"), follow_redirects=True
    )

    file = (io.BytesIO(b"""features
    Chat
        mandatory
            Connection
                alternative
                    "Peer 2 Peer"
                    Server
            Messages
                or
		    Text
                    Video
                    Audio
        optional
            "Data Storage"
       fdd     "Media Player"

constraints
    Server => "Data Storage"
    Video | Audio => "Media Player\""""), 'test_bad_indent.uvl')
    error = "The UVL has the following error that prevents reading it :Line 15:7 - mismatched input 'fdd' expecting '<DEDENT>'"
    aux_upload_errors(file,error,test_client)

def test_upload_file_syntax_error(test_client):
    file = (io.BytesIO(b"""features
    Chat
        mandatory
            Connection
                alternative
                    "Peer 2 Peer"
                    Server
            Messages
                or
		    Text
                    Video
                    Audio
        optional
            "Data Storage"
       	    "Media Player"

constraints
    Server =s"> "Data Storage"
    Video | Audio => "Media Player\""""),'test_syntax_error.uvl')
    error = "The UVL has the following error that prevents reading it :Line 18:11 - token recognition error at: '=s'"
    aux_upload_errors(file,error,test_client)

def test_upload_file_typo(test_client):
    file = (io.BytesIO(b"""features
    Chat
        mandatory
            Connection
                alternative
                    "Peer 2 Peer"
                    Server
            Messages
                or
		    Text
                    Video
                    Audio
        optional
            "Data Storage"
       	    "Media Player"

constraintss
    Server => "Data Storage"
    Video | Audio => "Media Player\""""),'test_typo.uvl')
    error = "The UVL has the following error that prevents reading it :Line 17:0 - mismatched input 'constraintss' expecting {<EOF>, 'constraints'}"
    aux_upload_errors(file,error,test_client)

def test_delete_file_from_dropbox(test_client):
    file = (io.BytesIO(b"""This one doesn't matter"""),'test.uvl')
    data = {'name': 'file', 'filename': 'test_file.uvl'}
    data['file'] = file
    response = test_client.post(
        url_for('dataset.upload_check'), data=data, follow_redirects=True,
        content_type='multipart/form-data'
    )
    assert response.status_code == 200
    data = {'file':'test.uvl'}
    response = test_client.post(url_for('dataset.delete'),data=json.dumps(data),content_type = 'application/json')
    assert response.status_code == 200


def test_upload_models_with_syntax_errors(test_client):
    file = (io.BytesIO(b"""features
    Chat
        mandatory
            Connection
                alternative
                    "Peer 2 Peer"
                    Server
            Messages
                or
		    Text
                    Video
                    Audio
        optional
            "Data Storage"
       	    "Media Player"

constraintss
    Server => "Data Storage"
    Video | Audio => "Media Player\""""),'test_typo.uvl')
    data = {'name': 'file', 'filename':'test_file.uvl'}
    data['file'] = file
    response = test_client.post(
        url_for('dataset.upload'), data=data,
        content_type='multipart/form-data'
    )
    assert response.status_code == 400
    assert response.json['message']=="The UVL has the following error that prevents reading it :Line 17:0 - mismatched input 'constraintss' expecting {<EOF>, 'constraints'}"



