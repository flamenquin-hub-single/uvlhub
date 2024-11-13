import os
from flask import Flask, jsonify, render_template, redirect, url_for, request
from flask_login import current_user, login_user, logout_user
import requests
from app.modules.auth import auth_bp
from app.modules.auth.forms import SignupForm, LoginForm
from app.modules.auth.services import AuthenticationService
from app.modules.profile.services import UserProfileService
from flask_dance.contrib.github import make_github_blueprint, github

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
        #username = "Javiruizg"
         
        # API de GitHub para invitar a un usuario a una organización
        url = f'https://api.github.com/orgs/uvlhub/invitations'  
        headers = {
            'Authorization': f'token {token_admin}',
            'Accept': 'application/vnd.github.v3+json'
        }
        payload = {
            "invitee_id": None,  # Esta es una asignación temporal
        }

        # Obtener el ID del usuario desde la API de GitHub
        user_url = f'https://api.github.com/users/{username}'
        user_response = requests.get(user_url, headers=headers)
        
        if user_response.status_code == 200:
            user_id = user_response.json().get("id")
            payload["invitee_id"] = user_id  # Actualizo el invitee_id con el ID real del usuario de github
        else:
            return jsonify({"error": f"No se pudo encontrar el usuario {username}"}), 404

        # Enviar la invitación a la organización
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 201:
            return jsonify({"message": f"Invitación enviada a {username} exitosamente."}), 201
        elif response.status_code == 404:
            return jsonify({"error": f"Usuario {username} no encontrado."}), 404
        else:
            return jsonify({"error": "No se pudo enviar la invitación", "details": response.json()}), response.status_code
        
    else:
        return '<h1>Request failed! First sync your account with github</h1>'