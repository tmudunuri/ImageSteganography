# Flask, Authentication
from flask import Blueprint, render_template, redirect, url_for, request, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from webapp.models import User
from webapp import db
# Algorithms
from steganogan import SteganoGAN
from lsb.lsb import hide_data, recover_data
# Metrics
import cv2
from metrics.metrics import SSIM, MSE, Histogram
# Misc
import os

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

    # if this returns a user, then the email already exists in database
    user = User.query.filter_by(email=email).first()

    if user:  # if a user is found, we want to redirect back to signup page so user can try again
        flash('Account already exists. You may login.')
        return redirect(url_for('auth.login'))

    # create new user with the form data. Hash the password so plaintext version isn't saved.
    new_user = User(email=email, name=name,
                    password=generate_password_hash(password, method='sha256'))

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
        # if user doesn't exist or password is wrong, reload the page
        return redirect(url_for('auth.login'))

    # if the above check passes, then we know the user has the right credentials
    login_user(user, remember=remember)
    return redirect(url_for('main.index'))


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been successfully logged out.')
    return redirect(url_for('auth.login'))


@auth.route('/delete_user')
@login_required
def delete_user():
    user = User.query.filter_by(email=current_user.email).first()
    db.session.delete(user)
    db.session.commit()
    flash('User ' + current_user.email + ' has been deleted.')
    return redirect(url_for('auth.login'))


# ============================== Images ==============================
MEDIA_FOLDER = os.path.normcase(os.getcwd() + '/images/')
@auth.route('/images/<path:filename>')
@login_required
def download_file(filename):
    return send_from_directory(MEDIA_FOLDER, filename, as_attachment=True)

# ============================== Algorithms ==============================
# GAN 
@auth.route('/gan')
@login_required
def gan_page():
    return render_template('algorithms/gan.html', name=current_user.name)


@auth.route('/gan', methods=['POST'])
@login_required
def gan_run():
    args = {}
    args['name'] = current_user.name
    args['secret_message'] = request.form.get('secret_message')
    args['image_file'] = request.form.get('image_file')
    model = 'dense' if (request.form.get('model') == 'dense') else 'basic'

    input_file = os.path.normcase(MEDIA_FOLDER + 'input/' + args['image_file'])
    output_file = os.path.normcase(MEDIA_FOLDER + 'gan/output/' + args['image_file'])

    height, width, args['channels'] = cv2.imread(input_file).shape
    args['dimensions'] = (str(height) + ' x ' + str(width))
    args['pixels'] = (height * width)

    steganogan = SteganoGAN.load(model)

    if request.form.get('action') == 'encode':
        try:
            steganogan.encode(input_file, output_file, args['secret_message'])
            args['payload'] = (len(args['secret_message'])* 16)
            args['capacity'] = round((args['payload'] / args['pixels']),4)
            return render_template('algorithms/gan.html', **args)
        except:
            return render_template('algorithms/gan.html', name=current_user.name)
    elif request.form.get('action') == 'decode':
        try:
            args['decode_message'] = steganogan.decode(output_file)
            args['payload'] = (len(args['decode_message'])* 16)
            args['capacity'] = round((args['payload'] / args['pixels']),4)
        except:
            args['decode_message'] = 'ERROR'
            args['dimensions'] = args['channels'] = args['pixels'] = args['payload'] =  args['capacity'] = 'Error'
        return render_template('algorithms/gan.html', **args)
    elif request.form.get('action') == 'calculate':
        try:
            psnr_val = round(cv2.PSNR(cv2.imread(input_file), cv2.imread(output_file)), 2)
            ssim_val = round(SSIM(cv2.imread(input_file), cv2.imread(output_file), 'gan', args['image_file']), 2)
            mse_val = round(MSE(cv2.imread(input_file), cv2.imread(output_file)), 2)
            args['psnr'] = psnr_val if psnr_val is not None else 'Error'
            args['mse'] = mse_val if mse_val is not None else 'Error'
            args['ssim'] = ssim_val if ssim_val is not None else 'Error'
            # Histogram
            original = cv2.imread(input_file)
            compressed = cv2.imread(output_file)
            args['histogramCover'] = Histogram(original)
            args['histogramStego'] = Histogram(compressed)
            return render_template('algorithms/gan.html', **args)
        except:
            return render_template('algorithms/gan.html', name=current_user.name)

# LSB
@auth.route('/lsb')
@login_required
def lsb_page():
    return render_template('algorithms/lsb.html', name=current_user.name)

@auth.route('/lsb', methods=['POST'])
@login_required
def lsb_run():
    args = {}
    args['name'] = current_user.name
    args['secret_message'] = request.form.get('secret_message')
    args['image_file'] = request.form.get('image_file')
    args['nbits'] = int(request.form.get('nbits'))

    input_file = os.path.normcase(MEDIA_FOLDER + 'input/' + args['image_file'])
    output_file = os.path.normcase(MEDIA_FOLDER + 'lsb/output/' + args['image_file'])

    height, width, args['channels'] = cv2.imread(input_file).shape
    args['dimensions'] = (str(height) + ' x ' + str(width))
    args['pixels'] = (height * width)

    if request.form.get('action') == 'encode':
        try:
            hide_data(input_file, args['secret_message'], output_file, args['nbits'], 1)
            args['payload'] = (len(args['secret_message'])* 16)
            args['capacity'] = round((args['payload'] / args['pixels']),4)
            return render_template('algorithms/lsb.html', **args)
        except:
            return render_template('algorithms/lsb.html', name=current_user.name)
    elif request.form.get('action') == 'decode':
        try:
            args['decode_message'] = recover_data(output_file, args['nbits'])
            args['payload'] = (len(args['decode_message'])* 16)
            args['capacity'] = round((args['payload'] / args['pixels']),4)
        except:
            args['decode_message'] = 'ERROR'
            args['dimensions'] = args['channels'] = args['pixels'] = args['payload'] =  args['capacity'] = 'Error'
        return render_template('algorithms/lsb.html', **args)
    elif request.form.get('action') == 'calculate':
        try:
            psnr_val = round(cv2.PSNR(cv2.imread(input_file), cv2.imread(output_file)), 2)
            ssim_val = round(SSIM(cv2.imread(input_file), cv2.imread(output_file), 'lsb', args['image_file']), 2)
            mse_val = round(MSE(cv2.imread(input_file), cv2.imread(output_file)), 2)
            args['psnr'] = psnr_val if psnr_val is not None else 'Error'
            args['mse'] = mse_val if mse_val is not None else 'Error'
            args['ssim'] = ssim_val if ssim_val is not None else 'Error'
            # Histogram
            original = cv2.imread(input_file)
            compressed = cv2.imread(output_file)
            args['histogramCover'] = Histogram(original)
            args['histogramStego'] = Histogram(compressed)
            return render_template('algorithms/lsb.html', **args)
        except:
            return render_template('algorithms/lsb.html', name=current_user.name)