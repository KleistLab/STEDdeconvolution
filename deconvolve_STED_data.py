#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 28 13:53:07 2023

@author: eric
"""

# import necessary modules
import os
import glob
import numpy as np
import matplotlib.pyplot as plt
from skimage import restoration
import bioformats
import javabridge
from pyoformats import read
from PIL import Image
from tkinter import Tk, filedialog

 # start java virtual environment to communicate with bioformats
javabridge.start_vm(class_path=bioformats.JARS)

def cauchy2d(x_eval, y_eval, x_0, y_0, gamma):
    """
    PDF of the bivariate Cauchy distribution aka Lorentzian function
    """
    denom = (x_eval - x_0)**2 + (y_eval - y_0)**2 + gamma**2
    full = gamma / denom**1.5
    return full / 2 / np.pi

# ask the user in what path the msr files are
root = Tk()
root.withdraw()
PATH = filedialog.askdirectory()
# go to that path
os.chdir(PATH)
# get the names of all msr files in PATH
FILENAMES = glob.glob('*.msr')
# loop through these msr files
for FILE in FILENAMES:
    # create a folder for each .msr file and store the images
    # in one of four subfolders (grey, red, green, fire)
    FILE_wo_msr = FILE.split('.', maxsplit=1)[0]
    os.makedirs(FILE_wo_msr + '/grey/')
    os.makedirs(FILE_wo_msr + '/green/')
    os.makedirs(FILE_wo_msr + '/red/')
    os.makedirs(FILE_wo_msr + '/fire/')
    # use pyoformats' read module
    read.file_info(FILE)
    for s, data in read.image_5d_iterator(os.path.join(PATH, FILE)):
        # pick the images that contain 'STED' in their name
        if 'STED' in s:
            # convert data to array and make it two-dimensional
            dat = np.array(data)[0, 0, 0, :, :]
            # create the kernel for deconvolution
            xkernel, ykernel = np.meshgrid(np.linspace(-10/2, 10/2, dat.shape[0]),
                                           np.linspace(-10/2, 10/2, dat.shape[1]))
                                           # 10um field of view, change here if you want
                                           # something else
            kernel = cauchy2d(xkernel, ykernel, 0, 0, 0.04) # 0.04 is the PSF width, gamma,
            						    # in um, change here if you want 
            						    # something else 
            kernel /= np.max(kernel) # probably not necessary
            # perform the deconvolution
            deconvolved = restoration.richardson_lucy(dat, kernel, num_iter=20, clip=False)
            # rescale the result to [0, 255] integers
            deconvolved = np.array(deconvolved / deconvolved.max() * 255, dtype='uint8')
            
            # save file to tif, greyscale image
            im = Image.fromarray(deconvolved)
            im.save('./' + FILE_wo_msr + '/grey/' + FILE_wo_msr + '_' + s + '_greyscale.tif')
            
            # save array in green channel
            rgb_array = np.zeros((deconvolved.shape[0], deconvolved.shape[1], 3)).astype(np.uint8)
            rgb_array[..., 1] = deconvolved
            im_g = Image.fromarray(rgb_array, mode='RGB')
            im_g.save('./' + FILE_wo_msr + '/green/' + FILE_wo_msr + '_' + s + '_green.tif')

            # save array in red channel
            rgb_array = np.zeros((deconvolved.shape[0], deconvolved.shape[1], 3)).astype(np.uint8)
            rgb_array[..., 0] = deconvolved
            im_r = Image.fromarray(rgb_array, mode='RGB')
            im_r.save('./' + FILE_wo_msr + '/red/' + FILE_wo_msr + '_' + s + '_red.tif')
            
            # matplotlib does not have abberior's 'fire' colormap
            # but matplotlib's 'afmhot' seems close            
            deconvolved = deconvolved / deconvolved.max()
            cmap = plt.cm.get_cmap('afmhot')
            colormap_array = cmap(deconvolved)
            colormap_array = (colormap_array[:, :, :3] * 255).astype(np.uint8)
            im_hot = Image.fromarray(colormap_array, mode='RGB')
            im_hot.save('./' + FILE_wo_msr + '/fire/' + FILE_wo_msr + '_' + s + '_afmhot.tif')
            
# kill java virtual environment
javabridge.kill_vm()
