from flask import Blueprint, render_template
from webapp import db

main = Blueprint('main', __name__)

@main.route('/login')
def login():
    return render_template('login.html')


@main.route('/signup')
def signup():
    return render_template('signup.html')