# %% ==========================================================================
# Import and Definitions
# =============================================================================
import datetime
import time
from dataclasses import dataclass
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from tqdm import tqdm


@dataclass
class SourceCfg:
    name: str
    device: Any  # or a Protocol for your instrument API
    auto: bool
    channel: int | str
    set_voltage: float
    current_limit: float

    def apply_startup(self) -> None:
        if self.auto:
            self.device.set_voltage(self.channel, self.set_voltage)
            self.device.set_current_limit(self.channel, self.current_limit)


# Instrument Libraries Github: https://github.com/MartinMiroslavovMihaylov/Python_Instruments_Automation_Scripts
# Install with:
# pip install git+https://github.com/MartinMiroslavovMihaylov/Python_Instruments_Automation_Scripts.git

# from Instruments_Libraries.GPP4323 import GPP4323
# from Instruments_Libraries.KEITHLEY2612 import KEITHLEY2612
from Instruments_Libraries.InstrumentSelect import PowerSupply_GPP4323, SourceMeter

# %% ==========================================================================
# Select Instruments and Load Instrument Libraries
# =============================================================================
# myGPP4323 = GPP4323('COMXX') # noqa: N816
myGPP4323 = PowerSupply_GPP4323()  # noqa: N816
myGPP4323.reset()

# myKEITHLEY2612 = KEITHLEY2612('COMXX') # noqa: N816
myKEITHLEY2612 = SourceMeter()  # noqa: N816
myKEITHLEY2612.reset()

# %% ==========================================================================
# Setup the Measurement
# =============================================================================
num_of_points = 10
sleep_time = 0.5

DC_Sources: dict[str, SourceCfg] = {
    # dataclass name: SourceCfg(name, device, auto, channel, set_voltage, current_limit)
    "VCC": SourceCfg("VCC", myKEITHLEY2612, True, "a", 4.0, 0.310),
    "bias": SourceCfg("bias", myGPP4323, True, 1, 2.9, 0.005),
}

# %% ==========================================================================
# Configure the Instrument
# =============================================================================
# Keithly Sourcemeter needs to be setup as voltage source more specifically
myKEITHLEY2612.set_channel_display()  # Display all channels
myKEITHLEY2612.set_output_source_function("a", "voltage")
myKEITHLEY2612.set_output_source_function("b", "voltage")
myKEITHLEY2612.set_display_measurement_function("a", "amp")  # measure current
myKEITHLEY2612.set_display_measurement_function("b", "amp")  # measure current


for source in DC_Sources.values():
    source.apply_startup()  # apply startup, checks for "auto" internally

# %% ==========================================================================
# Measurement
# =============================================================================
for source in DC_Sources.values():
    if source.auto:  # if the source is set to auto
        source.device.set_output(source.channel, "ON")  # Turn on the channel

records = []  # Empty list to store data and meta data
for idx in tqdm(range(num_of_points)):
    rec = {}  # single record
    for source in DC_Sources.values():
        rec[source.name + "_Voltage"] = source.device.measure_voltage(source.channel)
        rec[source.name + "_Current"] = source.device.measure_current(source.channel)
        rec[source.name + "_Power"] = source.device.measure_power(source.channel)

    rec["Timestamps"] = datetime.datetime.now()
    records.append(rec)
    time.sleep(sleep_time)
    temp = idx * np.pi  # do something with idx

# %% ==========================================================================
# Create Dataframe
# =============================================================================
meas_df = pd.DataFrame.from_records(records)

# %% ==========================================================================
# Plot the Measurement
# =============================================================================
t0 = meas_df["Timestamps"].iloc[0]
relative_time = (meas_df["Timestamps"] - t0).dt.total_seconds()

plt.plot(relative_time, meas_df["VCC_Current"])
plt.xlabel("Time (s)")
plt.ylabel("Current (A)")
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

# or

# Save DataFrame to CSV
meas_df.to_csv("measurements.csv", index=False)

# Load it back, auto-parsing the "Timestamps" column as datetime
loaded_df = pd.read_csv("measurements.csv", parse_dates=["Timestamps"])
print(loaded_df.head())

# %% ==========================================================================
# Close Instrument
# =============================================================================
myGPP4323.Close()
