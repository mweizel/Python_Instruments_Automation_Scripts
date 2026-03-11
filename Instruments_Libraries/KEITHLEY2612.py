"""
Created on Fri Dec 10 08:39:48 2021

@author: Martin.Mihaylov
@author: Maxim Weizel
"""

import re
from typing import Any

from .BaseInstrument import BaseInstrument


class KEITHLEY2612(BaseInstrument):
    """
    Driver for Keithley 2612 SourceMeter using BaseInstrument.
    """

    def __init__(self, resource_str: str, visa_library: str = "@py", **kwargs):
        """
        Initialize the Keithley 2612 SourceMeter.

        Parameters
        ----------
        resource_str : str
            The VISA resource string (e.g., 'COMXX').
        **kwargs : dict
            Additional keyword arguments passed to the BaseInstrument constructor.
        """
        super().__init__(resource_str, visa_library=visa_library, **kwargs)

        idn = self.get_idn()
        if "2612" not in idn:
            self.logger.warning(f"Device at {resource_str} may not be a Keithley 2612. IDN: {idn}")
        else:
            self.logger.info(f"Connected to: {idn}")

        kwargs.setdefault("read_termination", "\n")
        self._resource.read_termination = kwargs["read_termination"]

        # Internal Variables
        self._ChannelLS = ["a", "b"]
        self._Measurement_Types = {
            "voltage": "v",
            "volt": "v",
            "v": "v",
            "current": "i",
            "amp": "i",
            "i": "i",
            "power": "p",
            "watt": "p",
            "p": "p",
            "resistance": "r",
            "ohm": "r",
            "r": "r",
        }
        self.dict_of_lua_scripts = {}

        # Voltage and current limits for safety
        self._absolute_Voltage_Limits = {"min": 0, "max": 200}
        self._Voltage_Limits = {"min": 0, "max": 10.0}
        self._Current_Limits = {"min": 0, "max": 3.0}

    # =============================================================================
    # Checks and Validations
    # =============================================================================

    def validate_channel(self, channel: str) -> str:
        """
        Validate and normalize channel input.
        Returns the normalized channel string ('a' or 'b').

        Parameters
        ----------
        channel : str
            Channel identifier. Valid options: ``'a'``, ``'b'``.

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

    def validate_state(self, state: int | str | bool, output: bool = False) -> str:
        """
        Validate and normalize state input.

        Parameters
        ----------
        state : int | str | bool
            State to validate. Valid options: ``1``, ``0``, ``True``, ``False``, ``'ON'``,
            ``'OFF'``.
        output : bool, optional
            If True, allows 'HIGH_Z' state. Default is False.

        Returns
        -------
        str
            Normalized state string (e.g., 'ON', 'OFF', 'HIGH_Z').
        """
        if output and str(state).upper() in ["2", "HIGH_Z"]:
            return "HIGH_Z"
        return self._parse_state(state)

    def format_scientific(self, value: int | float, precision: int = 4) -> str:
        """
        Format number in scientific notation consistently.

        Parameters
        ----------
        value : int | float
            The value to format.
        precision : int, optional
            Number of decimal places. Default is 4.
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
        channel = self.validate_channel(channel)
        self.write(f"smu{channel}.reset()")

    def clear_error_queue(self) -> None:
        """Clear the instrument's error queue."""
        self.write("errorqueue.clear()")

    # =============================================================================
    # Measurement/GET Methods
    # =============================================================================

    def measure_current(self, channel: str) -> float:
        """
        Measure current on the specified channel.

        Parameters
        ----------
        channel : str
            Channel identifier. Valid options: ``'a'``, ``'b'``.

        """
        channel = self.validate_channel(channel)
        return float(self.query(f"print(smu{channel}.measure.i())"))

    def measure_voltage(self, channel: str) -> float:
        """
        Measure voltage on the specified channel.

        Parameters
        ----------
        channel : str
            Channel identifier. Valid options: ``'a'``, ``'b'``.

        """
        channel = self.validate_channel(channel)
        return float(self.query(f"print(smu{channel}.measure.v())"))

    def measure_power(self, channel: str) -> float:
        """
        Measure power on the specified channel.

        Parameters
        ----------
        channel : str
            Channel identifier. Valid options: ``'a'``, ``'b'``.

        """
        channel = self.validate_channel(channel)
        return float(self.query(f"print(smu{channel}.measure.p())"))

    def measure_resistance(self, channel: str) -> float:
        """
        Measure resistance on the specified channel.

        Parameters
        ----------
        channel : str
            Channel identifier. Valid options: ``'a'``, ``'b'``.

        """
        channel = self.validate_channel(channel)
        return float(self.query(f"print(smu{channel}.measure.r())"))

    def read_measurement(self, channel: str, type_: str) -> float:
        """
        Perform a measurement of the specified type.

        Parameters
        ----------
        channel : str
            Channel identifier. Valid options: ``'a'``, ``'b'``.
        type_ : str
            Type of measurement (e.g., 'voltage', 'current', 'power', 'resistance').
        """
        channel = self.validate_channel(channel)
        meas_type = self._check_scpi_param(
            type_,
            ["VOLTage", "CURRent", "POWer", "RESistance", "V", "I", "P", "R", "AMP", "OHM", "WATT"],
        )
        meas_code = self._Measurement_Types.get(meas_type.lower())
        return float(self.query(f"print(smu{channel}.measure.{meas_code}())"))

    def get_voltage_range_measure(self, channel: str) -> float:
        """
        Get measurement voltage range.

        If the source function is the same as the measurement function (for example,
        sourcing voltage and measuring voltage), the measurement range is locked to
        be the same as the source range. However, the setting for the measure range
        is retained. If the source function is changed (for example, from sourcing
        voltage to sourcing current), the retained measurement range will be used.

        Parameters
        ----------
        channel : str
            Channel identifier. Valid options: ``'a'``, ``'b'``.

        """
        channel = self.validate_channel(channel)
        return float(self.query(f"print(smu{channel}.measure.rangev)"))

    def get_current_range_measure(self, channel: str) -> float:
        """This attribute contains the smuX.measure.rangeY current setting. Look up the datasheet!

        If the source function is the same as the measurement function (for example,
        sourcing voltage and measuring voltage), the measurement range is locked to
        be the same as the source range. However, the setting for the measure range
        is retained. If the source function is changed (for example, from sourcing
        voltage to sourcing current), the retained measurement range will be used.

        Parameters
        ----------
        channel : str
            Channel identifier. Valid options: ``'a'``, ``'b'``.

        """
        channel = self.validate_channel(channel)
        return float(self.query(f"print(smu{channel}.measure.rangei)"))

    def get_auto_voltage_range_measure(self, channel: str) -> int:
        """
        Get measurement auto voltage range status (1 if enabled, 0 if disabled).
        You might want to keep it on auto i.e. 1 or "ON"!

        Parameters
        ----------
        channel : str
            Channel identifier. Valid options: ``'a'``, ``'b'``.
        """
        channel = self.validate_channel(channel)
        return int(float(self.query(f"print(smu{channel}.measure.autorangev)")))

    def get_auto_current_range_measure(self, channel: str) -> int:
        """
        Get measurement auto current range status (1 if enabled, 0 if disabled).
        You might want to keep it on auto i.e. 1 or "ON"!

        Parameters
        ----------
        channel : str
            Channel identifier. Valid options: ``'a'``, ``'b'``.
        """
        channel = self.validate_channel(channel)
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
            Channel identifier. Valid options: ``'a'``, ``'b'``.
        """
        channel = self.validate_channel(channel)
        response = self.query(f"print(smu{channel}.source.compliance)").lower()
        return response == "true"

    def get_auto_voltage_range(self, channel: str) -> int:
        """
        Get source auto voltage range status (1 if enabled, 0 if disabled).
        You might want to keep it on auto i.e. 1 or "ON"!

        Parameters
        ----------
        channel : str
            Channel identifier. Valid options: ``'a'``, ``'b'``.
        """
        channel = self.validate_channel(channel)
        return int(float(self.query(f"print(smu{channel}.source.autorangev)")))

    def get_auto_current_range(self, channel: str) -> int:
        """
        Get source auto current range status (1 if enabled, 0 if disabled).
        You might want to keep it on auto i.e. 1 or "ON"!

        Parameters
        ----------
        channel : str
            Channel identifier. Valid options: ``'a'``, ``'b'``.
        """
        channel = self.validate_channel(channel)
        return int(float(self.query(f"print(smu{channel}.source.autorangei)")))

    def get_voltage_range(self, channel: str) -> float:
        """
        Get source voltage range.

        Parameters
        ----------
        channel : str
            Channel identifier. Valid options: ``'a'``, ``'b'``.

        """
        channel = self.validate_channel(channel)
        return float(self.query(f"print(smu{channel}.source.rangev)"))

    def get_current_range(self, channel: str) -> float:
        """
        Get source current range.

        Parameters
        ----------
        channel : str
            Channel identifier. Valid options: ``'a'``, ``'b'``.

        """
        channel = self.validate_channel(channel)
        return float(self.query(f"print(smu{channel}.source.rangei)"))

    def get_voltage_limit(self, channel: str) -> float:
        """
        Get source voltage limit.

        Parameters
        ----------
        channel : str
            Channel identifier. Valid options: ``'a'``, ``'b'``.

        """
        channel = self.validate_channel(channel)
        return float(self.query(f"print(smu{channel}.source.levelv)"))

    def get_current_limit(self, channel: str) -> float:
        """
        Get source current limit.

        Parameters
        ----------
        channel : str
            Channel identifier. Valid options: ``'a'``, ``'b'``.

        """
        channel = self.validate_channel(channel)
        return float(self.query(f"print(smu{channel}.source.leveli)"))

    def get_voltage_setting(self, channel: str) -> float:
        """
        Get source voltage setting.

        Parameters
        ----------
        channel : str
            Channel identifier. Valid options: ``'a'``, ``'b'``.

        """
        channel = self.validate_channel(channel)
        return float(self.query(f"print(smu{channel}.source.levelv)"))

    def get_current_setting(self, channel: str) -> float:
        """
        Get source current setting.

        Parameters
        ----------
        channel : str
            Channel identifier. Valid options: ``'a'``, ``'b'``.

        """
        channel = self.validate_channel(channel)
        return float(self.query(f"print(smu{channel}.source.leveli)"))

    def get_output_source_function(self, channel: str) -> int:
        """
        Get source output function (1 if voltage, 0 if current).

        Parameters
        ----------
        channel : str
            Channel identifier. Valid options: ``'a'``, ``'b'``.
        """
        channel = self.validate_channel(channel)
        return int(float(self.query(f"print(smu{channel}.source.func)")))

    # =============================================================================
    # Further GET Methods
    # =============================================================================

    def get_read_buffer(self, channel: str, start: int, stop: int) -> None:
        """
        TODO: This function should be checked. Also is doesn't return anything at the moment.
        """
        channel = self.validate_channel(channel)
        self.query(f"printbuffer({str(start)},{str(stop)},smu{str(channel)})")

    # =============================================================================
    # Source/SET Methods
    # =============================================================================

    def set_output(self, channel: str, state: int | str | bool) -> None:
        """
        Set source output state (on or off).

        Parameters
        ----------
        channel : str
            Channel identifier. Valid options: ``'a'``, ``'b'``.
        state : int | str | bool
            Output state. Valid options: ``1``, ``0``, ``True``, ``False``, ``'ON'``, ``'OFF'``.
        """
        channel = self.validate_channel(channel)
        state_normalized = self.validate_state(state, output=True)
        self.write(f"smu{channel}.source.output = smu{channel}.OUTPUT_{state_normalized}")

    set_out = set_output
    set_source_output = set_output
    set_meas_output = set_output

    def set_auto_voltage_range(self, channel: str, state: int | str | bool) -> None:
        """
        Set source autorange voltage control.

        Parameters
        ----------
        channel : str
            Channel identifier. Valid options: ``'a'``, ``'b'``.
        state : int | str | bool
            Status. Valid options: ``'ON'``, ``'OFF'``.
        """
        channel = self.validate_channel(channel)
        state_normalized = self.validate_state(state)
        self.write(f"smu{channel}.source.autorangev = smu{channel}.AUTORANGE_{state_normalized}")

    def set_auto_current_range(self, channel: str, state: int | str | bool) -> None:
        """
        Set source autorange current control.

        Parameters
        ----------
        channel : str
            Channel identifier. Valid options: ``'a'``, ``'b'``.
        state : int | str | bool
            Status. Valid options: ``'ON'``, ``'OFF'``.
        """
        channel = self.validate_channel(channel)
        state_normalized = self.validate_state(state)
        self.write(f"smu{channel}.source.autorangei = smu{channel}.AUTORANGE_{state_normalized}")

    def set_voltage_range(self, channel: str, value: int | float) -> None:
        """
        Set source voltage range.

        Parameters
        ----------
        channel : str
            Channel identifier. Valid options: ``'a'``, ``'b'``.
        value : int | float
            Voltage range Unit: ``'V'``.
        """
        channel = self.validate_channel(channel)
        value_formatted = self.format_scientific(value=value, precision=0)
        self.write(f"smu{channel}.source.rangev = {value_formatted}")

    def set_current_range(self, channel: str, value: int | float) -> None:
        """
        Set source current range.

        Parameters
        ----------
        channel : str
            Channel identifier. Valid options: ``'a'``, ``'b'``.
        value : int | float
            Current range Unit: ``'A'``.
        """
        channel = self.validate_channel(channel)
        value_formatted = self.format_scientific(value=value, precision=0)
        self.write(f"smu{channel}.source.rangei = {value_formatted}")

    def set_voltage_limit(
        self, channel: str, limit: int | float, high_voltage: bool = False
    ) -> None:
        """
        Set voltage source compliance.

        Parameters
        ----------
        channel : str
            Channel identifier. Valid options: ``'a'``, ``'b'``.
        limit : int | float
            Voltage limit Unit: ``'V'``.
        high_voltage : bool, optional
            Enable high voltage range (>10V). Default is False.

        Raises
        ------
        ValueError
            If limit is out of range.
        """
        channel = self.validate_channel(channel)
        if high_voltage:
            if not (
                self._absolute_Voltage_Limits["min"]
                <= limit
                <= self._absolute_Voltage_Limits["max"]
            ):
                raise ValueError(
                    f"""Voltage limit must be between {self._absolute_Voltage_Limits["min"]} 
                    and {self._absolute_Voltage_Limits["max"]} V"""
                )
        else:
            if not (self._Voltage_Limits["min"] <= limit <= self._Voltage_Limits["max"]):
                raise ValueError(
                    f"""Voltage limit must be between {self._Voltage_Limits["min"]} 
                    and {self._Voltage_Limits["max"]} V.
                    If you want more than 10V, use high_voltage = True."""
                )

        limit_str = self.format_scientific(value=limit, precision=4)
        self.write(f"smu{channel}.source.limitv = {limit_str}")

    def set_current_limit(self, channel: str, limit: int | float) -> None:
        """Sets current source compliance. Use to limit the current output
        when in the voltage source mode. This attribute should be set in the
        test sequence before turning the source on.

        Parameters
        ----------
        channel : str
            Channel identifier. Valid options: ``'a'``, ``'b'``.
        limit : int | float
            Current limit Unit: ``'A'``.

        Raises
        ------
        ValueError
            If limit is out of range.
        """
        channel = self.validate_channel(channel)
        if not (self._Current_Limits["min"] < limit < self._Current_Limits["max"]):
            raise ValueError(
                f"""Current limit must be between {self._Current_Limits["min"]} 
                and {self._Current_Limits["max"]} A"""
            )

        limit_str = self.format_scientific(value=limit, precision=4)
        self.write(f"smu{channel}.source.limiti = {limit_str}")

    def set_voltage(self, channel: str, voltage: int | float, high_voltage: bool = False) -> None:
        """
        Set source voltage level.

        Parameters
        ----------
        channel : str
            Channel identifier. Valid options: ``'a'``, ``'b'``.
        voltage : int | float
            Voltage to set Unit: ``'V'``.
        high_voltage : bool, optional
            Enable high voltage range (>10V). Default is False.

        Raises
        ------
        ValueError
            If voltage is out of range.
        """
        channel = self.validate_channel(channel)
        if high_voltage:
            if not (
                self._absolute_Voltage_Limits["min"]
                <= voltage
                <= self._absolute_Voltage_Limits["max"]
            ):
                raise ValueError(
                    f"""Voltage must be between {self._absolute_Voltage_Limits["min"]} 
                    and {self._absolute_Voltage_Limits["max"]} V"""
                )
        else:
            if not (self._Voltage_Limits["min"] <= voltage <= self._Voltage_Limits["max"]):
                raise ValueError(
                    f"""Voltage must be between {self._Voltage_Limits["min"]} 
                      and {self._Voltage_Limits["max"]} V. 
                    If you want more than 10V, use high_voltage = True."""
                )

        voltage_str = self.format_scientific(value=voltage, precision=4)
        self.write(f"smu{channel}.source.levelv = {voltage_str}")

    def set_current(self, channel: str, current: int | float) -> None:
        """
        Set source current level.

        Parameters
        ----------
        channel : str
            Channel identifier. Valid options: ``'a'``, ``'b'``.
        current : int | float
            Current to set Unit: ``'A'``.

        Raises
        ------
        ValueError
            If current is out of range.
        """
        channel = self.validate_channel(channel)
        if not (self._Current_Limits["min"] < current < self._Current_Limits["max"]):
            raise ValueError(
                f"""Current must be between {self._Current_Limits["min"]} 
                and {self._Current_Limits["max"]} A"""
            )
        current_str = self.format_scientific(value=current, precision=4)
        self.write(f"smu{channel}.source.leveli = {current_str}")

    def set_output_source_function(self, channel: str, function: str) -> None:
        """
        Set source function (V or I).

        Parameters
        ----------
        channel : str
            Channel identifier. Valid options: ``'a'``, ``'b'``.
        function : str
            Source function.

            * ``'volt'`` / ``'voltage'`` : Voltage source
            * ``'amp'`` / ``'current'`` : Current source
        """
        channel = self.validate_channel(channel)
        func_type = self._check_scpi_param(function, ["VOLTage", "CURRent", "V", "I", "AMP"])

        func_target = (
            "OUTPUT_DCVOLTS"
            if func_type.startswith("VOLT") or func_type == "V"
            else "OUTPUT_DCAMPS"
        )
        self.write(f"smu{channel}.source.func = smu{channel}.{func_target}")

    def set_pulse_measured(
        self, channel: str, value: Any, ton: int | float, toff: int | float
    ) -> None:
        """
        Configure pulse measurement (TODO: Verify function).

        Parameters
        ----------
        channel : str
            Channel identifier. Valid options: ``'a'``, ``'b'``.
        value : Any
            Pulse value.
        ton : int | float
            On time.
        toff : int | float
            Off time.
        """
        channel = self.validate_channel(channel)
        self.write(f"ConfigPulseIMeasureV(smu{channel},{str(value)},{str(ton)},{str(toff)})")

    def set_offmode(self, channel: str, mode: str | int) -> None:
        """
        Set source output-off mode.

        Parameters
        ----------
        channel : str
            Channel identifier. Valid options: ``'a'``, ``'b'``.
        mode : str | int
            Off mode.

            * ``'normal'`` / ``0`` : normal mode
            * ``'zero'`` / ``1`` : zero mode
            * ``'high_z'`` / ``2`` : high impedance mode
        """
        channel = self.validate_channel(channel)

        mode_str = str(mode).upper().replace("HIGHZ", "HIGH_Z")
        mode_mapping = {"0": "NORMal", "1": "ZERO", "2": "HIGH_Z"}
        mode_to_check = mode_mapping.get(mode_str, mode_str)

        mode_normalized = self._check_scpi_param(mode_to_check, ["NORMal", "ZERO", "HIGH_Z"])
        self.write(f"smu{channel}.source.offmode = smu{channel}.OUTPUT_{mode_normalized}")

    # =============================================================================
    # Measure/SET Methods
    # =============================================================================

    def set_voltage_range_measure(self, channel: str, value: int | float) -> None:
        """This attribute contains the positive full-scale value of the measure range for voltage.
        Look up the datasheet! -> smuX.measure.rangeY.  You might want to keep it on auto!

        If the source function is the same as the measurement function (for example,
        sourcing voltage and measuring voltage), the measurement range is locked to be
        the same as the source range. However, the setting for the measure range is retained.
        If the source function is changed (for example, from sourcing voltage to sourcing
        current), the retained measurement range will be used.

        Parameters
        ----------
        channel : str
            Channel identifier. Valid options: ``'a'``, ``'b'``.
        value : int | float
            Range Unit: ``'V'``.
        """
        channel = self.validate_channel(channel)
        value_formatted = self.format_scientific(value=value, precision=0)
        self.write(f"smu{channel}.measure.rangev = {value_formatted}")

    def set_current_range_measure(self, channel: str, value: int | float) -> None:
        """
        Set measure current range.

        If the source function is the same as the measurement function (for example,
        sourcing voltage and measuring voltage), the measurement range is locked to be
        the same as the source range. However, the setting for the measure range is retained.
        If the source function is changed (for example, from sourcing voltage to sourcing
        current), the retained measurement range will be used.

        Parameters
        ----------
        channel : str
            Channel identifier. Valid options: ``'a'``, ``'b'``.
        value : int | float
            Range Unit: ``'A'``.
        """
        channel = self.validate_channel(channel)
        value_formatted = self.format_scientific(value=value, precision=0)
        self.write(f"smu{channel}.measure.rangei = {value_formatted}")

    def set_measurement_range(
        self, channel: str, measurement_type: str, range_value: int | float
    ) -> None:
        """
        Set measurement range for voltage or current.

        If the source function is the same as the measurement function (for example,
        sourcing voltage and measuring voltage), the measurement range is locked to be
        the same as the source range. However, the setting for the measure range is retained.
        If the source function is changed (for example, from sourcing voltage to sourcing
        current), the retained measurement range will be used.

        Parameters
        ----------
        channel : str
            Channel identifier. Valid options: ``'a'``, ``'b'``.
        measurement_type : str
            Type.

            * ``'volt'`` / ``'voltage'`` : Voltage measurement
            * ``'amp'`` / ``'current'`` : Current measurement
        range_value : int | float
            Range value.
        """
        channel = self.validate_channel(channel)
        meas_type = self._check_scpi_param(
            measurement_type, ["VOLTage", "CURRent", "V", "I", "AMP"]
        )
        range_str = self.format_scientific(range_value, precision=0)

        if meas_type.startswith("VOLT") or meas_type == "V":
            self.write(f"smu{channel}.measure.rangev = {range_str}")
        else:
            self.write(f"smu{channel}.measure.rangei = {range_str}")

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
            channel = self.validate_channel(channel)
            self.write(f"display.screen = display.SMU{channel.upper()}")

    def set_display_measurement_function(self, channel: str, measurement_type: str) -> None:
        """
        Set displayed measurement function.

        Parameters
        ----------
        channel : str
            Channel identifier. Valid options: ``'a'``, ``'b'``.
        measurement_type : str
            Measurement type. Valid options: ``'v'``, ``'i'``, ``'r'``, ``'p'``.
        """
        channel = self.validate_channel(channel)
        meas_type = self._check_scpi_param(
            measurement_type,
            ["VOLTage", "CURRent", "POWer", "RESistance", "V", "I", "P", "R", "AMP", "OHM", "WATT"],
        )
        meas_code = self._Measurement_Types.get(meas_type.lower())

        display_mapping = {
            "v": "_DCVOLTS",
            "i": "_DCAMPS",
            "r": "_OHMS",
            "p": "_WATTS",
        }
        display_func = display_mapping.get(meas_code)

        self.write(f"display.smu{channel}.measure.func = display.MEASURE{display_func}")

    # =============================================================================
    # Get/Save Data
    # =============================================================================

    def get_data(self, channel: str | None = None) -> dict:
        """
        Get voltage and current measurements.
        Returns dictionary containing 'voltage_V', 'current_A', and 'channel(s)'.

        Parameters
        ----------
        channel : str, optional
            Channel to measure ('a' or 'b'). If None, measures both.
        """
        if channel is None:
            voltages = []
            currents = []
            for ch in self._ChannelLS:
                voltages.append(self.measure_voltage(ch))
                currents.append(self.measure_current(ch))
            return {
                "voltage_V": voltages,
                "current_A": currents,
                "channels": [ch.upper() for ch in self._ChannelLS],
            }
        else:
            channel = self.validate_channel(channel)
            return {
                "voltage_V": self.measure_voltage(channel),
                "current_A": self.measure_current(channel),
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
            Channel identifier. Valid options: ``'a'``, ``'b'``.
        voltage : float
            Voltage level Unit: ``'V'``.
        current_limit : float
            Current compliance Unit: ``'A'``.
        """
        channel = self.validate_channel(channel)
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
            Channel identifier. Valid options: ``'a'``, ``'b'``.
        current : float
            Current level Unit: ``'A'``.
        voltage_limit : float
            Voltage compliance Unit: ``'V'``.
        """
        channel = self.validate_channel(channel)
        self.set_channel_display(channel)
        self.set_output_source_function(channel, "current")
        self.set_display_measurement_function(channel, "voltage")
        self.set_current(channel, current)
        self.set_voltage_limit(channel, voltage_limit)

    # =============================================================================
    # Send Lua Code
    # =============================================================================

    def validate_lua_script(self, lua_script: str) -> tuple[str, str]:
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
        tuple[str, str]
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
            # script.delete not always available depending on firmware
            # using None assignment usually works
            del self.dict_of_lua_scripts[script_name]
        else:
            self.logger.warning(f"Script {script_name} not found locally.")

    def read_after_lua_script(self, print_output: bool = False) -> tuple[list[str], str]:
        """
        Read output from the instrument after script execution.

        Parameters
        ----------
        print_output : bool, optional
            If True, logs the output. Default is False.

        Returns
        -------
        tuple[list[str], str]
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

    def read_lua_table(self, lua_table_name: str) -> list[float]:
        """
        Read a Lua table from the instrument as a list of floats.

        Parameters
        ----------
        lua_table_name : str
            Name of the table to read.

        Returns
        -------
        list[float]
            List of values in the table.
        """
        try:
            raw_response = self.query(f"print(table.concat({lua_table_name}, ','))")
            if not raw_response:
                return []
            return [float(x) for x in raw_response.strip().split(",")]
        except Exception as e:
            self.logger.error(f"Failed to read table {lua_table_name}: {e}")
            return []
