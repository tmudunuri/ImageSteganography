from flask import Blueprint, render_template
from flask_login import login_required, current_user
from ImageSteganography import db
from ImageSteganography.algorithms.steganogan import SteganoGAN

main = Blueprint('main', __name__)

@main.route('/')
@login_required
def index():
    return render_template('index.html', name=current_user.name)
