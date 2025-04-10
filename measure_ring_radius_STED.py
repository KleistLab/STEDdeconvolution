#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul  5 15:44:14 2023

@author: eric
"""
import os
import csv
import numpy as np
import matplotlib.pyplot as plt
import cv2 as cv
from sklearn.cluster import KMeans
from tkinter import Tk, filedialog, Entry, Button

# let the user choose the base directory
root = Tk()
root.withdraw()
basedir = filedialog.askdirectory()

# let the user choose the channel
comp_str = 'STAR RED'
win = Tk()

def destroy_window():
    global win
    win.quit()
    win.destroy()

def set_string_alexa():
    global comp_str, win
    comp_str = 'Alexa'
    destroy_window()

win.geometry("300x100")
win.title('Choose a channel')
entry= Entry(win, width= 40)
entry.grid(row = 0, column = 0, columnspan = 2)
button1 = Button(win, text= "Alexa", command=set_string_alexa)
button1.grid(row = 1, column = 0)
button2 = Button(win, text= "Star Red", command=destroy_window)
button2.grid(row = 1, column = 1)
win.mainloop()

# basedir = '/home/eric/Helen_Data/Sted_Ring_diameter/'
r_all_control = np.array([])
r_all_exp = np.array([])
files_export = []
nrrings_export = []
rmean_export = []
Amean_export = []
# img = cv.imread('/home/eric/Helen_Data/BRPS187A_Nc82-AF94_animal1/fire/BRPS187A_Nc82-AF94_animal1_Alexa 594_STED {2}_afmhot.tif')
for root, dirs, files in os.walk(basedir):
    for file in files:
        if file.endswith("_green.tif") and comp_str in file:
            print(file)
            img = cv.imread(os.path.join(root, file))

            gray_all = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
            
            ret, thresh = cv.threshold(gray_all, 0, 255, cv.THRESH_BINARY_INV+cv.THRESH_OTSU)
            kernel = np.ones((3,3),np.uint8)
            opening = cv.morphologyEx(thresh,cv.MORPH_OPEN,kernel, iterations = 2)
            sure_bg = cv.dilate(opening, kernel, iterations=3)
            ret, sure_fg = cv.threshold(opening, 0.9*opening.max(), 255, cv.THRESH_BINARY_INV+cv.THRESH_OTSU)
            sure_fg = np.uint8(sure_fg)
            unknown = cv.subtract(sure_bg,sure_fg)
            ret, markers = cv.connectedComponents(sure_fg)
            markers = markers+1
            markers[unknown==255] = 0
            markers = cv.watershed(img, markers)

            markers = markers.astype(np.uint8)
            ret, m2 = cv.threshold(markers, 0, 255, cv.THRESH_BINARY|cv.THRESH_OTSU)
            contours, hierarchy = cv.findContours(m2, cv.RETR_LIST, cv.CHAIN_APPROX_NONE)
            
            roundness_all = []
            perimeters_all = []
            area_all = []
            fig, ax = plt.subplots(1, 2, figsize=(10, 6))
            ax[0].imshow(gray_all)
            ax[1].imshow(gray_all)
            round_thresh1 = 0.75 # threshold to detect merged rings
            round_thresh2 = 0.7 # final roundness threshold
            allcxy = [[-100, -100]] # usually there are duplicate countours, so we only consider contours with unique centroids
            for j in range(len(contours)):
                cnt = contours[j]
                area = cv.contourArea(cnt)
                perimeter = cv.arcLength(cnt, True)
                roundness = 4*np.pi*area/perimeter**2
                if area > 25 and area < 1000:
                    # there might be multiple-ring systems, measure area for all of them
                    area_all.append(area)
                    if roundness > round_thresh1:
                        # center of mass
                        cx, cy = np.array(np.mean(cnt, axis=0)[0], dtype='int')
                        inner_mean = np.mean(gray_all[cy-1:cy+2, cx-1:cx+2])
                        out_coord = np.unique(np.array((2*cnt[:, 0, :] + np.r_[cx, cy])/3, dtype='int'), axis=0)
                        dat = gray_all[out_coord[:, 1], out_coord[:, 0]]
                        outer_mean = np.mean(dat)
                        # check that the ring is not too bumpy
                        outer_cv = np.std(dat)/np.mean(dat)
                        # print(outer_cv)
                        # check if the inside area has lower intensity than outer ring
                        dist = (np.abs(np.array(allcxy) - np.array([cx, cy])) <= np.ones(2))
                        if inner_mean < outer_mean and not np.logical_and(dist[:, 0], dist[:, 1]).any():
                            roundness_all.append(roundness)
                            perimeters_all.append(perimeter)
                            ax[1].scatter(*cnt.T, s=1)
                            ax[1].text(cx, cy, str(np.round(outer_cv, 2)))
                            allcxy.append([cx, cy])
                    else:
                        # check for merged rings, seperate along the long axis                        
                        dat = cnt[:, 0, :].T
                        # 2-means clustering
                        kmeans = KMeans(n_clusters=2, random_state=0).fit(dat.T) # n_init="auto"
                        cnt1 = cnt[kmeans.labels_==1, :, :]
                        cnt2 = cnt[kmeans.labels_==0, :, :]
                        
                        area1 = cv.contourArea(cnt1)
                        area2 = cv.contourArea(cnt2)
                        perimeter1 = cv.arcLength(cnt1, True)
                        perimeter2 = cv.arcLength(cnt2, True)
                        roundness1 = 4*np.pi*area1/perimeter1**2
                        roundness2 = 4*np.pi*area2/perimeter2**2
                        if roundness1 > round_thresh2:
                            # center of mass
                            cx1, cy1 = np.array(np.mean(cnt1, axis=0)[0], dtype='int')
                            inner_mean = np.mean(gray_all[cy1-1:cy1+2, cx1-1:cx1+2])
                            out_coord = np.unique(np.array((2*cnt1[:, 0, :] + np.r_[cx1, cy1])/3, dtype='int'), axis=0)
                            dat = gray_all[out_coord[:, 1], out_coord[:, 0]]
                            outer_mean = np.mean(dat)
                            # check that the ring is not too bumpy
                            outer_cv = np.std(dat)/np.mean(dat)
                            # check if the inside area has lower intensity than outer ring
                            dist = (np.abs(np.array(allcxy) - np.array([cx1, cy1])) <= np.ones(2))
                            if inner_mean < outer_mean and not np.logical_and(dist[:, 0], dist[:, 1]).any():
                                roundness_all.append(roundness1)
                                perimeters_all.append(perimeter1)
                                ax[1].scatter(*cnt1.T, s=1)
                                ax[1].text(cx1, cy1, str(np.round(outer_cv, 2)))
                                allcxy.append([cx1, cy1])
                        
                        if roundness2 > round_thresh2:
                            # center of mass
                            cx2, cy2 = np.array(np.mean(cnt2, axis=0)[0], dtype='int')
                            # check if the inside area has lower intensity than outer ring
                            inner_mean = np.mean(gray_all[cy2-1:cy2+2, cx2-1:cx2+2])
                            out_coord = np.unique(np.array((2*cnt2[:, 0, :] + np.r_[cx2, cy2])/3, dtype='int'), axis=0)
                            dat = gray_all[out_coord[:, 1], out_coord[:, 0]]
                            outer_mean = np.mean(dat)
                            # # check that the ring is not too bumpy
                            outer_cv = np.std(dat)/np.mean(dat)
                            # print(outer_cv)
                            # make sure the countour has not been considered before
                            dist = (np.abs(np.array(allcxy) - np.array([cx2, cy2])) <=np.ones(2))
                            
                            if inner_mean < outer_mean and not np.logical_and(dist[:, 0], dist[:, 1]).any():
                                roundness_all.append(roundness2)
                                perimeters_all.append(perimeter2)
                                ax[1].scatter(*cnt2.T, s=1)
                                ax[1].text(cx2, cy2, str(np.round(outer_cv, 2)))
                                allcxy.append([cx2, cy2])

            ax[0].set_aspect('equal')
            ax[1].set_aspect('equal')
            plt.savefig(root + '/detected_rings_' + file + '.png')
            plt.close(fig)
            
            # measure radius from perimeter
            roundness = np.array(roundness_all)
            perimeters = np.array(perimeters_all)
            areas = np.array(area_all)
            r = perimeters/np.pi/2# * 10/500
            
            print(file)
            print(len(r))
            print(np.mean(r))
            
            files_export.append(file)
            nrrings_export.append(len(r))
            rmean_export.append(np.mean(r))
            Amean_export.append(np.mean(areas))
            
            # make sure that there are more than 7 rings in an image,
            # discard otherwise
            if len(r) > 7:
                if 'control' in file:
                    r_all_control = np.hstack((r_all_control, r))
                else:
                    r_all_exp = np.hstack((r_all_exp, r))
            
            # resolution: 10um x 10um, 500 x 500 pixel

# writing to csv file
fields = ['file name', 'number of rings', 'average ring radius', 'average area of ALL structures']
filename = 'summary_ringradii.csv'     
with open(filename, 'w') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(fields)
    writer.writerows(np.c_[files_export, nrrings_export, rmean_export, Amean_export])

print('Average radius, control: '+ str(np.round(np.mean(r_all_control), 2)) + ' pixels')
print('Average radius, experiment: '+ str(np.round(np.mean(r_all_exp), 2)) + ' pixels')
