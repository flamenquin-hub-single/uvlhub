import logging
import os
import json
import shutil
import subprocess
import tempfile
import uuid
from datetime import datetime, timezone
from zipfile import ZipFile
from flask import jsonify, redirect, url_for, render_template, request, send_from_directory, make_response, abort
from flask_login import login_required, current_user
import requests
from app.modules.dataset.repositories import DSMetaDataRepository
from app.modules.dataset.forms import DataSetForm
from app.modules.dataset.models import DSDownloadRecord
from app.modules.dataset import dataset_bp
from app.modules.dataset.repositories import DataSetRepository
from app.modules.dataset.services import (
    AuthorService,
    DSDownloadRecordService,
    DSMetaDataService,
    DSViewRecordService,
    DataSetService,
    DOIMappingService
)
from app.modules.hubfile.repositories import HubfileRepository
from app.modules.zenodo.services import ZenodoService
from app.modules.dataset.parser import get_tree
logger = logging.getLogger(__name__)
from flask_dance.contrib.github import github


logger = logging.getLogger(__name__)

dataset_service = DataSetService()
author_service = AuthorService()
dsmetadata_service = DSMetaDataService()
zenodo_service = ZenodoService()
doi_mapping_service = DOIMappingService()
ds_view_record_service = DSViewRecordService()

@dataset_bp.route("/dataset/upload", methods=["GET", "POST"])
@login_required
def create_dataset():
    form = DataSetForm()
    if request.method == "POST":
        dataset = None

        if not form.validate_on_submit():
            return jsonify({"message": form.errors}), 400

        try:
            logger.info("Creating dataset...")
            dataset = dataset_service.create_from_form(form=form, current_user=current_user)
            logger.info(f"Created dataset: {dataset}")
            dataset_service.move_feature_models(dataset)
        except Exception as exc:
            logger.exception(f"Exception while creating dataset data in local {exc}")
            return jsonify({"Exception while creating dataset data in local": str(exc)}), 400

        # send dataset as deposition to Zenodo
        data = {}
        try:
            zenodo_response_json = zenodo_service.create_new_deposition(dataset)
            response_data = json.dumps(zenodo_response_json)
            data = json.loads(response_data)
        except Exception as exc:
            data = {}
            zenodo_response_json = {}
            logger.exception(f"Exception while creating dataset data in Zenodo {exc}")

        if data.get("conceptrecid"):
            deposition_id = data.get("id")
            dataset_service.update_dsmetadata(dataset.ds_meta_data_id, deposition_id=deposition_id)

            try:
                for feature_model in dataset.feature_models:
                    zenodo_service.upload_file(dataset, deposition_id, feature_model)
                zenodo_service.publish_deposition(deposition_id)
                deposition_doi = zenodo_service.get_doi(deposition_id)
                dataset_service.update_dsmetadata(dataset.ds_meta_data_id, dataset_doi=deposition_doi)
            except Exception as e:
                msg = f"it has not been possible to upload feature models in Zenodo and update the DOI: {e}"
                return jsonify({"message": msg}), 200

        file_path = current_user.temp_folder()
        if os.path.exists(file_path) and os.path.isdir(file_path):
            shutil.rmtree(file_path)

        msg = "Everything works!"
        return jsonify({"message": msg}), 200

    return render_template("dataset/upload_dataset.html", form=form)

@dataset_bp.route("/dataset/list", methods=["GET", "POST"])
@login_required
def list_dataset():
    return render_template(
        "dataset/list_datasets.html",
        datasets=dataset_service.get_synchronized(current_user.id),
        local_datasets=dataset_service.get_unsynchronized(current_user.id),
    )


@dataset_bp.route("/dataset/check", methods=["GET", "POST"])
@login_required
def check_dataset():
    form = DataSetForm()
    if request.method=="POST": 

        temp_folder = current_user.temp_folder()
        if not os.path.exists(temp_folder):
           return jsonify({"message": "Something went wrong, try again"}), 400
        
        filename = os.listdir(temp_folder)[0]
        file_path = os.path.join(temp_folder, filename)
        
        with open(file_path) as f:
            indent = 0
            x = "".join([i for i in f])
            print(x)
        return jsonify({"message": x}),200
   
    # setting things up for the checker to have only one file available
    temp_folder = current_user.temp_folder()
    if os.path.exists(temp_folder) and os.path.isdir(temp_folder):
            shutil.rmtree(temp_folder)

    return render_template(
        "dataset/check_datasets.html", form = form )


@dataset_bp.route("/dataset/file/upload", methods=["POST"])
@login_required
def upload():
    file = request.files["file"]
    temp_folder = current_user.temp_folder()

    if not file or not file.filename.endswith(".uvl"):
        return jsonify({"message": "No valid file"}), 400

    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    file_path = os.path.join(temp_folder, file.filename)

    if os.path.exists(file_path):
        base_name, extension = os.path.splitext(file.filename)
        i = 1
        while os.path.exists(
            os.path.join(temp_folder, f"{base_name} ({i}){extension}")
        ):
            i += 1
        new_filename = f"{base_name} ({i}){extension}"
        file_path = os.path.join(temp_folder, new_filename)
    else:
        new_filename = file.filename

    try:
        file.save(file_path)
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    try:
        get_tree(file_path)
    except Exception as e:
        os.remove(file_path)
        return jsonify({"message": str(e),"syntax": True}),400

    return (
        jsonify(
            {
                "message": "UVL uploaded and validated successfully",
                "filename": new_filename,
            }
        ),
        200,
    )

@dataset_bp.route("/dataset/file/delete", methods=["POST"])
def delete():
    data = request.get_json()
    filename = data.get("file")
    temp_folder = current_user.temp_folder()
    filepath = os.path.join(temp_folder, filename)

    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({"message": "File deleted successfully"})

    return jsonify({"error": "Error: File not found"})

@dataset_bp.route("/dataset/download/<int:dataset_id>", methods=["GET"])
def download_dataset(dataset_id):
    dataset = dataset_service.get_or_404(dataset_id)
    file_path = f"uploads/user_{dataset.user_id}/dataset_{dataset.id}/"
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, f"dataset_{dataset_id}.zip")

    with ZipFile(zip_path, "w") as zipf:
        for subdir, dirs, files in os.walk(file_path):
            for file in files:
                full_path = os.path.join(subdir, file)
                relative_path = os.path.relpath(full_path, file_path)
                zipf.write(
                    full_path,
                    arcname=os.path.join(
                        os.path.basename(zip_path[:-4]), relative_path
                    ),
                )

    user_cookie = request.cookies.get("download_cookie")
    if not user_cookie:
        user_cookie = str(uuid.uuid4())
        resp = make_response(
            send_from_directory(
                temp_dir,
                f"dataset_{dataset_id}.zip",
                as_attachment=True,
                mimetype="application/zip",
            )
        )
        resp.set_cookie("download_cookie", user_cookie)
    else:
        resp = send_from_directory(
            temp_dir,
            f"dataset_{dataset_id}.zip",
            as_attachment=True,
            mimetype="application/zip",
        )

    existing_record = DSDownloadRecord.query.filter_by(
        user_id=current_user.id if current_user.is_authenticated else None,
        dataset_id=dataset_id,
        download_cookie=user_cookie
    ).first()

    if not existing_record:
        DSDownloadRecordService().create(
            user_id=current_user.id if current_user.is_authenticated else None,
            dataset_id=dataset_id,
            download_date=datetime.now(timezone.utc),
            download_cookie=user_cookie,
        )

    return resp

@dataset_bp.route("/doi/<path:doi>/", methods=["GET"])
def subdomain_index(doi):
    new_doi = doi_mapping_service.get_new_doi(doi)
    if new_doi:
        return redirect(url_for('dataset.subdomain_index', doi=new_doi), code=302)

    ds_meta_data = dsmetadata_service.filter_by_doi(doi)

    if not ds_meta_data:
        abort(404)

    dataset = ds_meta_data.data_set
    
    # Export DataSet to BibTex
    
    bibtex_propiedades = {
        "author": " and ".join([a_.name for a_ in ds_meta_data.authors]),
        "title": ds_meta_data.title,
        "howpublished": None,
        "year": str(dataset.created_at.date().year),
        "note": "Accessed: {}".format(str(datetime.now().date())),
        "annote": ds_meta_data.description
    }
    texto_howpublished = "https://zenodo.org/records/{}" if os.environ.get("FLASK_ENV").lower()=="production" else "https://sandbox.zenodo.org/records/{}"
    bibtex_propiedades["howpublished"] = texto_howpublished.format(ds_meta_data.deposition_id)
    
    lineas_preview ="@misc{MiscUvl" + ds_meta_data.title.replace(" ", "") + ",\n  "
    lineas_preview += "\n  ".join([k_ + " = {" + v_+ "}," for (k_,v_) in bibtex_propiedades.items()]) + "\n}"

    bibtex_file_name = ds_meta_data.title.replace(" ", "_").lower() + ".bib"

    # Save the cookie to the user's browser
    user_cookie = ds_view_record_service.create_cookie(dataset=dataset)

    resp = make_response(render_template("dataset/view_dataset.html",dataset=dataset,bibtex_dataset=lineas_preview,bibtex_file_name=bibtex_file_name))
    resp.set_cookie("view_cookie", user_cookie)

    return resp

@dataset_bp.route("/dataset/unsynchronized/<int:dataset_id>/", methods=["GET"])
@login_required
def get_unsynchronized_dataset(dataset_id):
    dataset = dataset_service.get_unsynchronized_dataset(current_user.id, dataset_id)

    if not dataset:
        abort(404)
    
    ds_meta_data = dsmetadata_service.get_by_id(dataset.ds_meta_data_id)

    bibtex_propiedades = {
        "author": " and ".join([a_.name for a_ in ds_meta_data.authors]),
        "title": ds_meta_data.title,
        "howpublished": None,
        "year": str(dataset.created_at.date().year),
        "note": "Accessed: {}".format(str(datetime.now().date())),
        "annote": ds_meta_data.description
    }
    texto_howpublished = "https://zenodo.org/records/{}" if os.environ.get("FLASK_ENV").lower()=="production" else "https://sandbox.zenodo.org/records/{}"
    bibtex_propiedades["howpublished"] = texto_howpublished.format(ds_meta_data.deposition_id)
    
    lineas_preview ="@misc{MiscUvl" + ds_meta_data.title.replace(" ", "") + ",\n  "
    lineas_preview += "\n  ".join([k_ + " = {" + v_+ "}," for (k_,v_) in bibtex_propiedades.items()]) + "\n}"

    bibtex_file_name = ds_meta_data.title.replace(" ", "_").lower() + ".bib"
   
    return render_template("dataset/view_dataset.html", dataset=dataset,bibtex_dataset=lineas_preview,bibtex_file_name=bibtex_file_name)


@dataset_bp.route('/dataset/commit/<int:dataset_id>', methods=['GET','POST'])
def commit(dataset_id):
    
    account_info = github.get('/user')
    
    if account_info.ok:
        username = account_info.json()['login']
        name = account_info.json().get('name') or "Unknown Name"
        email = account_info.json().get('email') or "unknown@example.com"
    else:
        return 'First sync your github account.'
    
    try:
            
        ruta_repositorio = f"/app/uvl_git/{username}"   
        
        subprocess.run(f"git config user.name '{name}'", cwd=ruta_repositorio, check=True, shell=True)
        subprocess.run(f"git config user.email '{email}'", cwd=ruta_repositorio, check=True, shell=True)
        
        token = os.getenv('GH_PAT')
        repo_url = f"https://{token}@github.com/uvlhub/{username}.git"
        subprocess.run(f"git remote set-url origin {repo_url}", cwd=ruta_repositorio, check=True, shell=True)
             
        # Obtener el nombre y los archivos del dataset
        repository = DataSetRepository()
        nombre = repository.get_dataset_name(dataset_id)
        ruta_carpeta = os.path.join(ruta_repositorio, nombre)
        os.makedirs(ruta_carpeta, exist_ok=True)
        
        all_files = repository.get_all_files_for_dataset(dataset_id)
        
        # Copiar archivos, llevarlos al directorio de git y stagearlos
        for archivo in all_files:
            ruta_archivo_origen = archivo.get_path()
            ruta_destino_archivo = os.path.join(ruta_carpeta, os.path.basename(ruta_archivo_origen))
            shutil.copy(ruta_archivo_origen, ruta_destino_archivo)
            subprocess.run(f"git add {os.path.relpath(ruta_destino_archivo, ruta_repositorio)}", cwd=ruta_repositorio, check=True, shell=True)
        
        subprocess.run('git commit -m "Commit realizado desde uvlhub"', cwd=ruta_repositorio, check=True, shell=True)
        subprocess.run("git push origin main", cwd=ruta_repositorio, check=True, shell=True)

        return "Dataset has been pushed to GitHub correctly."


    except subprocess.CalledProcessError as e:
        return f"This dataset is already in your github repository."
    
    
    
@dataset_bp.route('/dataset/commit_file/<int:file_id>', methods=['GET','POST'])
def commit_file(file_id):
    
    account_info = github.get('/user')
    
    if account_info.ok:
        username = account_info.json()['login']
        name = account_info.json().get('name') or "Unknown Name"
        email = account_info.json().get('email') or "unknown@example.com"
        
    else:
        return 'First sync your github account.'
    
    try:
       
        ruta_repositorio = f"/app/uvl_git/{username}"
    
        subprocess.run(f"git config user.name '{name}'", cwd=ruta_repositorio, check=True, shell=True)
        subprocess.run(f"git config user.email '{email}'", cwd=ruta_repositorio, check=True, shell=True)

        # Configurar URL remota con el PAT
        token = os.getenv('GH_PAT')
        repo_url = f"https://{token}@github.com/uvlhub/{username}.git"
        subprocess.run(f"git remote set-url origin {repo_url}", cwd=ruta_repositorio, check=True, shell=True)

        # Obtener archivo y copiarlo al directorio de git
        hubfile_repository = HubfileRepository()
        hubfile = hubfile_repository.get_hubfile_by_id(file_id)
        ruta_archivo_origen = hubfile.get_path()
        ruta_destino_archivo = os.path.join(ruta_repositorio, hubfile.name)
        shutil.copy(ruta_archivo_origen, ruta_destino_archivo)

        subprocess.run(f"git add {hubfile.name}", cwd=ruta_repositorio, check=True, shell=True)
        subprocess.run('git commit -m "Commit realizado desde uvlhub"', cwd=ruta_repositorio, check=True, shell=True)
        subprocess.run("git push origin main", cwd=ruta_repositorio, check=True, shell=True)

        return "This model has been pushed to GitHub correctly."

    except subprocess.CalledProcessError as e:
        return f"This model is already in your github repository."

    return render_template("dataset/view_dataset.html", dataset=dataset)

@dataset_bp.route("/dataset/download/<int:file_id>/<string:format>", methods=["GET"])
def download_dataset_format(file_id, format):
    """Endpoint to download dataset in the specified format.
    Formats supported: glencoe, splot, dimacs, zip.
    """
    if format == "glencoe":
        return redirect(url_for("flamapy.to_glencoe", file_id=file_id))
    elif format == "splot":
        return redirect(url_for("flamapy.to_splot", file_id=file_id))
    elif format == "dimacs":
        return redirect(url_for("flamapy.to_cnf", file_id=file_id))
    elif format == "zip":
        return redirect(url_for("dataset.download_dataset", dataset_id=file_id))
    else:
        return jsonify({"error": "Formato no soportado"}), 400
