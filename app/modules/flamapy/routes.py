import os
import zipfile
import tempfile
import logging

from flask import send_file, jsonify, redirect, url_for
from app.modules.hubfile.services import HubfileService
from app.modules.flamapy import flamapy_bp

from flamapy.metamodels.fm_metamodel.transformations import UVLReader, GlencoeWriter, SPLOTWriter
from flamapy.metamodels.pysat_metamodel.transformations import FmToPysat, DimacsWriter

from antlr4 import CommonTokenStream, FileStream
from uvl.UVLCustomLexer import UVLCustomLexer
from uvl.UVLPythonParser import UVLPythonParser
from antlr4.error.ErrorListener import ErrorListener

logger = logging.getLogger(__name__)


@flamapy_bp.route('/flamapy/check_uvl/<int:file_id>', methods=['GET'])
def check_uvl(file_id):
    class CustomErrorListener(ErrorListener):
        def __init__(self):
            self.errors = []

        def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
            if "\\t" in msg:
                warning_message = (
                    f"The UVL has the following warning that prevents reading it: "
                    f"Line {line}:{column} - {msg}"
                )
                print(warning_message)
                self.errors.append(warning_message)
            else:
                error_message = (
                    f"The UVL has the following error that prevents reading it: "
                    f"Line {line}:{column} - {msg}"
                )
                self.errors.append(error_message)

    try:
        hubfile = HubfileService().get_by_id(file_id)
        input_stream = FileStream(hubfile.get_path())
        lexer = UVLCustomLexer(input_stream)

        error_listener = CustomErrorListener()

        lexer.removeErrorListeners()
        lexer.addErrorListener(error_listener)

        stream = CommonTokenStream(lexer)
        parser = UVLPythonParser(stream)

        parser.removeErrorListeners()
        parser.addErrorListener(error_listener)

        # tree = parser.featureModel()

        if error_listener.errors:
            return jsonify({"errors": error_listener.errors}), 400

        # Optional: Print the parse tree
        # print(tree.toStringTree(recog=parser))

        return jsonify({"message": "Valid Model"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@flamapy_bp.route('/flamapy/valid/<int:file_id>', methods=['GET'])
def valid(file_id):
    return jsonify({"success": True, "file_id": file_id})


@flamapy_bp.route('/flamapy/to_glencoe/<int:file_id>', methods=['GET'])
def to_glencoe(file_id):
    temp_file = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
    try:
        hubfile = HubfileService().get_or_404(file_id)
        fm = UVLReader(hubfile.get_path()).transform()
        GlencoeWriter(temp_file.name, fm).transform()

        # Return the file in the response
        return send_file(temp_file.name, as_attachment=True, download_name=f'{hubfile.name}_glencoe.txt')
    finally:
        # Clean up the temporary file
        os.remove(temp_file.name)


@flamapy_bp.route('/flamapy/to_splot/<int:file_id>', methods=['GET'])
def to_splot(file_id):
    temp_file = tempfile.NamedTemporaryFile(suffix='.splx', delete=False)
    try:
        hubfile = HubfileService().get_by_id(file_id)
        fm = UVLReader(hubfile.get_path()).transform()
        SPLOTWriter(temp_file.name, fm).transform()

        # Return the file in the response
        return send_file(temp_file.name, as_attachment=True, download_name=f'{hubfile.name}_splot.txt')
    finally:
        # Clean up the temporary file
        os.remove(temp_file.name)


@flamapy_bp.route('/flamapy/to_cnf/<int:file_id>', methods=['GET'])
def to_cnf(file_id):
    temp_file = tempfile.NamedTemporaryFile(suffix='.cnf', delete=False)
    try:
        hubfile = HubfileService().get_by_id(file_id)
        fm = UVLReader(hubfile.get_path()).transform()
        sat = FmToPysat(fm).transform()
        DimacsWriter(temp_file.name, sat).transform()

        # Return the file in the response
        return send_file(temp_file.name, as_attachment=True, download_name=f'{hubfile.name}_cnf.txt')
    finally:
        # Clean up the temporary file
        os.remove(temp_file.name)

@flamapy_bp.route('/flamapy/export_dataset/<int:dataset_id>/<string:format>', methods=['GET'])
def export_dataset(dataset_id, format):
    """Export all UVL files in the dataset to the specified format and package as a ZIP."""
    hubfile_service = HubfileService()
    files = hubfile_service.get_files_by_dataset_id(dataset_id)

    if not files:
        return jsonify({"error": "No files found for this dataset"}), 404

    with tempfile.TemporaryDirectory() as temp_dir:
        zip_filename = os.path.join(temp_dir, f"dataset_{dataset_id}_{format}.zip")

        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            for file in files:
                uvl_path = file.get_path()
                fm = UVLReader(uvl_path).transform()

                # Transform the file to the desired format
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{format}")
                try:
                    if format == "glencoe":
                        GlencoeWriter(temp_file.name, fm).transform()
                    elif format == "splot":
                        SPLOTWriter(temp_file.name, fm).transform()
                    elif format == "dimacs":
                        sat = FmToPysat(fm).transform()
                        DimacsWriter(temp_file.name, sat).transform()
                    else:
                        return jsonify({"error": "Formato no soportado"}), 400

                    # Add transformed file to ZIP
                    zipf.write(temp_file.name, arcname=f"{file.name}.{format}")
                finally:
                    os.remove(temp_file.name)

        return send_file(zip_filename, as_attachment=True, download_name=f"dataset_{dataset_id}_{format}.zip")