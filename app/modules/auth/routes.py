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
           return '<h1>Your github account is already sync with uvlhub</h1>'

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
        return jsonify({"error": f"Can't find the user: {username}"}), 404

    # ENVIA LA INVITACION AL USUARIO
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 201:
        return f'Invitación enviada a {username} exitosamente. Debe aceptarla desde github y una vez pertenezca a nuestra organización no tenrá que repetir este proceso</h1>'
        #return jsonify({"message": f"Invitación enviada a {username} exitosamente."}), 201
    
    elif response.status_code == 404:
        return jsonify({"error": f"Usuario {username} no encontrado."}), 404
    
    elif response.status_code == 422:
        return f'El usuario {username} ya pertenece a nuestra organización de github o tiene una invitación válida para unirse. Compruébelo desde github'
    
    else:
        return jsonify({"error": "No se pudo enviar la invitación", "details": response.json()}), response.status_code
    


@auth_bp.route('/create_repo', methods=['GET', 'POST'])
def crear_repo():
    
    account_info = github.get('/user')
    
    if account_info.ok:
        username = account_info.json()['login']
    else:
        return '<h1>First sync your github account</h1>'

    # Definir el comando que se ejecutará
    comando = f"gh repo create uvlhub/{username} --public"
    url_repo = f"https://github.com/uvlhub/{username}.git"
    
    try:
        # Ejecutar el comando en el sistema
        subprocess.run(comando, check=True, shell=True)
        subprocess.run(f"git clone {url_repo}", check=True, shell=True)
        return f"Repositorio '{username}' creado exitosamente en la organización uvlhub."
    except subprocess.CalledProcessError as e:
        return f"El repositorio '{username}' ya está creado. Ahora siempre que su cuenta esté sincronizada con github, puede subir desde uvlhub sus archivos a este repositorio."
    
