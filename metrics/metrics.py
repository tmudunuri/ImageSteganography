from skimage.metrics import structural_similarity
import argparse
import imutils
import cv2
import os
import numpy as np
# histogram
import matplotlib.pyplot as plt

WORKING_DIR = os.path.normcase(os.getcwd())


def SSIM(imageA, imageB, image_file):
    # convert the images to grayscale
    grayA = cv2.cvtColor(imageA, cv2.COLOR_BGR2GRAY)
    grayB = cv2.cvtColor(imageB, cv2.COLOR_BGR2GRAY)

    (score, diff) = structural_similarity(grayA, grayB, full=True)
    diff = (diff * 255).astype("uint8")

    thresh = cv2.threshold(diff, 0, 255,
                           cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                            cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)

    for c in cnts:
        # compute the bounding box of the contour and then draw the
        # bounding box on both input images to represent where the two
        # images differ
        (x, y, w, h) = cv2.boundingRect(c)
        cv2.rectangle(imageA, (x, y), (x + w, y + h), (0, 0, 255), 2)
        cv2.rectangle(imageB, (x, y), (x + w, y + h), (0, 0, 255), 2)

    MEDIA_FOLDER = os.path.normcase(WORKING_DIR + '/images/gan/metrics/ssim/')
    # cv2.imwrite(MEDIA_FOLDER + '/gan/ip/' + image_file, imageA)
    cv2.imwrite(MEDIA_FOLDER + '/gan/op/' + image_file, imageB)
    cv2.imwrite(MEDIA_FOLDER + '/gan/diff/' + image_file, diff)
    cv2.imwrite(MEDIA_FOLDER + '/gan/thresh/' + image_file, thresh)

    return score


def MSE(imageA, imageB):
    imageA = cv2.cvtColor(imageA, cv2.COLOR_BGR2GRAY)
    imageB = cv2.cvtColor(imageB, cv2.COLOR_BGR2GRAY)
    # error_value = np.sum((imageA.astype("float") - imageB.astype("float")) ** 2)
    # error_value /= float(imageA.shape[0] * imageA.shape[1])
    error_value = np.square(np.subtract(
        imageA.astype("float"), imageB.astype("float"))).mean()
    return error_value


def Histogram(image):
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    hist = cv2.calcHist([gray_image], [0], None, [256], [0, 256])
    flatten = lambda l: [item for sublist in l for item in sublist]
    # Colour 
    # for i, col in enumerate(['b', 'g', 'r']):
    #     hist = cv2.calcHist([image], [i], None, [256], [0, 256])
    # plt.plot(hist, color='k')
    # plt.show()
    return flatten(hist)