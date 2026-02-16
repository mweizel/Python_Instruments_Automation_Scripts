
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 10 08:39:48 2021

@author: Martin.Mihaylov
@author: Maxim Weizel
"""

import re
from typing import List, Dict, Any, Tuple
from .BaseInstrument import BaseInstrument

class KEITHLEY2612(BaseInstrument):
    """
    Driver for Keithley 2612 SourceMeter using BaseInstrument.
    """

    def __init__(self, resource_str: str, **kwargs):
        """
        Initialize the Keithley 2612 SourceMeter.

        Parameters
        ----------
        resource_str : str
            The VISA resource string (e.g., 'COMXX').
        **kwargs : dict
            Additional keyword arguments passed to the BaseInstrument constructor.
        """
        super().__init__(resource_str, **kwargs)

        idn = self.get_idn()
        if "2612" not in idn:
            self.logger.warning(f"Device at {resource_str} may not be a Keithley 2612. IDN: {idn}")
        else:
            self.logger.info(f"Connected to: {idn}")

        self._resource.read_termination = "\n"

        # Internal Variables
        self._ChannelLS = ["a", "b"]
        self._Measurement_Types = {
            "voltage": "v", "volt": "v", "v": "v",
            "current": "i", "amp": "i", "i": "i",
            "power": "p", "watt": "p", "p": "p",
            "resistance": "r", "ohm": "r", "r": "r",
        }
        self.dict_of_lua_scripts = {}

        # Voltage and current limits for safety
        self._absolute_Voltage_Limits = {"min": 0, "max": 200}
        self._Voltage_Limits = {"min": 0, "max": 10.0}
        self._Current_Limits = {"min": 0, "max": 3.0}

    # =============================================================================
    # Checks and Validations
    # =============================================================================

    def _validate_channel(self, channel: str) -> str:
        """
        Validate and normalize channel input.

        Parameters
        ----------
        channel : str
            Channel identifier ('a' or 'b').

        Returns
        -------
        str
            Normalized channel string ('a' or 'b').

        Raises
        ------
        ValueError
            If the channel is invalid.
        """
        channel = channel.lower().strip()
        if channel not in self._ChannelLS:
            raise ValueError(f"Invalid channel '{channel}'. Must be one of: {self._ChannelLS}")
        return channel

    def _validate_state(self, state: int | str | bool, output: bool = False) -> str:
        """
        Validate and normalize state input.

        Parameters
        ----------
        state : int | str | bool
            State to validate (e.g., 'ON', 'OFF', 1, 0, True, False).
        output : bool, optional
            If True, allows 'HIGH_Z' state. Default is False.

        Returns
        -------
        str
            Normalized state string (e.g., 'ON', 'OFF', 'HIGH_Z').

        Raises
        ------
        ValueError
            If the state is invalid.
        """
        if output:
            state_mapping = {
                "on": "ON", "off": "OFF", "high_z": "HIGH_Z",
                1: "ON", 0: "OFF", 2: "HIGH_Z",
                "1": "ON", "0": "OFF", "2": "HIGH_Z",
                True: "ON", False: "OFF",
            }
        else:
            state_mapping = {
                "on": "ON", "off": "OFF",
                1: "ON", 0: "OFF",
                "1": "ON", "0": "OFF",
                True: "ON", False: "OFF",
            }

        normalized = state_mapping.get(
            state if isinstance(state, (int, bool)) else str(state).lower()
        )
        if normalized is None:
            raise ValueError(f"Invalid state '{state}'. Valid options: on/off/high_z or 1/0/2")
        return normalized

    def _format_scientific(self, value: int | float, precision: int = 4) -> str:
        """
        Format number in scientific notation consistently.

        Parameters
        ----------
        value : int | float
            The value to format.
        precision : int, optional
            Number of decimal places. Default is 4.

        Returns
        -------
        str
            Formatted string.
        """
        return f"{float(value):.{precision}e}"

    # =============================================================================
    # Reset and Clear
    # =============================================================================

    def reset_channel(self, channel: str) -> None:
        """Reset channel to default settings.

        Parameters
        ----------
        channel : str
            Select channel A or B

        """
        channel = self._validate_channel(channel)
        self.write(f"smu{channel}.reset()")

    def clear_error_queue(self) -> None:
        """Clear the instrument's error queue."""
        self.write("errorqueue.clear()")

    # =============================================================================
    # Measurement/GET Methods
    # =============================================================================

    def get_current(self, channel: str) -> float:
        """
        Measure current on the specified channel.

        Parameters
        ----------
        channel : str
            Channel identifier ('a' or 'b').
            
        """
        channel = self._validate_channel(channel)
        return float(self.query(f"print(smu{channel}.measure.i())"))

    def get_voltage(self, channel: str) -> float:
        """
        Measure voltage on the specified channel.

        Parameters
        ----------
        channel : str
            Channel identifier ('a' or 'b').

        """
        channel = self._validate_channel(channel)
        return float(self.query(f"print(smu{channel}.measure.v())"))

    def get_power(self, channel: str) -> float:
        """
        Measure power on the specified channel.

        Parameters
        ----------
        channel : str
            Channel identifier ('a' or 'b').

        """
        channel = self._validate_channel(channel)
        return float(self.query(f"print(smu{channel}.measure.p())"))

    def get_resistance(self, channel: str) -> float:
        """
        Measure resistance on the specified channel.

        Parameters
        ----------
        channel : str
            Channel identifier ('a' or 'b').

        """
        channel = self._validate_channel(channel)
        return float(self.query(f"print(smu{channel}.measure.r())"))

    def read_measurement(self, channel: str, type_: str) -> float:
        """
        Perform a measurement of the specified type.

        Parameters
        ----------
        channel : str
            Channel identifier ('a' or 'b').
        type_ : str
            Type of measurement (e.g., 'voltage', 'current', 'power', 'resistance').

        Returns
        -------
        float
            Measured value.

        Raises
        ------
        ValueError
            If the measurement type is unknown.
        """
        channel = self._validate_channel(channel)
        meas_type = self._Measurement_Types.get(type_.lower())
        if meas_type is None:
            raise ValueError("Unknown input! See function description for more info.")
        return float(self.query(f"print(smu{channel}.measure.{meas_type}())"))

    def get_voltage_range_measure(self, channel: str) -> float:
        """
        Get measurement voltage range.

        If the source function is the same as the measurement function (for example, sourcing voltage and measuring
        voltage), the measurement range is locked to be the same as the source range. However, the setting for the
        measure range is retained. If the source function is changed (for example, from sourcing voltage to sourcing
        current), the retained measurement range will be used.

        Parameters
        ----------
        channel : str
            Channel identifier ('a' or 'b').

        """
        channel = self._validate_channel(channel)
        return float(self.query(f"print(smu{channel}.measure.rangev)"))

    def get_current_range_measure(self, channel: str) -> float:
        """This attribute contains the smuX.measure.rangeY current setting. Look up the datasheet!

        If the source function is the same as the measurement function (for example, sourcing voltage and measuring
        voltage), the measurement range is locked to be the same as the source range. However, the setting for the
        measure range is retained. If the source function is changed (for example, from sourcing voltage to sourcing
        current), the retained measurement range will be used.

        Parameters
        ----------
        channel : str
            Channel identifier ('a' or 'b').

        """
        channel = self._validate_channel(channel)
        return float(self.query(f"print(smu{channel}.measure.rangei)"))

    def get_auto_voltage_range_measure(self, channel: str) -> int:
        """
        Get measurement auto voltage range status.
        You might want to keep it on auto i.e. 1 or "ON"!

        Parameters
        ----------
        channel : str
            Channel identifier ('a' or 'b').

        Returns
        -------
        int
            1 if enabled, 0 if disabled.
        """
        channel = self._validate_channel(channel)
        return int(float(self.query(f"print(smu{channel}.measure.autorangev)")))

    def get_auto_current_range_measure(self, channel: str) -> int:
        """
        Get measurement auto current range status.
        You might want to keep it on auto i.e. 1 or "ON"!

        Parameters
        ----------
        channel : str
            Channel identifier ('a' or 'b').

        Returns
        -------
        int
            1 if enabled, 0 if disabled.
        """
        channel = self._validate_channel(channel)
        return int(float(self.query(f"print(smu{channel}.measure.autorangei)")))

    # =============================================================================
    # Source/GET Methods
    # =============================================================================

    def get_limit_reached(self, channel: str) -> bool:
        """
        Check if source compliance limit has been reached.

        Parameters
        ----------
        channel : str
            Channel identifier ('a' or 'b').

        Returns
        -------
        bool
            True if limit reached, False otherwise.
        """
        channel = self._validate_channel(channel)
        response = self.query(f"print(smu{channel}.source.compliance)").lower()
        return response == "true"

    def get_auto_voltage_range(self, channel: str) -> int:
        """
        Get source auto voltage range status.
        You might want to keep it on auto i.e. 1 or "ON"!

        Parameters
        ----------
        channel : str
            Channel identifier ('a' or 'b').

        Returns
        -------
        int
            1 if enabled, 0 if disabled.
        """
        channel = self._validate_channel(channel)
        return int(float(self.query(f"print(smu{channel}.source.autorangev)")))

    def get_auto_current_range(self, channel: str) -> int:
        """
        Get source auto current range status.
        You might want to keep it on auto i.e. 1 or "ON"!

        Parameters
        ----------
        channel : str
            Channel identifier ('a' or 'b').

        Returns
        -------
        int
            1 if enabled, 0 if disabled.
        """
        channel = self._validate_channel(channel)
        return int(float(self.query(f"print(smu{channel}.source.autorangei)")))

    def get_voltage_range(self, channel: str) -> float:
        """
        Get source voltage range.

        Parameters
        ----------
        channel : str
            Channel identifier ('a' or 'b').

        """
        channel = self._validate_channel(channel)
        return float(self.query(f"print(smu{channel}.source.rangev)"))

    def get_current_range(self, channel: str) -> float:
        """
        Get source current range.

        Parameters
        ----------
        channel : str
            Channel identifier ('a' or 'b').

        """
        channel = self._validate_channel(channel)
        return float(self.query(f"print(smu{channel}.source.rangei)"))

    def get_voltage_limit(self, channel: str) -> float:
        """
        Get source voltage limit.

        Parameters
        ----------
        channel : str
            Channel identifier ('a' or 'b').

        """
        channel = self._validate_channel(channel)
        return float(self.query(f"print(smu{channel}.source.levelv)"))

    def get_current_limit(self, channel: str) -> float:
        """
        Get source current limit.

        Parameters
        ----------
        channel : str
            Channel identifier ('a' or 'b').

        """
        channel = self._validate_channel(channel)
        return float(self.query(f"print(smu{channel}.source.leveli)"))

    def get_voltage_setting(self, channel: str) -> float:
        """
        Get source voltage setting.

        Parameters
        ----------
        channel : str
            Channel identifier ('a' or 'b').

        """
        channel = self._validate_channel(channel)
        return float(self.query(f"print(smu{channel}.source.levelv)"))

    def get_current_setting(self, channel: str) -> float:
        """
        Get source current setting.

        Parameters
        ----------
        channel : str
            Channel identifier ('a' or 'b').

        """
        channel = self._validate_channel(channel)
        return float(self.query(f"print(smu{channel}.source.leveli)"))

    def get_output_source_function(self, channel: str) -> int:
        """
        Get source output function.

        Parameters
        ----------
        channel : str
            Channel identifier ('a' or 'b').

        Returns
        -------
        int
            1 if voltage, 0 if current.
        """
        channel = self._validate_channel(channel)
        return int(float(self.query(f"print(smu{channel}.source.func)")))

    # =============================================================================
    # Further GET Methods
    # =============================================================================
    
    def get_read_buffer(self, channel: str, start: int, stop: int) -> None:
        """
        TODO: This function should be checked. Also is doesn't return anything at the moment.
        """
        channel = self._validate_channel(channel)
        self.query(f"printbuffer({str(start)},{str(stop)},smu{str(channel)})")

    # =============================================================================
    # Source/SET Methods
    # =============================================================================

    def set_source_output(self, channel: str, state: int | str | bool) -> None:
        """
        Set source output state (on or off).

        Parameters
        ----------
        channel : str
            Channel identifier ('a' or 'b').
        state : int | str | bool
            Output state (e.g., 'ON', 'OFF', 1, 0, True, False).
        """
        channel = self._validate_channel(channel)
        state_normalized = self._validate_state(state, output=True)
        self.write(f"smu{channel}.source.output = smu{channel}.OUTPUT_{state_normalized}")

    def set_out(self, channel: str, state: int | str | bool) -> None:
        """Alias for set_source_output()."""
        self.set_source_output(channel, state)
        
    def set_meas_output(self, channel: str, state: int | str | bool) -> None:
        """Alias for set_source_output()."""
        self.set_source_output(channel, state)

    def set_auto_voltage_range(self, channel: str, state: int | str | bool) -> None:
        """
        Set source autorange voltage control.

        Parameters
        ----------
        channel : str
            Channel identifier ('a' or 'b').
        state : int | str | bool
            Status (e.g., 'ON' or 'OFF').
        """
        channel = self._validate_channel(channel)
        state_normalized = self._validate_state(state)
        self.write(f"smu{channel}.source.autorangev = smu{channel}.AUTORANGE_{state_normalized}")

    def set_auto_current_range(self, channel: str, state: int | str | bool) -> None:
        """
        Set source autorange current control.

        Parameters
        ----------
        channel : str
            Channel identifier ('a' or 'b').
        state : int | str | bool
            Status (e.g., 'ON' or 'OFF').
        """
        channel = self._validate_channel(channel)
        state_normalized = self._validate_state(state)
        self.write(f"smu{channel}.source.autorangei = smu{channel}.AUTORANGE_{state_normalized}")

    def set_voltage_range(self, channel: str, value: int | float) -> None:
        """
        Set source voltage range.

        Parameters
        ----------
        channel : str
            Channel identifier ('a' or 'b').
        value : int | float
            Voltage range in Volts.
        """
        channel = self._validate_channel(channel)
        value_formatted = self._format_scientific(value=value, precision=0)
        self.write(f"smu{channel}.source.rangev = {value_formatted}")

    def set_current_range(self, channel: str, value: int | float) -> None:
        """
        Set source current range.

        Parameters
        ----------
        channel : str
            Channel identifier ('a' or 'b').
        value : int | float
            Current range in Amperes.
        """
        channel = self._validate_channel(channel)
        value_formatted = self._format_scientific(value=value, precision=0)
        self.write(f"smu{channel}.source.rangei = {value_formatted}")

    def set_voltage_limit(self, channel: str, limit: int | float, high_voltage: bool = False) -> None:
        """
        Set voltage source compliance.

        Parameters
        ----------
        channel : str
            Channel identifier ('a' or 'b').
        limit : int | float
            Voltage limit in Volts.
        high_voltage : bool, optional
            Enable high voltage range (>10V). Default is False.

        Raises
        ------
        ValueError
            If limit is out of range.
        """
        channel = self._validate_channel(channel)
        if high_voltage:
            if not (self._absolute_Voltage_Limits["min"] <= limit <= self._absolute_Voltage_Limits["max"]):
                raise ValueError(
                    f"Voltage limit must be between {self._absolute_Voltage_Limits['min']} and {self._absolute_Voltage_Limits['max']} V"
                )
        else:
            if not (self._Voltage_Limits["min"] <= limit <= self._Voltage_Limits["max"]):
                raise ValueError(
                    f"Voltage limit must be between {self._Voltage_Limits['min']} and {self._Voltage_Limits['max']} V. "
                    "If you want more than 10V, use high_voltage = True."
                )

        limit_str = self._format_scientific(value=limit, precision=4)
        self.write(f"smu{channel}.source.limitv = {limit_str}")

    def set_current_limit(self, channel: str, limit: int | float) -> None:
        """Sets current source compliance. Use to limit the current output
        when in the voltage source mode. This attribute should be set in the
        test sequence before turning the source on.

        Parameters
        ----------
        channel : str
            Channel identifier ('a' or 'b').
        limit : int | float
            Current limit in Amperes.

        Raises
        ------
        ValueError
            If limit is out of range.
        """
        channel = self._validate_channel(channel)
        if not (self._Current_Limits["min"] < limit < self._Current_Limits["max"]):
            raise ValueError(
                f"Current limit must be between {self._Current_Limits['min']} and {self._Current_Limits['max']} A"
            )

        limit_str = self._format_scientific(value=limit, precision=4)
        self.write(f"smu{channel}.source.limiti = {limit_str}")

    def set_voltage(self, channel: str, voltage: int | float, high_voltage: bool = False) -> None:
        """
        Set source voltage level.

        Parameters
        ----------
        channel : str
            Channel identifier ('a' or 'b').
        voltage : int | float
            Voltage to set in Volts.
        high_voltage : bool, optional
            Enable high voltage range (>10V). Default is False.

        Raises
        ------
        ValueError
            If voltage is out of range.
        """
        channel = self._validate_channel(channel)
        if high_voltage:
            if not (self._absolute_Voltage_Limits["min"] <= voltage <= self._absolute_Voltage_Limits["max"]):
                raise ValueError(
                    f"Voltage must be between {self._absolute_Voltage_Limits['min']} and {self._absolute_Voltage_Limits['max']} V"
                )
        else:
            if not (self._Voltage_Limits["min"] <= voltage <= self._Voltage_Limits["max"]):
                raise ValueError(
                    f"Voltage must be between {self._Voltage_Limits['min']} and {self._Voltage_Limits['max']} V. "
                    "If you want more than 10V, use high_voltage = True."
                )

        voltage_str = self._format_scientific(value=voltage, precision=4)
        self.write(f"smu{channel}.source.levelv = {voltage_str}")

    def set_current(self, channel: str, current: int | float) -> None:
        """
        Set source current level.

        Parameters
        ----------
        channel : str
            Channel identifier ('a' or 'b').
        current : int | float
            Current to set in Amperes.

        Raises
        ------
        ValueError
            If current is out of range.
        """
        channel = self._validate_channel(channel)
        if not (self._Current_Limits["min"] < current < self._Current_Limits["max"]):
            raise ValueError(
                f"Current must be between {self._Current_Limits['min']} and {self._Current_Limits['max']} A"
            )
        current_str = self._format_scientific(value=current, precision=4)
        self.write(f"smu{channel}.source.leveli = {current_str}")

    def set_output_source_function(self, channel: str, function: str) -> None:
        """
        Set source function (V or I).

        Parameters
        ----------
        channel : str
            Channel identifier ('a' or 'b').
        function : str
            Source function ('volt', 'voltage', 'amp', 'current').

        Raises
        ------
        ValueError
            If function is invalid.
        """
        channel = self._validate_channel(channel)
        function = function.lower()

        if function in ["volt", "voltage"]:
            self.write(f"smu{channel}.source.func = smu{channel}.OUTPUT_DCVOLTS")
        elif function in ["amp", "current"]:
            self.write(f"smu{channel}.source.func = smu{channel}.OUTPUT_DCAMPS")
        else:
            raise ValueError("Function must be 'volt'/'voltage' or 'amp'/'current'")

    def set_pulse_measured(self, channel: str, value: Any, ton: int | float, toff: int | float) -> None:
        """
        Configure pulse measurement (TODO: Verify function).

        Parameters
        ----------
        channel : str
            Channel identifier ('a' or 'b').
        value : Any
            Pulse value.
        ton : int | float
            On time.
        toff : int | float
            Off time.
        """
        channel = self._validate_channel(channel)
        self.write(f"ConfigPulseIMeasureV(smu{channel},{str(value)},{str(ton)},{str(toff)})")

    def set_offmode(self, channel: str, mode: str | int) -> None:
        """
        Set source output-off mode.

        Parameters
        ----------
        channel : str
            Channel identifier ('a' or 'b').
        mode : str | int
            Off mode ('normal'/0, 'zero'/1, 'high_z'/2).

        Raises
        ------
        ValueError
            If mode is invalid.
        """
        channel = self._validate_channel(channel)

        mode_mapping = {
            0: "NORMAL", 1: "ZERO", 2: "HIGH_Z",
            "normal": "NORMAL", "zero": "ZERO", "high_z": "HIGH_Z",
        }
        mode_normalized = mode_mapping.get(mode if isinstance(mode, int) else str(mode).lower())
        if mode_normalized is None:
            raise ValueError("Mode must be 0/1/2 or 'normal'/'zero'/'high_z'")

        self.write(f"smu{channel}.source.offmode = smu{channel}.OUTPUT_{mode_normalized}")

    # =============================================================================
    # Measure/SET Methods
    # =============================================================================

    def set_voltage_range_measures(self, channel: str, value: int | float) -> None:
        """This attribute contains the positive full-scale value of the measure range for voltage.
        Look up the datasheet! -> smuX.measure.rangeY.  You might want to keep it on auto!

        If the source function is the same as the measurement function (for example, sourcing voltage and measuring
        voltage), the measurement range is locked to be the same as the source range. However, the setting for the
        measure range is retained. If the source function is changed (for example, from sourcing voltage to sourcing
        current), the retained measurement range will be used.

        Parameters
        ----------
        channel : str
            Channel identifier ('a' or 'b').
        value : int | float
            Range in Volts.
        """
        channel = self._validate_channel(channel)
        value_formatted = self._format_scientific(value=value, precision=0)
        self.write(f"smu{channel}.measure.rangev = {value_formatted}")

    def set_current_range_measure(self, channel: str, value: int | float) -> None:
        """
        Set measure current range.

        If the source function is the same as the measurement function (for example, sourcing voltage and measuring
        voltage), the measurement range is locked to be the same as the source range. However, the setting for the
        measure range is retained. If the source function is changed (for example, from sourcing voltage to sourcing
        current), the retained measurement range will be used.

        Parameters
        ----------
        channel : str
            Channel identifier ('a' or 'b').
        value : int | float
            Range in Amperes.
        """
        channel = self._validate_channel(channel)
        value_formatted = self._format_scientific(value=value, precision=0)
        self.write(f"smu{channel}.measure.rangei = {value_formatted}")

    def set_measurement_range(self, channel: str, measurement_type: str, range_value: int | float) -> None:
        """
        Set measurement range for voltage or current.

        If the source function is the same as the measurement function (for example, sourcing voltage and measuring
        voltage), the measurement range is locked to be the same as the source range. However, the setting for the
        measure range is retained. If the source function is changed (for example, from sourcing voltage to sourcing
        current), the retained measurement range will be used.

        Parameters
        ----------
        channel : str
            Channel identifier ('a' or 'b').
        measurement_type : str
            Type ('volt', 'voltage', 'amp', 'current').
        range_value : int | float
            Range value.

        Raises
        ------
        ValueError
            If measurement type is invalid.
        """
        channel = self._validate_channel(channel)
        measurement_type = measurement_type.lower()
        range_str = self._format_scientific(range_value, precision=0)

        if measurement_type in ["volt", "voltage"]:
            self.write(f"smu{channel}.measure.rangev = {range_str}")
        elif measurement_type in ["amp", "current"]:
            self.write(f"smu{channel}.measure.rangei = {range_str}")
        else:
            raise ValueError("Measurement type must be 'volt'/'voltage' or 'amp'/'current'")

    # =============================================================================
    # Display Control
    # =============================================================================

    def set_channel_display(self, channel: str | None = None) -> None:
        """
        Set which channel(s) to display.

        Parameters
        ----------
        channel : str, optional
            Channel to display ('a' or 'b'). If None, displays both.
        """
        if channel is None:
            self.write("display.screen = display.SMUA_SMUB")
        else:
            channel = self._validate_channel(channel)
            self.write(f"display.screen = display.SMU{channel.upper()}")

    def set_display_measurement_function(self, channel: str, measurement_type: str) -> None:
        """
        Set displayed measurement function.

        Parameters
        ----------
        channel : str
            Channel identifier ('a' or 'b').
        measurement_type : str
            Measurement type ('v', 'i', 'r', 'p', etc.).

        Raises
        ------
        ValueError
            If measurement type is invalid.
        """
        channel = self._validate_channel(channel)
        measurement_type = self._Measurement_Types.get(measurement_type.lower())

        display_mapping = {
            "v": "_DCVOLTS", "i": "_DCAMPS", "r": "_OHMS", "p": "_WATTS",
        }
        display_func = display_mapping.get(measurement_type)
        if display_func is None:
            raise ValueError(f"Invalid measurement type. Valid options: {list(display_mapping.keys())}")

        self.write(f"display.smu{channel}.measure.func = display.MEASURE{display_func}")

    # =============================================================================
    # Get/Save Data
    # =============================================================================

    def get_data(self, channel: str | None = None) -> dict:
        """
        Get voltage and current measurements.

        Parameters
        ----------
        channel : str, optional
            Channel to measure ('a' or 'b'). If None, measures both.

        Returns
        -------
        dict
            Dictionary containing 'voltage_V', 'current_A', and 'channel(s)'.
        """
        if channel is None:
            voltages = []
            currents = []
            for ch in self._ChannelLS:
                voltages.append(self.get_voltage(ch))
                currents.append(self.get_current(ch))
            return {
                "voltage_V": voltages,
                "current_A": currents,
                "channels": [ch.upper() for ch in self._ChannelLS],
            }
        else:
            channel = self._validate_channel(channel)
            return {
                "voltage_V": self.get_voltage(channel),
                "current_A": self.get_current(channel),
                "channel": channel.upper(),
            }

    # =============================================================================
    # Convenience Methods
    # =============================================================================

    def setup_voltage_source(self, channel: str, voltage: float, current_limit: float) -> None:
        """
        Setup voltage source with current limit.

        Parameters
        ----------
        channel : str
            Channel identifier ('a' or 'b').
        voltage : float
            Voltage level in Volts.
        current_limit : float
            Current compliance in Amperes.
        """
        channel = self._validate_channel(channel)
        self.set_channel_display(channel)
        self.set_output_source_function(channel, "voltage")
        self.set_display_measurement_function(channel, "current")
        self.set_voltage(channel, voltage)
        self.set_current_limit(channel, current_limit)

    def setup_current_source(self, channel: str, current: float, voltage_limit: float) -> None:
        """
        Setup current source with voltage limit.

        Parameters
        ----------
        channel : str
            Channel identifier ('a' or 'b').
        current : float
            Current level in Amperes.
        voltage_limit : float
            Voltage compliance in Volts.
        """
        channel = self._validate_channel(channel)
        self.set_channel_display(channel)
        self.set_output_source_function(channel, "current")
        self.set_display_measurement_function(channel, "voltage")
        self.set_current(channel, current)
        self.set_voltage_limit(channel, voltage_limit)

    # =============================================================================
    # Send Lua Code
    # =============================================================================

    def validate_lua_script(self, lua_script: str) -> Tuple[str, str]:
        """
        Validates a Keithley 2612 Lua script to ensure:
        - It starts with 'loadscript <name>'
        - It ends with 'endscript'
        - A script name is provided

        Parameters
        ----------
        lua_script : str
            The Lua script content.

        Returns
        -------
        Tuple[str, str]
            (script_name, cleaned_script_content).

        Raises
        ------
        ValueError
            If script format is invalid (missing loadscript/endscript).
        """
        from textwrap import dedent
        lua_script = dedent(lua_script)
        lines = [line.strip() for line in lua_script.strip().splitlines() if line.strip()]

        if not lines:
            raise ValueError("Lua script is empty.")

        match = re.search(r"loadscript\s+([a-zA-Z_]\w*)", lines[0]) 
        if not match:
             # Try second line just in case user put newline first
             if len(lines) > 1:
                match = re.search(r"loadscript\s+([a-zA-Z_]\w*)", lines[1])

        if not match:
            raise ValueError("Script must include 'loadscript <name>'.")
        
        script_name = match.group(1)
        if "endscript" not in lines[-1]:
             raise ValueError("Script must end with 'endscript'.")

        return script_name, lua_script

    def define_lua_script(self, lua_script: str | None = None) -> None:
        """
        Load a Lua script into the instrument.

        Parameters
        ----------
        lua_script : str | None, optional
            The Lua script to load. If None, loads a default 'Hello World' script.
        """
        if lua_script is None:
            # Load Example Script. It prints: Hello World!
            lua_script = """
                loadscript my_script
                display.clear()
                myMessage = "Hello World!"
                for k = 1, string.len(myMessage) do
                    x = string.sub(myMessage, k, k)
                    display.settext(x)
                    print(x)
                    delay(1)
                end
                print("__END__")
                endscript
                """
        script_name, lua_script = self.validate_lua_script(lua_script)
        self.dict_of_lua_scripts[script_name] = lua_script
        self.write(lua_script)
        if script_name == "my_script":
           self.write("my_script.run()")
           self.read_after_lua_script(print_output=True)

    def execute_lua_script(self, script_name: str) -> None:
        """
        Execute a previously loaded Lua script.

        Parameters
        ----------
        script_name : str
            Name of the script to execute.

        Raises
        ------
        ValueError
            If script is not found in local cache.
        """
        if script_name not in self.dict_of_lua_scripts:
            raise ValueError(f"Script '{script_name}' not found.")
        self.write(f"{script_name}.run()")

    def delete_lua_script(self, script_name: str) -> None:
        """
        Delete a Lua script from the instrument and local cache.

        Parameters
        ----------
        script_name : str
            Name of the script to delete.
        """
        if script_name in self.dict_of_lua_scripts:
            self.write(f"{script_name} = nil")
            # script.delete not always available depending on firmware, using None assignment usually works
            del self.dict_of_lua_scripts[script_name]
        else:
             self.logger.warning(f"Script {script_name} not found locally.")

    def read_after_lua_script(self, print_output: bool = False) -> Tuple[List[str], str]:
        """
        Read output from the instrument after script execution.

        Parameters
        ----------
        print_output : bool, optional
            If True, logs the output. Default is False.

        Returns
        -------
        Tuple[List[str], str]
            (list_of_lines, full_output_string).
        """
        lines = []
        try:
            while True:
                line = self.read().strip()
                if line == "__END__":
                    break
                lines.append(line)
        except Exception: 
            # Timeout is expected if no more data
            pass
            
        full_output = "\n".join(lines)
        if print_output:
            self.logger.info("Lua Output:\n" + full_output)

        return lines, full_output

    def read_lua_table(self, lua_table_name: str) -> List[float]:
        """
        Read a Lua table from the instrument as a list of floats.

        Parameters
        ----------
        lua_table_name : str
            Name of the table to read.

        Returns
        -------
        List[float]
            List of values in the table.
        """
        try:
            raw_response = self.query(f"print(table.concat({lua_table_name}, ','))")
            if not raw_response:
                return []
            return [float(x) for x in raw_response.strip().split(',')]
        except Exception as e:
             self.logger.error(f"Failed to read table {lua_table_name}: {e}")
             return []

    # =============================================================================
    # Aliases for backwards compatibility
    # =============================================================================
    ask_Current = get_current
    ask_Voltage = get_voltage
    ask_Power = get_power
    ask_Resistance = get_resistance
    read_Measurement = read_measurement
    ask_VoltageRangeMeasure = get_voltage_range_measure
    ask_CurrentRangeMeasure = get_current_range_measure
    ask_AutoVoltageRangeMeasure = get_auto_voltage_range_measure
    ask_AutoCurrentRangeMeasure = get_auto_current_range_measure
    ask_LimitReached = get_limit_reached
    ask_AutoVoltageRange = get_auto_voltage_range
    ask_AutoCurrentRange = get_auto_current_range
    ask_VoltageRange = get_voltage_range
    ask_CurrentRange = get_current_range
    ask_VoltageLimit = get_voltage_limit
    ask_CurrentLimit = get_current_limit
    ask_VoltageSetting = get_voltage_setting
    ask_CurrentSetting = get_current_setting
    ask_OutputSourceFunction = get_output_source_function
    ask_readBuffer = get_read_buffer
    set_SourceOutput = set_source_output
    set_Out = set_source_output # Was alias in original
    set_MeasOutput = set_source_output # Was alias in original
    set_AutoVoltageRange = set_auto_voltage_range
    set_AutoCurrentRange = set_auto_current_range
    set_VoltageRange = set_voltage_range
    set_CurrentRange = set_current_range
    set_VoltageLimit = set_voltage_limit
    set_CurrentLimit = set_current_limit
    set_Voltage = set_voltage
    set_Current = set_current
    set_OutputSourceFunction = set_output_source_function
    set_PulseMeasured = set_pulse_measured
    set_offmode = set_offmode
    set_VoltageRangeMeasure = set_voltage_range_measure
    set_CurrentRangeMeasure = set_current_range_measure
    set_MeasurementRange = set_measurement_range
    set_ChannelDisplay = set_channel_display
    set_DisplayMeasurementFunction = set_display_measurement_function
    get_Data = get_data