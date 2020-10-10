from flask import Blueprint, render_template

main = Blueprint('main', __name__)

# ============================== Authentication ==============================
@main.route('/signup')
def signup():
    return render_template('signup.html')