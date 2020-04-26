# Flask, Authentication
from flask import Flask, Blueprint, render_template, request, send_from_directory
from flask_login import login_required, current_user
# Algorithms
from webapp.algorithms.lsb.lsb import hide_data, recover_data
# Metrics
import cv2
import sys
from metrics.metrics import SSIM, MSE, Histogram, show_lsb
# Misc
from webapp import config
import os
import glob

auth = Blueprint('auth', __name__)

# ============================== Images ==============================
MEDIA_FOLDER = os.path.normcase(os.getcwd() + '/webapp/static/images/')
@auth.route('/images/<path:filename>')
@login_required
def download_file(filename):
    return send_from_directory(MEDIA_FOLDER, filename, as_attachment=True)


# ============================== Dashboard ==============================
@auth.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('dashboard.html', name=current_user.name)
    return render_template('index.html')

@auth.route('/dashboard', methods=['POST'])
@login_required
def dashboard_run():
    args = {}
    args['name'] = current_user.name
    if request.form.get('action') == 'compare':
        try:
            args['image_file'] = request.form.get('image_file')
        except:
            args['image_file_error'] = 'ERROR'
    elif request.form.get('action') == 'clear':
        fileList = glob.glob(MEDIA_FOLDER + '**/*.png', recursive=True)
        for file_name in fileList:
            if 'input' not in file_name:
                os.remove(file_name)
    return render_template('dashboard.html', **args)


# ============================== Algorithms ==============================
# GAN 
@auth.route('/gan')
@login_required
def gan_page():
    return render_template('algorithms/gan.html', name=current_user.name)


@auth.route('/gan', methods=['POST'])
@login_required
def gan_run():
    if not config.GAN:
        return render_template('algorithms/gan.html', name=current_user.name)
    from steganogan import SteganoGAN
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
            args['payload'] = sys.getsizeof(args['secret_message'].encode('utf-16'))* 8
            args['capacity'] = round((args['payload'] / args['pixels']),6)
            return render_template('algorithms/gan.html', **args)
        except:
            return render_template('algorithms/gan.html', name=current_user.name)
    elif request.form.get('action') == 'decode':
        try:
            args['decode_message'] = steganogan.decode(output_file)
            args['payload'] = sys.getsizeof(args['decode_message'].encode('utf-16'))* 8
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
            # LSB
            show_lsb(output_file, 1, 'gan')
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
            args['payload'] = sys.getsizeof(args['secret_message'].encode('utf-16'))* 8
            args['capacity'] = round((args['payload'] / args['pixels']),4)
            return render_template('algorithms/lsb.html', **args)
        except:
            return render_template('algorithms/lsb.html', name=current_user.name)
    elif request.form.get('action') == 'decode':
        try:
            args['decode_message'] = recover_data(output_file, args['nbits'])
            args['payload'] = sys.getsizeof(args['decode_message'].encode('utf-16')) * 8
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
            # LSB
            show_lsb(output_file, args['nbits'], 'lsb')
            return render_template('algorithms/lsb.html', **args)
        except:
            return render_template('algorithms/lsb.html', name=current_user.name)
