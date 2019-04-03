# -*- coding: utf-8 -*-
"""
Created on Mon Jan 21 18:08:48 2019

@author: Fotonica
"""

import numpy as np

from matplotlib import pyplot as plt

from .batch import file_dialog_open, validate_files

from re import split

WINDOWS_NEW_LINE = "\r\n"
UNIX_NEW_LINE = "\n"

HEADER_START_FLAG = "++++++++++++++++++++++++++++++++++++"
SPECTRUM_START_FLAG = ">>>>>Begin Processed Spectral Data<<<<<"
SPECTRUM_END_FLAG = ">>>>>End Processed Spectral Data<<<<<"

def read_spectrum(path, header_lines=None):
    
    separator = "\t"
    split_condition = WINDOWS_NEW_LINE + "|" + UNIX_NEW_LINE + "|" + separator
    
    wavelength = np.empty((0,), dtype=float)
    intensity = np.empty((0,), dtype=float)
    
    with open(path, 'r') as f:
        # Seek spectrum start flag
        line = f.readline()
        while not (line == SPECTRUM_START_FLAG + WINDOWS_NEW_LINE or line == SPECTRUM_START_FLAG + UNIX_NEW_LINE):
            line = f.readline()
        
        # Read spectrum until end flag
        line = f.readline()
        while not (line == SPECTRUM_END_FLAG + WINDOWS_NEW_LINE or line == SPECTRUM_END_FLAG + UNIX_NEW_LINE):
            split_line = split(split_condition, line)
            w = float(split_line[0].replace(",","."))
            i = float(split_line[1].replace(",","."))
            
            wavelength = np.append(wavelength, w)
            intensity = np.append(intensity, i)
            
            line = f.readline()
    
    return wavelength, intensity

def read_header(path):
    header = []
    
    with open(path, 'r') as f:
        # Seart for header start flag:
        while True:
            line = f.readline()
            if line == HEADER_START_FLAG + WINDOWS_NEW_LINE or line == HEADER_START_FLAG + UNIX_NEW_LINE:
                break
        
        # Read header until end flag
        while True:
            line = f.readline()
            if line == SPECTRUM_START_FLAG + WINDOWS_NEW_LINE or line == SPECTRUM_START_FLAG + UNIX_NEW_LINE:
                break
            else:
                header.append(line.replace(WINDOWS_NEW_LINE,"").replace(UNIX_NEW_LINE,""))
    
    return header

def normalize(intensity, mode='max'):
    if mode == 'max':
        intensity = intensity/np.max(intensity)
    
    return intensity

class Spectrum:
        
    def __init__(self, file_path=None):
        if file_path == None:
            self.path = file_dialog_open(batch=False)[0]
        elif isinstance(file_path, str):
            self.path = validate_files(file_path)
        
        self.header = read_header(self.path)
        self.wavelength, self.intensity = read_spectrum(self.path)
    
    def plot(self, append_to=None, normalization=None):
        if append_to==None:
            figure = plt.figure()
            axes = plt.axes()
        elif isinstance(append_to, type(plt.axes())):
            axes = append_to
            plt.axes(axes)
            figure = plt.gcf()
        
        if normalize != None:
            intensity = normalize(self.intensity, mode=normalization)
        else:
            intensity = self.intensity
        wavelength = self.wavelength
        
        axes.plot(wavelength, intensity,
                  linewidth = 1)
        
        plt.xlabel("Longitud de onda [nm]")
        plt.ylabel("Intensidad")
        plt.grid("on", linestyle = ":")
        
        return figure, axes

if __name__ == '__main__':
    
    from os import listdir
    
    from scipy.signal import find_peaks
    from scipy.optimize import lsq_linear
    from scipy.interpolate import CubicSpline
    
    path = "E:\\Axel (Google Drive)\\Proyecto OCT\\2019-02-05_Calibracion_espectrometro\\2018-02-05_Mediciones_Ocean_Optics"
    files = listdir(path)
    
    xlim = [750, 850]
    prominence = 20
    
    fit = np.zeros((len(files), 2))
    
    for i, name in enumerate(files):
        
        fullpath = path + "\\" + name
        s = Spectrum(fullpath)
        
        filter_indices = np.argwhere(np.logical_and(s.wavelength>xlim[0], s.wavelength<xlim[1]))
        
        x = s.wavelength[filter_indices].flatten()
        y = s.intensity[filter_indices].flatten()
        
        splines = CubicSpline(x, y, bc_type="clamped")
        xi = np.linspace(x[0], x[-1], x.size*10)
        yi = splines(xi)
        
#        plt.scatter(x,y)
#        plt.plot(xi,yi)

        peaks_p, properties_p = find_peaks(yi, prominence=prominence)
        peaks_n, properties_n = find_peaks(-yi, prominence=prominence)
        
        peaks = np.sort(np.append(peaks_p, peaks_n))
        
#        plt.plot(xi, yi)
#        plt.scatter(xi[peaks], yi[peaks])
        
        x_col = np.arange(x.size).reshape((x.size, 1))
        A = np.hstack((x_col, np.ones(x_col.shape)))
        
        lsq_res = lsq_linear(A, x)
        
#        print(lsq_res.x)
        fit[i, :] = lsq_res.x
    
#        plt.scatter(x_col, x)
#        plt.plot(x_col, np.dot(A, lsq_res.x))
        
       
    
#    from scipy.optimize import least_squares
#    
#    def fun(p, x, y):
#        return np.multiply(np.exp(-np.power(x-p[0], 2)/(2*p[1]**2)) , p[2] - p[3] * np.cos(2*np.pi/p[4]*x+p[5])**2) - y
#    
#    def fun1(p, x, y):
#        return p[0] * np.exp(-(x-p[1])**2 / (2*p[2]**2)) - y
#    
#    def fun2(p, fix, x, y):
#        return np.multiply(np.exp(-(x-fix[1])**2 / (2*fix[2]**2)) , fix[0] - p[0] * np.cos(2*np.pi/p[1] * x + p[2])) - y
#    
#    xlim = [750, 850]
#    filter_indices = np.argwhere(np.logical_and(s.wavelength>xlim[0], s.wavelength<xlim[1]))
#    
#    x = s.wavelength[filter_indices].flatten()
#    y = s.intensity[filter_indices].flatten()
#    
#    x1 = [6000, # Gaussian max
#          800, # Gaussian centre
#          18] # Gaussian std
#    
#    res_lsq_1 = least_squares(fun1, x1, args=(x, y), method='lm')
#    
#    plt.figure()
#    plt.plot(x, y)
#    plt.plot(x, fun1(res_lsq_1.x, x, np.zeros(x.shape)))
#        
#    x2 = [3000, # Cosine amplitude
#          1.5, # Wavelength periodicity
#          0] # Phase
#    
#    bounds = ([2000, 1, -np.inf],
#              [4500, 5,  np.inf])
#    
#    res_lsq_2 = least_squares(fun2, x2, bounds=bounds, args=(res_lsq_1.x, x, y), max_nfev=10**6)
#    print(res_lsq_2.message)
#    print("""Gaussian max: {}
#    Gaussian center: {}
#    Gaussian std: {}
#    Cosine amplitude: {}
#    Periodicity: {}
#    Phase: {}""".format(res_lsq_1.x[0], res_lsq_1.x[1], res_lsq_1.x[2], res_lsq_2.x[0], res_lsq_2.x[1], res_lsq_2.x[2]))
#    
#    plt.figure()
#    plt.plot(x, y)
#    plt.plot(x, fun2(res_lsq_2.x, res_lsq_1.x, x, np.zeros(x.shape)))

    
    
    
    
    
    
            
            
            
            