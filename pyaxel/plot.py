# -*- coding: utf-8 -*-
"""
Created on Thu Apr  4 15:45:42 2019

@author: Axel Lacapmesure
"""

from matplotlib import pyplot as plt

# Defaults
COLOR = "#000000FF"
MARKER = "o"
MARKERSIZE = 3
LINEWIDTH = 0.5

def figure(figsize=(4,3), dpi=150, *args, **kwargs):

    plt.rc('text', usetex=True)
    plt.rc('font', family='serif')
    plt.rc('figure', autolayout=True)
    
    plt.figure(figsize=(4, 3), dpi=150, *args, **kwargs)

def errorbar(x, y, xerr, yerr, label=None, color=COLOR, marker=MARKER, markersize=MARKERSIZE, capsize=1, capthick=LINEWIDTH, *args, **kwargs):
    plt.errorbar(x, y,
                 xerr=xerr, yerr=yerr,
                 capsize=capsize,
                 capthick=capthick,
                 linestyle="",
                 linewidth=capthick,
                 color=color,
                 marker=marker,
                 markersize=markersize,
                 markerfacecolor=color,
                 markeredgecolor="#00000000",
                 label=label,
                 *args, **kwargs)
    
    plt.tight_layout(pad=2)
    plt.grid(linestyle=":")
    
def scatter(x, y, label=None, color=COLOR, marker=MARKER, markersize=MARKERSIZE, *args, **kwargs):
    plt.scatter(x, y,
                linestyle="",
                color=color,
                marker=marker,
                markersize=markersize,
                markerfacecolor=color,
                markeredgecolor="#00000000",
                label=label,
                *args, **kwargs)
    
    plt.tight_layout(pad=2)
    plt.grid(linestyle=":")

def plot(x, y, label=None, color=COLOR, linewidth=LINEWIDTH, marker=MARKER, markersize=MARKERSIZE, *args, **kwargs):
    plt.plot(x, y,
             color=color,
             linewidth=linewidth,
             label="Ajuste polinomial")
    
    plt.tight_layout(pad=2)
    plt.grid(linestyle=":")