#!/usr/bin/env python

__author__ = "Bartłomiej Kroczek"
__contact__ = "bartek.kroczek@doctoral.uj.edu.pl"
__copyright__ = "Copyright 2009, Planet Earth"

import os
import random
import numpy as np
from scipy import signal
import pandas as pd
from os.path import join
import matplotlib.pyplot as plt
from mne.viz import plot_filter


# Badanie charakterystyki amplitudowej filtru "roll-mean"

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

moving_avg = lambda x, k:np.convolve(x, np.ones(k)/k, mode = "same")

sfreq = 50
cutoff = 2.0
flim = (.01, sfreq / 2.)  # limits for plotting
nyq = sfreq / 2.  # the Nyquist frequency is half our sample rate
freq = [0, cutoff,  2 * cutoff, nyq]
gain = [0, 0, 1, 1]

song_order = 11
real_order = 45
song_filter = signal.firwin2(song_order, freq, gain, fs = sfreq)
real_filter = signal.firwin2(real_order, freq, gain, fs = sfreq)

plot_filter(song_filter, sfreq, freq, gain, title = "FIR from Song",
            flim=flim, compensate=True)
plot_filter(real_filter, sfreq, freq, gain, title = "Real FIR",
            flim=flim, compensate=True)
plot_filter(np.ones(song_order)/song_order, sfreq, freq, gain,
            title = f"Moving avg. Ord:{song_order}", flim=flim, compensate=True)
plot_filter(np.ones(real_order)/real_order, sfreq, freq, gain,
            title = f"Moving avg. Ord:{real_order}", flim=flim, compensate=True)

fig, ax = plt.subplots()
ax.plot(low_data, label = "Raw")
ax.plot(moving_avg(low_data, song_order), label = f"Moving avg. Ord:{song_order}")
ax.plot(moving_avg(low_data, real_order), label = f"Moving avg. Ord:{real_order}")
ax.plot(np.convolve(low_data, song_filter, mode = "same"),
        label = f"Song Fir len:{len(song_filter)}")
ax.plot(np.convolve(low_data, real_filter, mode = "same"),
        label = f"Real Fir len:{len(real_filter)}")
ax.legend()
fig.show()




























