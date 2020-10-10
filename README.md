
# **StegoApp** - *Generate stego-image.*

A web application to embed secret data into cover images to produce stego-images using:

 1. [DCT](#dct)
 2. [SVD](#svd)
 3. [LSB](#lsb)
 4. [PVD](#pvd)
 5. [GAN](#gan)
 
##### **Technologies** : Python, Flask, AWS Cognito, Torch, JavaScript, Bootstrap, HTML, CSS, Docker

## Techniques

> The following techniques are studied and compared closely:

### DCT
The discrete cosine transform (DCT) helps separate the image into parts (or spectral sub-bands) of differing importance (with respect to the image's visual quality). The DCT is similar to the discrete Fourier transform: it transforms a signal or image from the spatial domain to the frequency domain
![DCT](/README/01_DCT.PNG)

### SVD
The Singular Value Decomposition (SVD) is one of the generally utilized apparatuses in straight polynomial math, having applications in information stowing away, picture
pressure, and numerous other sign handling zones.

### LSB
The secret to be embedded replaces the least significant bit in the image. It's a
common technique used to embed arbitrary data within images. It is simple to perform but
is dangerously vulnerable to loss of quality due to compression and image manipulation.
![LSB](/README/03_LSB.PNG)

### PVD
Effective use of both the outstanding step-by-stego piece and the embedding is
done. Separation system is separated into appropriate blocks of two pixels in the initial
image and the pixel discrepancy can be modified in each data block.
![PVD](/README/04_PVD.PNG)

### GAN
The model generates a cover picture that acts as a holder that can produce a safe
steganography of the images to fool the defined form of steganalysis. The embedding
scheme of LSB-match is applied to SGANs to produce respective holders for
steganography.
![GAN](/README/05_GAN.PNG)


## Overview

![Overview](/README/01_Overview.PNG)

## Class Diagram

![Class Diagram](/README/02_Class.PNG)

## Dashboard

![Dashboard](/README/03_Dashboard.PNG)

## Analysis

![Analysis](/README/04_Analysis.PNG)

## Histogram

![Histogram](/README/05_Histogram.PNG)
