# STEDdeconvolution
This script deconvolves STED microscopic images recorded with Abberior's Imspector software. The input files are provided in the msr format.
The script asks the user to choose a folder with msr files, loads all images contained in the msr files in the given folder (using the 
pyoformat wrapper for python-bioformats) and applies the deconvolution to the images with the string "STED" in their image name. 

The deconvolution is calculated via the Richardson-Lucy algorithm (20 iterations).
The PSF is a bivariate Cauchy distribution (called Lorentzian_2d in Imspector) with width parameter gamma = 40nm.
The field of view of the STED images is assumed to be 10x10 micrometers. 
Please change these parameters as needed for data.

Finally, the deconvolved images are stored in different color schemes (grey scale, green channel, red channel, fire/afmhot). 

Required modules:
numpy, matplotlib, PIL, tkinter, skimage, bioformats, javabridge, pyoformats

The installation of javabridge and python-bioformats can be tricky. A very helpful guide can be found at
https://git.ista.ac.at/csommer/pyoformats/-/blob/master/Installation.md
