# STEDdeconvolution
The script 'deconvolve_STED_data.py' deconvolves STED microscopic images recorded with Abberior's Imspector software. The input files are provided in the msr format.
The script asks the user to choose a folder containing msr files, loads all images in these msr files (using the 
pyoformat wrapper for python-bioformats) and applies the deconvolution to all images with the string "STED" in their image name. 

The deconvolution is calculated via the Richardson-Lucy algorithm (20 iterations).
The PSF is a bivariate Cauchy distribution (called Lorentzian_2d in Imspector) with width parameter gamma = 40nm.
The field of view of the STED images is assumed to be 10x10 micrometers. 
Please change these parameters as needed for your data.

Finally, the deconvolved images are stored in different color schemes (grey scale, green channel, red channel, fire/afmhot). 

Required modules:
numpy, matplotlib, PIL, tkinter, skimage, bioformats, javabridge, pyoformats

The installation of javabridge and python-bioformats can be tricky. A very helpful guide can be found at
https://git.ista.ac.at/csommer/pyoformats/-/blob/master/Installation.md


The script 'measure_ring_radius_STED.py' uses the the deconvolved images to detect ring structures and measure their diameters.
In brief, after preprocessing (thresholding, de-noising) we apply the Watershed algorithm (Python's OpenCV library)
to detect candidate structures. These candidate structures are then filtered according to size and roundness.
Roundness is defined as 4 * pi * A / u^2, where A is the area and u the perimeter of the detected structures.
If structures are judged 'not round', we split them along their longer axis and test whether the resulting two structures
are rings (higher intensity outside than inside) that satisfy the criteria for size and roundness. The results are stored in csv files.

Required modules: os, csv, numpy, matplotlib, cv2, scikit-learn, tkinter
