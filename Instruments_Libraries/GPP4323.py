# -*- coding: utf-8 -*-
"""
Created on Wed Feb  1 15:55:01 2023

@author: Martin.Mihaylov

Install Driver:
    To use the DC-Power Supply GW-Instek GPP4323 you need to install the USB Driver
    from https://www.gwinstek.com/en-global/download/ - GPP USB Driver
    Python Library needed: ``pip install pyserial``
"""

import time
from .BaseInstrument import BaseInstrument

class GPP4323(BaseInstrument):
    """
    Driver for GW-Instek GPP-4323 Power Supply using BaseInstrument (PyVISA).
    """

    def __init__(self, resource_str: str, visa_library: str = '@py', **kwargs):
        """
        Initialize the GW-Instek GPP-4323 Power Supply.

        Parameters
        ----------
        resource_str : str
            The VISA resource string (e.g., 'COMXX').
        **kwargs : dict
            Additional keyword arguments passed to the BaseInstrument constructor.
        """
        # Default serial connection parameters for GPP4323
        # PyVISA-compatible keyword arguments for ASRL resources
        kwargs.setdefault('baud_rate', 115200)
        kwargs.setdefault('data_bits', 8)
        kwargs.setdefault('stop_bits', 1.0) # 1 stop bit
        kwargs.setdefault('parity', 0)      # No parity
        kwargs.setdefault('read_termination', '\n')
        kwargs.setdefault('write_termination', '\n')
        kwargs.setdefault('timeout', 2000) # 2s

        super().__init__(resource_str, visa_library=visa_library, **kwargs)

        # Internal Variables
        self._ChannelLS = [1, 2, 3, 4]
        self._mainChannelLS = [1, 2]
        self._measurement_type_mapping = {
            "voltage": "Voltage",
            "volt": "Voltage",
            "v": "Voltage",
            "current": "Current",
            "amp": "Current",
            "a": "Current",
            "power": "Power",
            "watt": "Power",
            "p": "Power",
        }
        
    # =============================================================================
    # Checks and Validations
    # =============================================================================

    def _validate_channel(self, channel: int, mainChannel: bool = False) -> int:
        channel = int(channel)
        if mainChannel and channel not in self._mainChannelLS:
            raise ValueError("Invalid channel number given! Channel Number can be [1,2].")
        if channel not in self._ChannelLS:
            raise ValueError("Invalid channel number given! Channel Number can be [1,2,3,4].")
        return channel

    def _validate_voltage(self, channel: int, voltage: int | float) -> str:
        if channel in self._mainChannelLS and (voltage < 0 or voltage > 32):
            raise ValueError("Invalid voltage given! Voltage can be [0,32].")
        if channel == 3 and (voltage < 0 or voltage > 5):
            raise ValueError("Invalid voltage given! Voltage on Channel 3 can be [0,5].")
        if channel == 4 and (voltage < 0 or voltage > 15):
            raise ValueError("Invalid voltage given! Voltage on Channel 4 can be [0,15].")
        return f"{voltage:.3f}"

    def _validate_amp(self, channel: int, amp: int | float) -> str:
        if channel in self._mainChannelLS and (amp < 0 or amp > 3):
            raise ValueError("Invalid current given! Current on Channels 1 and 2 can be [0,3].")
        if (channel == 3 or channel == 4) and (amp < 0 or amp > 1):
            raise ValueError("Invalid current given! Current on Channels 3 and 4 can be [0,1].")
        return f"{amp:.4f}"

    def _validate_resistor(self, res: int | float) -> str:
        if res < 1 or res > 1000:
            raise ValueError("Invalid resistance given! Resistance can be [1,1000].")
        return f"{res:.3f}"

    def _validate_measurement_type(self, measurement_type: str) -> str:
        type_normalized = self._measurement_type_mapping.get(
            measurement_type.lower() if isinstance(measurement_type, str) else measurement_type
        )
        if type_normalized is None:
            raise ValueError("Invalid measurement type given! Type can be [voltage,current,power].")
        return type_normalized

    # =============================================================================
    # Set Values and Modes
    # =============================================================================

    def set_voltage(self, channel: int, voltage: int | float) -> None:
        """Set Voltage on the specified channel.


        Parameters
        ----------
        channel : int
            Select channel from List of Channel Numbers [1,2,3,4].
        voltage : int/float.
            Set Voltage on Channel.

        Returns
        -------
        None.

        """
        channel = self._validate_channel(channel)
        voltage_str = self._validate_voltage(channel, voltage)
        self.write(f"VSET{channel}:{voltage_str}")

    def set_current(self, channel: int, amp: int | float) -> None:
        """


        Parameters
        ----------
        channel : int
            Select channel from List of Channel Numbers [1,2,3,4].
        amp : int/float
            Set Current on Channel.

        Returns
        -------
        None.

        """
        channel = self._validate_channel(channel)
        amp_str = self._validate_amp(channel, amp)
        self.write(f"ISET{channel}:{amp_str}")

    def set_channel_tracking_series(self, state: str | int) -> None:
        """Sets CH1/CH2 as Tracking series mode.


        Parameters
        ----------
        state : str
            Possible state ["ON", "OFF"].

        Returns
        -------
        None.

        """
        state_normalized = self._parse_state(state)
        self.write(f":OUTPut:SERies {state_normalized}")

    def set_channel_tracking_parallel(self, state: str | int) -> None:
        """Sets CH1/CH2 as Tracking parallel mode.


        Parameters
        ----------
        state : str
            Possible state ["ON", "OFF"].

        Returns
        -------
        None.

        """
        state_normalized = self._parse_state(state)
        self.write(f":OUTPut:PARallel {state_normalized}")

    def set_channel_tracking(self, mode: int) -> None:
        """Selects the operation mode: independent, tracking series, or tracking parallel.
        GPP-1326 does not have this function. Series-parallel mode is not supported under LOAD.


        Parameters
        ----------
        mode : int
            Select 0 - Independent, 1 - Series or 2 - Parallel

        Returns
        -------
        None.

        """
        if mode not in [0, 1, 2]:
            raise ValueError("Invalid Mode. Select 0 - Independent, 1 - Series, 2 - Parallel")
        self.write(f"TRACK{mode}")

    def set_channel_load_mode(self, channel: int, mode: str, state: str | int) -> None:
        """Sets CH1 or CH2 as Load CV, CC or CR mode.


        Parameters
        ----------
        channel : int
            Select channel from List of Channel Numbers [1,2].
        mode : str
            Select Load CV, CC or CR mode.
        state : str
            Possible state ["ON", "OFF"].

        Returns
        -------
        None.

        """
        modeLS = ["CC", "CV", "CR"]
        channel = self._validate_channel(channel, mainChannel=True)
        state_normalized = self._parse_state(state)
        if mode not in modeLS:
            raise ValueError(f"Invalid Mode. Select from {modeLS}.")
        self.write(f":LOAD{channel}:{mode} {state_normalized}")

    def set_load_resistor(self, channel: int, res: float) -> None:
        """Sets the Load CR level.


        Parameters
        ----------
        channel : int
            Select channel from List of Channel Numbers [1,2].
        res : float
            Set resistance values from range 1-1000.

        Returns
        -------
        None.

        """
        channel = self._validate_channel(channel, mainChannel=True)
        res_str = self._validate_resistor(res)
        self.write(f":LOAD{channel}:RESistor {res_str}")

    def set_output(self, channel: int, state: str | int) -> None:
        """Enable/Disable Output


        Parameters
        ----------
        channel : int
            Select channel from List of Channel Numbers [1,2,3,4].
        state : str
            state of power Supple output. Could be ["ON", "OFF"]

        Returns
        -------
        None.

        """
        channel = self._validate_channel(channel)
        state_normalized = self._parse_state(state)
        self.write(f":OUTPut{channel}:STATe {state_normalized}")

    def set_all_output(self, state: str | int) -> None:
        """Enable/Disable All Outputs


        Parameters
        ----------
        state : str
            state of power Supple output. Could be ["ON", "OFF"]

        Returns
        -------
        None.

        """
        state_normalized = self._parse_state(state)
        if state_normalized == "ON":
            self.write("ALLOUTON")
        else:
            self.write("ALLOUTOFF")

    # =============================================================================
    # Ask Commands
    # =============================================================================

    def get_voltage_setting(self, channel: int) -> float:
        """Returns the voltage setting, NOT the measured voltage!!!


        Parameters
        ----------
        channel : int
            Select channel from List of Channel Numbers [1,2,3,4].

        Returns
        -------
        float
            Voltage Setting.

        """
        channel = self._validate_channel(channel)
        return float(self.query(f"VSET{channel}?"))

    def get_current_setting(self, channel: int) -> float:
        """Returns the current setting, NOT the measured current!!!


        Parameters
        ----------
        channel : int
            Select channel from List of Channel Numbers [1,2,3,4].

        Returns
        -------
        float
            Current Setting.

        """
        channel = self._validate_channel(channel)
        return float(self.query(f"ISET{channel}?"))

    def measure(self, channel: int, measurement_type: str) -> float:
        """Performs a measurement and returns the measured value.


        Parameters
        ----------
        channel : int
            Select channel from List of Channel Numbers [1,2,3,4].
        Type : str
            Select measurement type:
            'volt', 'amp' or 'watt'.

        Returns
        -------
        float
            Return float with the measured value on the channel.

        """
        channel = self._validate_channel(channel)
        type_norm = self._validate_measurement_type(measurement_type)
        return float(self.query(f":MEASure{channel}:{type_norm}?"))

    def measure_current(self, channel: int) -> float:
        """Performs one current measurements and returns the value.


        Parameters
        ----------
        channel : int
            Select channel from List of Channel Numbers [1,2,3,4].

        Returns
        -------
        float
            Measured Current.

        """
        return self.measure(channel, "amp")

    def measure_voltage(self, channel: int) -> float:
        """Performs one voltage measurements and returns the value.


        Parameters
        ----------
        channel : int
            Select channel from List of Channel Numbers [1,2,3,4].

        Returns
        -------
        float
            Measured Voltage.

        """
        return self.measure(channel, "volt")

    def measure_power(self, channel: int) -> float:
        """Performs one power measurements and returns the value.


        Parameters
        ----------
        channel : int
            Select channel from List of Channel Numbers [1,2,3,4].

        Returns
        -------
        float
            Measured Power.

        """
        return self.measure(channel, "watt")

    def get_channel_load_mode(self, channel: int) -> str:
        """Queries CH1 or CH2 work mode.
        6 modes: SERies/PARallel/INDE pendent, CV Load/CC Load/CR Load


        Parameters
        ----------
        channel : int
            Select channel from List of Channel Numbers [1,2].

        Returns
        -------
        str
            SERies/PARallel/INDependent, CV Load/CC Load/CR Load

        """
        channel = self._validate_channel(channel, mainChannel=True)
        return self.query(f":MODE{channel}?")

    def get_load_resistor(self, channel: int) -> float:
        """


        Parameters
        ----------
        channel : int
            Select channel from List of Channel Numbers [1,2].

        Returns
        -------
        float
            Set load Resistance Value for given channel.

        """
        channel = self._validate_channel(channel, mainChannel=True)
        return float(self.query(f":LOAD{channel}:RESistor?"))

    # =============================================================================
    # Get/Save Data
    # =============================================================================

    def get_data(self, channel: int) -> dict:
        """

        Parameters
        ----------
        channel : int
            Select channel from List of Channel Numbers [1,2,3,4].

        Returns
        -------
        OutPut : dict
            Return a dictionary with the measured voltage and current.

        """
        channel = self._validate_channel(channel)
        result = {}
        result["Voltage/V"] = self.measure_voltage(channel)
        result["Current/A"] = self.measure_current(channel)
        result["Power/W"] = self.measure_power(channel)
        return result

    # =============================================================================
    # Aliases for backwards compatibility
    # =============================================================================
    
    set_Volt = set_voltage
    set_Voltage = set_voltage
    set_Amp = set_current
    set_Current = set_current
    set_CurrentLimit = set_current
    set_ChannelToSerial = set_channel_tracking_series
    set_ChannelToParallel = set_channel_tracking_parallel
    set_ChannelTracking = set_channel_tracking
    set_ChannelLoadMode = set_channel_load_mode
    set_LoadResistor = set_load_resistor
    set_Out = set_output
    set_AllOut = set_all_output
    ask_VoltageSetting = get_voltage_setting
    ask_CurrentSetting = get_current_setting
    read_Measurement = measure
    ask_Current = measure_current
    ask_Voltage = measure_voltage
    ask_Power = measure_power
    ask_ChannelLoadMode = get_channel_load_mode
    ask_LoadResistor = get_load_resistor
