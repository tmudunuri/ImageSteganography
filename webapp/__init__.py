from flask import Flask, render_template, session, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user
from webapp import config, utils
from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth
import os

# ============================== Flask App ==============================
def create_app():
    app = Flask(__name__)

    app.register_error_handler(404, utils.page_not_found)
    app.config.from_pyfile('config.py')

    # blueprint for auth routes in our app
    from webapp.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    # blueprint for non-auth parts of app
    from webapp.main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    login_manager = LoginManager()
    login_manager.login_view = 'login'
    login_manager.init_app(app)

    # ============================== AWSCognito ==============================
    @login_manager.user_loader
    def user_loader(session_token):
        """Populate user object, check expiry"""
        if "expires" not in session:
            return None

        expires = datetime.utcfromtimestamp(session['expires'])
        expires_seconds = (expires - datetime.utcnow()).total_seconds()
        if expires_seconds < 0:
            return None

        user = utils.User()
        user.id = session_token
        user.name = session['name']
        return user


    @app.route("/login")
    def login():
        # http://docs.aws.amazon.com/cognito/latest/developerguide/login-endpoint.html
        config.AWS_COGNITO_REDIRECT_URL = request.host_url[0:-1]
        session['csrf_state'] = os.urandom(8).hex()
        cognito_login = ("%s/"
                        "login?response_type=code&client_id=%s"
                        "&state=%s"
                        "&redirect_uri=%s/callback" %
                        (config.AWS_COGNITO_DOMAIN, config.AWS_COGNITO_USER_POOL_CLIENT_ID, session['csrf_state'],
                        config.AWS_COGNITO_REDIRECT_URL))
        return redirect(cognito_login)


    @app.route("/callback")
    def callback():
        #http://docs.aws.amazon.com/cognito/latest/developerguide/token-endpoint.html
        csrf_state = request.args.get('state')
        code = request.args.get('code')
        request_parameters = {'grant_type': 'authorization_code',
                            'client_id': config.AWS_COGNITO_USER_POOL_CLIENT_ID,
                            'code': code,
                            "redirect_uri": config.AWS_COGNITO_REDIRECT_URL + "/callback"}
        response = requests.post("%s/oauth2/token" % config.AWS_COGNITO_DOMAIN,
                                data=request_parameters,
                                auth=HTTPBasicAuth(config.AWS_COGNITO_USER_POOL_CLIENT_ID,
                                                    config.AWS_COGNITO_USER_POOL_CLIENT_SECRET))

        # http://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-with-identity-providers.html
        if response.ok and csrf_state == session['csrf_state']:
            utils.verify(response.json()["access_token"])
            id_token = utils.verify(response.json()["id_token"], response.json()["access_token"])

            user = utils.User()
            user.id = id_token["cognito:username"]
            session['name'] = id_token["name"]
            session['expires'] = id_token["exp"]
            session['refresh_token'] = response.json()["refresh_token"]
            login_user(user, remember=True)
            return redirect(url_for("auth.index"))


    @app.route("/logout")
    def logout():
        # http://docs.aws.amazon.com/cognito/latest/developerguide/logout-endpoint.html
        logout_user()
        cognito_logout = ("%s/"
                        "logout?response_type=code&client_id=%s"
                        "&logout_uri=%s/" %
                        (config.AWS_COGNITO_DOMAIN, config.AWS_COGNITO_USER_POOL_CLIENT_ID, config.AWS_COGNITO_REDIRECT_URL))
        return redirect(cognito_logout)

    return app
