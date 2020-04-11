from flask import Blueprint, render_template
from flask_login import login_required, current_user
from steganogan import SteganoGAN
from webapp import db

main = Blueprint('main', __name__)

@main.route('/')
@login_required
def index():
    steganogan = SteganoGAN.load('basic')
    steganogan.encode('images/input.png', 'images/output.png', 'This is a super secret message!')
    return render_template('index.html', name=current_user.name)
