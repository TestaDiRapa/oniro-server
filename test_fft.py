from numpy.fft import fft, fftfreq
from scipy.signal import periodogram
import math
import matplotlib.pyplot as plt
import numpy as np
import pyedflib

with pyedflib.EdfReader("sdb4.edf") as in_file:
    channel = in_file.getSignalLabels().index("SpO2")
    values = in_file.readSignal(channel)
    sampling = in_file.getSampleFrequency(channel)
    
agg_values = []
grouping = 5
agg_window = grouping*sampling
i = 0
while i < len(values):
    mean = 0
    j = 0
    while j < len(values) and j < agg_window:
        mean += values[j]
        j += 1
    mean /= j
    agg_values.append(mean)
    i += j

ham_values = []
for i in range(len(agg_values)):
    val = 0.54 - 0.46*math.cos(2*math.pi*i/len(agg_values))
    ham_values.append(val*agg_values[i])

f, ps = periodogram(ham_values, 1/grouping)
plt.semilogy(f, ps)
plt.xlabel('frequency [Hz]')
plt.ylabel('PSD [V**2/Hz]')
plt.show()