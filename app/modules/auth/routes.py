import os
import shutil
import subprocess
from flask import Flask, jsonify, render_template, redirect, url_for, request
from flask_login import current_user, login_user, logout_user
import requests
from app.modules.auth import auth_bp
from app.modules.auth.forms import SignupForm, LoginForm
from app.modules.auth.services import AuthenticationService
from app.modules.profile.services import UserProfileService
from flask_dance.contrib.github import make_github_blueprint, github

from app.modules.dataset.repositories import DataSetRepository

authentication_service = AuthenticationService()
user_profile_service = UserProfileService()

app = Flask(__name__)
#app.config["SECRET_KEY"] = "SECRET KEY  "
token_admin = os.getenv("ORG_TOKEN_ADMIN")

github_blueprint = make_github_blueprint(client_id='Ov23liH3c6144kMW6I2g',
                                        client_secret='00b92023ceb36020d4d0a7f34d5a583e2e386611')

app.register_blueprint(github_blueprint, url_prefix='/github_login')


@auth_bp.route("/signup/", methods=["GET", "POST"])
def show_signup_form():
    if current_user.is_authenticated:
        return redirect(url_for('public.index'))

    form = SignupForm()
    if form.validate_on_submit():
        email = form.email.data
        if not authentication_service.is_email_available(email):
            return render_template("auth/signup_form.html", form=form, error=f'Email {email} in use')

        try:
            user = authentication_service.create_with_profile(**form.data)
        except Exception as exc:
            return render_template("auth/signup_form.html", form=form, error=f'Error creating user: {exc}')

        # Log user
        login_user(user, remember=True)
        return redirect(url_for('public.index'))

    return render_template("auth/signup_form.html", form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('public.index'))

    form = LoginForm()
    if request.method == 'POST' and form.validate_on_submit():
        if authentication_service.login(form.email.data, form.password.data):
            return redirect(url_for('public.index'))

        return render_template("auth/login_form.html", form=form, error='Invalid credentials')

    return render_template('auth/login_form.html', form=form)


@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('public.index'))


@auth_bp.route('/gitlogin')
def github_login():
    
   if not github.authorized:
       return redirect(url_for('github.login'))
   else:
       account_info = github.get('/user/repos')
       if account_info.ok:
           account_info_json = account_info.json()
           return '<h1>Your Github repo is {}'.format(account_info_json[1]['name'])

   return '<h1>Request failed!</h1>'


@auth_bp.route('/invite', methods=['GET', 'POST'])
def invite_user():
    account_info = github.get('/user')
    
    if account_info.ok:
        username = account_info.json()['login']
    else:
        return '<h1>First sync your github account</h1>'
              
    # INVITACION A LA ORGANIZACION
    url = f'https://api.github.com/orgs/uvlhub/invitations'  
    headers = {
        'Authorization': f'token {token_admin}',
        'Accept': 'application/vnd.github.v3+json'
    }
    payload = {
        "invitee_id": None, 
    }

    # OBTENER EL ID DEL USUARIO DE GITHUB
    user_url = f'https://api.github.com/users/{username}'
    user_response = requests.get(user_url, headers=headers)
    
    if user_response.status_code == 200:
        user_id = user_response.json().get("id")
        payload["invitee_id"] = user_id  
    else:
        return jsonify({"error": f"No se pudo encontrar el usuario {username}"}), 404

    # ENVIA LA INVITACION AL USUARIO
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 201:
        return jsonify({"message": f"Invitación enviada a {username} exitosamente."}), 201
    
    elif response.status_code == 404:
        return jsonify({"error": f"Usuario {username} no encontrado."}), 404
    
    else:
        return jsonify({"error": "No se pudo enviar la invitación", "details": response.json()}), response.status_code
    


@auth_bp.route('/create_repo', methods=['GET', 'POST'])
def crear_repo():

    #A PARTIR DE AQUI EL USERNAME SERA EL DE UVLHUB 
    nombre_repositorio = "Javiruizg"

    # Definir el comando que se ejecutará
    comando = f"gh repo create uvlhub/{nombre_repositorio} --public"
    url_repo = f"https://github.com/uvlhub/{nombre_repositorio}.git"
    
    try:
        # Ejecutar el comando en el sistema
        subprocess.run(comando, check=True, shell=True)
        subprocess.run(f"git clone {url_repo}", check=True, shell=True)
        return f"Repositorio '{nombre_repositorio}' creado exitosamente en la organización uvlhub."
    except subprocess.CalledProcessError as e:
        return f"Hubo un error al crear el repositorio: {e}"
    
    
    
@auth_bp.route('/commit', methods=['GET','POST'])
def hacer_commit():
    
    try:
        # Cambiar al directorio del repositorio
        
        ruta_repositorio = os.path.join(os.getcwd(), "Javiruizg")
        
        # Corregir el cambio de directorio en cada ejecución
        if os.path.basename(os.getcwd()) != "Javiruizg":
            os.chdir(ruta_repositorio)
        
        dataset_repository = DataSetRepository()
        all_files = dataset_repository.get_all_files_for_dataset(1)
        print(all_files)
        
        archivos_a_subir = [f.name for f in all_files]
        
        # Ejecutar git add, git commit y git push
        for archivo in archivos_a_subir:

            ruta_archivo_origen = f"/home/javier/uvlhub/app/modules/dataset/uvl_examples/{archivo}"
            ruta_destino_archivo = os.path.join(ruta_repositorio, os.path.basename(ruta_archivo_origen))
            # Copiar el archivo desde la ruta de origen a la carpeta del repositorio
            shutil.copy(ruta_archivo_origen, ruta_destino_archivo)
            print(archivo)
            subprocess.run(f"git add {os.getcwd()}/{archivo}", check=True, shell=True)
            
        subprocess.run('git commit -m "Commit realizado desde Flask"', check=True, shell=True)
        subprocess.run("git push origin main", check=True, shell=True)

        return "Los cambios han sido commiteados y enviados al repositorio con éxito."

    except subprocess.CalledProcessError as e:
        return f"Hubo un error al hacer commit y push: {e.stderr}"
