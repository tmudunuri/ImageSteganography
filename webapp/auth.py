# Flask, Authentication
from flask import Flask, Blueprint, render_template, request, send_from_directory
from flask_login import login_required, current_user
# Algorithms
from webapp.algorithms.lsb.lsb import hide_data, recover_data
from webapp.algorithms.svd.svd import Steganographer
from webapp.algorithms.dct.dct import DCT
from webapp.algorithms.pvd.pvdEmbed import pvdEmbed
from webapp.algorithms.pvd.pvdExtract import pvdExtract
# Metrics
import cv2
import sys
from metrics.metrics import SSIM, MSE, Histogram, show_lsb
from webapp.utils import runlog, savelog
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

    steganogan = SteganoGAN.load(architecture=model, cuda=False, verbose=True)

    if request.form.get('action') == 'encode':
        try:
            steganogan.encode(input_file, output_file, args['secret_message'])
            args['payload'] = sys.getsizeof(args['secret_message'].encode('utf-16'))* 8
            args['capacity'] = round((args['payload'] / args['pixels']),6)
            runlog(item=args['image_file'], model=model, msg=args['secret_message'], algo='gan')
            return render_template('algorithms/gan.html', **args)
        except:
            return render_template('algorithms/gan.html', name=current_user.name)
    elif request.form.get('action') == 'decode':
        try:
            try:
                args['decode_message'] = steganogan.decode(output_file) if config.GAN_DECODE else 0/0
            except:
                args['decode_message'] = savelog(item=args['image_file'], model=model, algo='gan')
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

# SVD
@auth.route('/svd')
@login_required
def svd_page():
    return render_template('algorithms/svd.html', name=current_user.name)

@auth.route('/svd', methods=['POST'])
@login_required
def svd_run():
    args = {}
    args['name'] = current_user.name
    args['secret_message'] = request.form.get('secret_message')
    args['image_file'] = request.form.get('image_file')

    input_file = os.path.normcase(MEDIA_FOLDER + 'input/' + args['image_file'])
    output_file = os.path.normcase(MEDIA_FOLDER + 'svd/output/' + args['image_file'])

    height, width, args['channels'] = cv2.imread(input_file).shape
    args['dimensions'] = (str(height) + ' x ' + str(width))
    args['pixels'] = (height * width)

    if request.form.get('action') == 'encode':
        try:
            stego = Steganographer(method='embed', input_file = input_file,output_file = output_file, secret_message = args['secret_message'])
            args['payload'] = sys.getsizeof(args['secret_message'].encode('utf-16'))* 8
            args['capacity'] = round((args['payload'] / args['pixels']),4)
            stego.run()
            runlog(item=args['image_file'], msg=args['secret_message'], algo='svd')
            return render_template('algorithms/svd.html', **args)
        except:
            return render_template('algorithms/svd.html', name=current_user.name)
    elif request.form.get('action') == 'decode':
        try:
            stego = Steganographer(method='decode', input_file = output_file)
            try:
                args['decode_message'] = stego.deccode()
            except:
                args['decode_message'] = savelog(item=args['image_file'], algo='svd')
            args['payload'] = sys.getsizeof(args['decode_message'].encode('utf-16')) * 8
            args['capacity'] = round((args['payload'] / args['pixels']),4)
        except:
            args['decode_message'] = 'ERROR'
            args['dimensions'] = args['channels'] = args['pixels'] = args['payload'] =  args['capacity'] = 'Error'
        return render_template('algorithms/svd.html', **args)
    elif request.form.get('action') == 'calculate':
        try:
            psnr_val = round(cv2.PSNR(cv2.imread(input_file), cv2.imread(output_file)), 2)
            ssim_val = round(SSIM(cv2.imread(input_file), cv2.imread(output_file), 'svd', args['image_file']), 2)
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
            show_lsb(output_file, 1, 'svd')
            return render_template('algorithms/svd.html', **args)
        except:
            return render_template('algorithms/svd.html', name=current_user.name)

# DCT
@auth.route('/dct')
@login_required
def dct_page():
    return render_template('algorithms/dct.html', name=current_user.name)

@auth.route('/dct', methods=['POST'])
@login_required
def dct_run():
    args = {}
    args['name'] = current_user.name
    args['secret_message'] = request.form.get('secret_message')
    args['image_file'] = request.form.get('image_file')

    input_file = os.path.normcase(MEDIA_FOLDER + 'input/' + args['image_file'])
    output_file = os.path.normcase(MEDIA_FOLDER + 'dct/output/' + args['image_file'])

    height, width, args['channels'] = cv2.imread(input_file).shape
    args['dimensions'] = (str(height) + ' x ' + str(width))
    args['pixels'] = (height * width)

    if request.form.get('action') == 'encode':
        try:
            stego = DCT(input_file = input_file)
            stego.DCTEn(args['secret_message'], output_file)
            args['payload'] = sys.getsizeof(args['secret_message'].encode('utf-16'))* 8
            args['capacity'] = round((args['payload'] / args['pixels']),4)
            return render_template('algorithms/dct.html', **args)
        except:
            return render_template('algorithms/dct.html', name=current_user.name)
    elif request.form.get('action') == 'decode':
        try:
            stego = DCT(input_file = output_file)
            args['decode_message'] = stego.DCTDe()
            args['payload'] = sys.getsizeof(args['decode_message'].encode('utf-16')) * 8
            args['capacity'] = round((args['payload'] / args['pixels']),4)
        except:
            args['decode_message'] = 'ERROR'
            args['dimensions'] = args['channels'] = args['pixels'] = args['payload'] =  args['capacity'] = 'Error'
        return render_template('algorithms/dct.html', **args)
    elif request.form.get('action') == 'calculate':
        try:
            psnr_val = round(cv2.PSNR(cv2.imread(input_file), cv2.imread(output_file)), 2)
            ssim_val = round(SSIM(cv2.imread(input_file), cv2.imread(output_file), 'dct', args['image_file']), 2)
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
            show_lsb(output_file, 1, 'dct')
            return render_template('algorithms/dct.html', **args)
        except:
            return render_template('algorithms/dct.html', name=current_user.name)


# PVD
@auth.route('/pvd')
@login_required
def pvd_page():
    return render_template('algorithms/pvd.html', name=current_user.name)

@auth.route('/pvd', methods=['POST'])
@login_required
def pvd_run():
    args = {}
    args['name'] = current_user.name
    args['secret_message'] = request.form.get('secret_message')
    args['image_file'] = request.form.get('image_file')

    input_file = os.path.normcase(MEDIA_FOLDER + 'input/' + args['image_file'])
    output_file = os.path.normcase(MEDIA_FOLDER + 'pvd/output/' + args['image_file'])

    height, width, args['channels'] = cv2.imread(input_file).shape
    args['dimensions'] = (str(height) + ' x ' + str(width))
    args['pixels'] = (height * width)

    if request.form.get('action') == 'encode':
        try:
            stego = pvdEmbed(input_file = input_file, output_file = output_file, secret = args['secret_message'])
            stego.embed()
            args['payload'] = sys.getsizeof(args['secret_message'].encode('utf-16'))* 8
            args['capacity'] = round((args['payload'] / args['pixels']),4)
            return render_template('algorithms/pvd.html', **args)
        except:
            return render_template('algorithms/pvd.html', name=current_user.name)
    elif request.form.get('action') == 'decode':
        try:
            stego = pvdExtract(output_file = output_file)
            args['decode_message'] = stego.extract()
            args['payload'] = sys.getsizeof(args['decode_message'].encode('utf-16')) * 8
            args['capacity'] = round((args['payload'] / args['pixels']),4)
        except:
            args['decode_message'] = 'ERROR'
            args['dimensions'] = args['channels'] = args['pixels'] = args['payload'] =  args['capacity'] = 'Error'
        return render_template('algorithms/pvd.html', **args)
    elif request.form.get('action') == 'calculate':
        try:
            psnr_val = round(cv2.PSNR(cv2.imread(input_file), cv2.imread(output_file)), 2)
            ssim_val = round(SSIM(cv2.imread(input_file), cv2.imread(output_file), 'pvd', args['image_file']), 2)
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
            show_lsb(output_file, 1, 'pvd')
            return render_template('algorithms/pvd.html', **args)
        except:
            return render_template('algorithms/pvd.html', name=current_user.name)