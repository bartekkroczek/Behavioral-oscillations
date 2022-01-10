#!/usr/bin/env python

__author__ = "Bartłomiej Kroczek"
__contact__ = "bartek.kroczek@doctoral.uj.edu.pl"
__copyright__ = "Copyright 2009, Planet Earth"

import os
import random
import mne
import numpy as np
from scipy import signal
import pandas as pd
from tqdm import tqdm
from os.path import join
import matplotlib.pyplot as plt
from mne.filter import construct_iir_filter, create_filter
from mne.viz import plot_filter, plot_ideal_filter
from scipy.signal import argrelextrema
from collections import Counter
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
from scipy.ndimage import gaussian_filter1d


def estimate_ringing(par, plot=False):
    """
        Estimate filter ringing time and check if estimation can be somehow
        skewed by error or warning.
    :param par:
    :param plot:
    """
    error = "No error"
    margin = par["margin"]
    try:
        iir_params = dict(ftype="butter",
                          gpass=par["gpass"],
                          gstop=par["gstop"],
                          output=par["output"])
        iir_params = construct_iir_filter(
            iir_params,
            f_pass=[F_s, F_p],
            f_stop=[F_s - margin, F_p + margin],
            sfreq=SFREQ,
            btype="bandpass",
            verbose=False,
        )
        filt = create_filter(SAMPLE_EPOCH,
                             SFREQ,
                             l_freq=F_s,
                             h_freq=F_p,
                             method="iir",
                             iir_params=iir_param,
                             verbose=False)
        ringing = 2 * filt["padlen"] / SFREQ
        if ringing == 0:
            ringing = 1000
            error = "Ringing estimation error"
    except Exception as e:
        ringing = 1000
        error = e
    if plot:  # plot both filter and efect of filtering on sample signal
        fig = plot_filter(filt,
                          SFREQ,
                          FREQ,
                          GAIN,
                          flim=FLIM,
                          compensate=True,
                          plot=("time", "magnitude"))
    return ringing, error


main_dir = join(os.path.expanduser("~"), "Projects", "Behavioral-oscillations",
                "data")
low_data_dir = join(main_dir, "low_resolution")
high_data_dir = join(main_dir, "high_resolution")

# import data
low_part = random.choice(os.listdir(low_data_dir))
high_part = random.choice(os.listdir(high_data_dir))

low_data = pd.read_csv(join(low_data_dir, low_part))
high_data = pd.read_csv(join(high_data_dir, high_part))

low_data = low_data.groupby('CSI').mean().Corr.to_list()
high_data = high_data.groupby('CSI').mean().Corr.to_list()

low_freq = 60.
high_freq = 120.

# set params

order = 2
ftype = 'butter'
iir_params = dict(order=order, ftype=ftype, output='sos')
iir_params = construct_iir_filter(iir_params,
                                  f_pass=3.9,
                                  f_stop=None,
                                  sfreq=high_freq,
                                  btype='highpass',
                                  return_copy=False)
ringing = 2 * iir_params['padlen']
mne.viz.plot_filter(iir_params,
                    high_freq,
                    title=f"Butterworth order={order} Ringing={ringing}",
                    flim=[0.01, 10],
                    compensate=False)

# plot filter

sfreq = low_freq
f_p = .1
flim = (.01, sfreq / 2.)  # limits for plotting
nyq = sfreq / 2.  # the Nyquist frequency is half our sample rate
freq = [0, f_p, f_p, nyq]
gain = [0, 0, 1, 1]

sos = signal.iirfilter(2,
                       f_p / nyq,
                       btype='highpass',
                       ftype='butter',
                       output='sos')
plot_filter(dict(sos=sos),
            sfreq,
            freq,
            gain,
            'Butterworth order=2',
            flim=flim,
            compensate=False)

iir_params = dict(order=1, ftype='cheby2', rs=25)
filt = mne.filter.create_filter(high_data,
                                high_freq,
                                l_freq=0.1,
                                h_freq=None,
                                method='iir',
                                iir_params=iir_params,
                                verbose=True)
plot_filter(filt,
            high_freq,
            freq,
            gain,
            'Butterworth order=2',
            flim=flim,
            compensate=True)
x_steep = signal.sosfiltfilt(filt['sos'], high_data)
