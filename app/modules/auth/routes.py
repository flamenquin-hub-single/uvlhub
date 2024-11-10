from flask import Flask, render_template, redirect, url_for, request
from flask_login import current_user, login_user, logout_user
from app.modules.auth import auth_bp
from app.modules.auth.forms import SignupForm, LoginForm
from app.modules.auth.services import AuthenticationService
from app.modules.profile.services import UserProfileService
from flask_dance.contrib.github import make_github_blueprint, github

authentication_service = AuthenticationService()
user_profile_service = UserProfileService()

app = Flask(__name__)
app.config["SECRET_KEY"] = "SECRET KEY  "

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
