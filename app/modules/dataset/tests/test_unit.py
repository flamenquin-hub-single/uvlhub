import pytest
from flask import url_for

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