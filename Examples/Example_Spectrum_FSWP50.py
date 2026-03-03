# %% ==========================================================================
# Import and Definitions
# =============================================================================
import datetime
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from tqdm import tqdm

# Instrument Libraries Github: https://github.com/MartinMiroslavovMihaylov/Python_Instruments_Automation_Scripts
# Install with:
# pip install git+https://github.com/MartinMiroslavovMihaylov/Python_Instruments_Automation_Scripts.git
from Instruments_Libraries.FSWP50 import FSWP50  # SpectrumAnalyzer

# from Instruments_Libraries.InstrumentSelect import FSWP50

# %% ==========================================================================
# Select Instruments and Load Instrument Libraries
# =============================================================================
mySpecAnalyser = FSWP50("169.254.253.126") # using class directly  # noqa: N816
# mySpecAnalyser = FSWP50() # using InstrumentSelect # noqa: N816
mySpecAnalyser.reset()

# %% ==========================================================================
# Setup the Measurement
# =============================================================================
num_of_points = 10
sleep_time = 1 # in seconds
freq = np.linspace(1e9, 40e9, num_of_points)

# Initial Spectrum Analyzer Sweep Settings
SA_RMS_TraceNum = 1 
SA_POS_TraceNum = 2 
SA_f_min = 0
SA_f_max = 40e9
SA_resBW = 100e3
SA_ref_level = -10  # dBm
datapoints = 4001

# %% ==========================================================================
# Configure the Instrument
# =============================================================================
mySpecAnalyser.create_channel('SANALYZER', 'Spectrum') # Create Spectrum Channel
mySpecAnalyser.delete_channel('Phase Noise') # Delete Phase Noise Channel
mySpecAnalyser.set_continuous('ON') # Set Continuous Mode
mySpecAnalyser.set_start_frequency(SA_f_min)
mySpecAnalyser.set_stop_frequency(SA_f_max)
mySpecAnalyser.set_resolution_bandwidth(SA_resBW)
mySpecAnalyser.set_reference_level(SA_ref_level)
mySpecAnalyser.set_sweep_points(datapoints) # Set Number of Data Points
mySpecAnalyser.set_input_attenuation_auto("OFF") # Disable Auto Input Attenuation
mySpecAnalyser.set_input_attenuation(0) # Set Input Attenuation
# Trace 1: RMS
mySpecAnalyser.set_detection_function("RMS", trace_number=SA_RMS_TraceNum)
# Trace 2: Positive
mySpecAnalyser.set_detection_function("POSITIVE", trace_number=SA_POS_TraceNum)
mySpecAnalyser.set_trace_mode("WRITE", trace_number=SA_POS_TraceNum) # turn it on


# %% ==========================================================================
# Measurement
# =============================================================================

records = [] # Empty list to store data and meta data
for idx in tqdm(range(num_of_points)):
    rec = {} # single record

    # Do some changes, like change input frequency
    # SignalGenerator.set_freq_CW(freq[idx])
    temp = idx*np.pi # do something with idx

    # Write Meta Data
    rec["SA f_min"] = SA_f_min
    rec["SA f_max"] = SA_f_max
    rec["SA ref level"] = SA_ref_level
    rec["SA Resolution BW"] = SA_resBW

    # Take the Measurement
    time.sleep(sleep_time)
    rec["data_rms"] = mySpecAnalyser.measure_and_get_trace(
        trace_number=SA_RMS_TraceNum, window_number=1)
    rec["data_pos"] = mySpecAnalyser.measure_and_get_trace(
        trace_number=SA_POS_TraceNum, window_number=1)

    # append the record
    rec["Timestamps"] = datetime.datetime.now()
    records.append(rec)
    

# %% ==========================================================================
# Create Dataframe
# =============================================================================
meas_df = pd.DataFrame.from_records(records)

# %% ==========================================================================
# Plot the Measurement
# =============================================================================
freq_hz = np.linspace(SA_f_min, SA_f_max, datapoints)
power_pos_dBm = np.vstack(meas_df["data_pos"])  # noqa: N816
power_rms_dBm = np.vstack(meas_df["data_rms"])  # noqa: N816

fig, ax = plt.subplots(figsize=(5, 4), layout='constrained')
ax.plot(freq_hz/1e9, power_pos_dBm[0], label="Positive")
ax.plot(freq_hz/1e9, power_rms_dBm[0], label="RMS")
# Formatting
ax.set_xlabel('Frequency (GHz)', fontsize=14, fontweight='bold')
ax.set_ylabel('Power (dBm)', fontsize=14, fontweight='bold')
ax.grid(True, which='both', linestyle='--')
ax.legend(fontsize=14)
ax.tick_params(axis='both', labelsize=12)
for tick in ax.get_xticklabels() + ax.get_yticklabels():
    tick.set_fontweight("bold")
plt.show()
# %% ==========================================================================
# Save Dataframe
# =============================================================================
# Save DataFrame to HDF5 (better than CSV)
meas_df.to_hdf("measurements.h5", key="data", mode="w")
# key="data" is like a "dataset name" inside the HDF5 file 
# (you can store multiple DataFrames in one file with different keys).
# mode="w" overwrites the file. Use mode="a" if you want to append new datasets.

# Later: Load it back
loaded_df = pd.read_hdf("measurements.h5", key="data")
print(loaded_df.head())

#or

# Save DataFrame to CSV
meas_df.to_csv("measurements.csv", index=False)

# Load it back, auto-parsing the "Timestamps" column as datetime
loaded_df = pd.read_csv("measurements.csv", parse_dates=["Timestamps"])
print(loaded_df.head())

# %% ==========================================================================
# Close Instrument
# =============================================================================
mySpecAnalyser.Close()
