from flask import render_template, current_app
from flask_login import UserMixin
import requests
from webapp import config
from jose import jwt

class User(UserMixin):
    pass

JWKS_URL = ("https://cognito-idp.%s.amazonaws.com/%s/.well-known/jwks.json"
            % (config.AWS_DEFAULT_REGION, config.AWS_COGNITO_USER_POOL_ID))
JWKS = requests.get(JWKS_URL).json()["keys"]

def verify(token, access_token=None):
    header = jwt.get_unverified_header(token)
    key = [k for k in JWKS if k["kid"] == header['kid']][0]
    id_token = jwt.decode(token, key, audience=config.AWS_COGNITO_USER_POOL_CLIENT_ID, access_token=access_token)
    return id_token

def page_not_found(e):
  return render_template('404.html'), 404