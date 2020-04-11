from flask import Blueprint, render_template, redirect, url_for, request, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from steganogan import SteganoGAN
import os
from webapp.models import User
from webapp import db

auth = Blueprint('auth', __name__)

# ============================== Authentication ==============================
@auth.route('/login')
def login():
    return render_template('login.html')

@auth.route('/signup')
def signup():
    return render_template('signup.html')

@auth.route('/signup', methods=['POST'])
def signup_post():
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')
    password_confirm = request.form.get('password_confirm')

    if password != password_confirm:
        flash("Passwords don't match.")
        return redirect(url_for('auth.signup'))

    user = User.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database

    if user: # if a user is found, we want to redirect back to signup page so user can try again
        flash('Account already exists. You may login.')
        return redirect(url_for('auth.login'))

    # create new user with the form data. Hash the password so plaintext version isn't saved.
    new_user = User(email=email, name=name, password=generate_password_hash(password, method='sha256'))

    # add the new user to the database
    db.session.add(new_user)
    db.session.commit()
    flash('Signup successful. You may login with email ' + email)

    return redirect(url_for('auth.login'))

@auth.route('/login', methods=['POST'])
def login_post():

    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = User.query.filter_by(email=email).first()

    # check if user actually exists take the user supplied password, hash it, and compare it to the hashed password in database
    if not user or not check_password_hash(user.password, password):
        flash('Please check your login credentials and try again.')
        return redirect(url_for('auth.login')) # if user doesn't exist or password is wrong, reload the page

    # if the above check passes, then we know the user has the right credentials
    login_user(user, remember=remember)
    return redirect(url_for('main.index'))

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been successfully logged out.')
    return redirect(url_for('main.index'))

@auth.route('/delete_user')
@login_required
def delete_user():
    user = User.query.filter_by(email=current_user.email).first()
    db.session.delete(user)
    db.session.commit()
    flash('User ' + current_user.email + ' has been deleted.')
    return redirect(url_for('main.index'))

# ============================== Images ==============================
MEDIA_FOLDER = os.path.normcase(os.getcwd() + '/images')
@auth.route('/images/<path:filename>')
@login_required
def download_file(filename):
    return send_from_directory(MEDIA_FOLDER, filename, as_attachment=True)

# ============================== Algorithms ==============================
@auth.route('/gan')
@login_required
def gan():
    return render_template('algorithms/gan.html', name=current_user.name)

@auth.route('/gan', methods=['POST'])
@login_required
def gan_run():
    secret_message = request.form.get('secret_message')
    image_file = request.form.get('image_file')
    dense = 'dense' if request.form.get('dense') else 'basic'

    steganogan = SteganoGAN.load(dense)
    if request.form.get('action') == 'encode':
        try:
            steganogan.encode('images/input/' + image_file, 'images/output/' + image_file, secret_message)
            return render_template('algorithms/gan.html', name=current_user.name, image_file = image_file)
        except:
            return render_template('algorithms/gan.html', name=current_user.name)
    elif request.form.get('action') == 'decode':
        try:
            decode_message = steganogan.decode('images/output/' + image_file)
        except:
            decode_message = 'Unable to decode message'
        return render_template('algorithms/gan.html', name=current_user.name, decode_message = decode_message, image_file = image_file)