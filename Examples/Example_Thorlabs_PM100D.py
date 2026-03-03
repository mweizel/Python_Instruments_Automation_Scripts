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
# from Instruments_Libraries.PM100D import PM100D
from Instruments_Libraries.InstrumentSelect import PowerMeter

# %% ==========================================================================
# Select Instruments and Load Instrument Libraries
# =============================================================================
# myPowermeter = PM100D('Seriennummer') # replace with your serial number   # noqa: N816
myPowermeter = PowerMeter()  # noqa: N816

# %% ==========================================================================
# Setup the Measurement
# =============================================================================
num_of_points = 10
sleep_time = 0.5
wavelength = 1550 # nm

# %% ==========================================================================
# Configure the Instrument
# =============================================================================
myPowermeter.config_power()
myPowermeter.set_auto_power_range('ON')
myPowermeter.set_power_units('dBm')
myPowermeter.set_wavelength(wavelength) # nm

# %% ==========================================================================
# Measurement
# =============================================================================
records = [] # Empty list to store data and meta data
for idx in tqdm(range(num_of_points)):
    rec = {} # single record
    rec["Power_dBm"] = myPowermeter.get_power()
    rec["WaveLength"] = myPowermeter.get_wavelength()
    rec["Timestamps"] = datetime.datetime.now()
    records.append(rec)
    time.sleep(sleep_time)
    temp = idx*np.pi # do something with idx

# %% ==========================================================================
# Create Dataframe
# =============================================================================
meas_df = pd.DataFrame.from_records(records)

# %% ==========================================================================
# Plot the Measurement
# =============================================================================
t0 = meas_df["Timestamps"].iloc[0]
relative_time = (meas_df["Timestamps"] - t0).dt.total_seconds()

plt.plot(relative_time, meas_df["Power_dBm"])
plt.xlabel('Time (s)')
plt.ylabel('Power (dBm)')
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
myPowermeter.Close()
