import logging
import requests
from flask import Blueprint, jsonify, request
from fakenodo.app.models import Deposition
from fakenodo.app.services import Service

api_bp = Blueprint("api_bp", __name__)
logger = logging.getLogger(__name__)
service = Service()


@api_bp.route('/api/fakenodo/depositions', methods=['GET', 'POST'])
def depositions() -> tuple:
    def get_all_depositions() -> tuple:
        try:
            depositions = service.get_all_depositions()
            return jsonify(depositions), 200

        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    def create_deposition() -> tuple:
        data = request.json
        try:
            # Create a Deposition instance with the request metadata
            deposition = Deposition(**data["metadata"])

            # Save the deposition in a local list
            response_data = service.create_new_deposition(deposition)

            return jsonify(response_data), 201
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    if request.method == "GET":
        return get_all_depositions()
    else:
        return create_deposition()


@api_bp.route('/api/fakenodo/depositions/<int:deposition_id>/files', methods=['POST'])
def upload_file(deposition_id) -> tuple:
    try:
        for file in request.files.getlist('file'):
            if not file:
                return jsonify({"success": False, "message": "Missing file"}), 400
            service.upload_file(file, deposition_id)

        return jsonify('File uploaded succesfully'), 201
    except Exception as e:
        error_message = f"Failed to upload files. Error details: {e}"
        raise Exception(error_message)


@api_bp.route('/api/fakenodo/depositions/<int:deposition_id>', methods=['GET', 'DELETE'])
def deposition(deposition_id):
    try:
        # Target deposition
        deposition = service.get_deposition(deposition_id)

        def get_deposition():
            resposne = deposition.to_dict()
            return jsonify(resposne), 200

        def delete_deposition():
            service.delete_deposition(deposition)
            return jsonify(f"Deposition with id {deposition_id} deleted succesfully"), 204

        if request.method == 'GET':
            return get_deposition()
        else:
            return delete_deposition()

    except Exception:
        return jsonify(f"Cannot find deposition with id {deposition_id}"), 404


@api_bp.route('/api/fakenodo/depositions/<int:deposition_id>/actions/publish', methods=['POST'])
def publish_deposition(deposition_id) -> tuple:
    try:
        # Target deposition
        deposition = service.get_deposition(deposition_id)
        service.generate_doi(deposition_id)
        service.publish_deposition(deposition)
        return jsonify(f"Deposition with id {deposition_id} published succesfully"), 202

    except Exception:
        return jsonify("Deposition not found"), 404


@api_bp.route('/api/fakenodo/depositions/<int:deposition_id>/doi', methods=['GET'])
def get_doi(deposition_id) -> tuple:
    try:
        doi = service.get_doi(deposition_id)
        return jsonify({"doi": doi}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
