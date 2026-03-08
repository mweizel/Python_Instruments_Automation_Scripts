""" "
Created on Fir Feb 02 13:00:00 2024

@author: mweizel
"""

from .BaseInstrument import BaseInstrument


class SMA100B(BaseInstrument):
    """
    A class thats uses pyvisa to connect to an SMA100B Signal Generator.
    """

    def __init__(self, resource_str: str, visa_library: str = "@py", **kwargs):
        # BaseInstrument handles parsing of IP addresses if "TCPIP" is missing
        super().__init__(resource_str=resource_str, visa_library=visa_library, **kwargs)

    # =============================================================================
    # Communication Wrappers (Inherited from BaseInstrument)
    # =============================================================================

    # write, query, close (Close), reset are inherited.

    # =============================================================================
    # Validate Variables
    # =============================================================================

    # Uses BaseInstrument._parse_state which returns 'ON'/'OFF'.

    # =============================================================================
    # Ask Commands
    # =============================================================================

    def get_output_impedance(self) -> float:
        """Queries the impedance of the RF output."""
        return float(self.query(":OUTPut1:IMP?"))

    # =============================================================================
    # Set Commands
    # =============================================================================

    def set_rf_output_all(self, state: int | str) -> None:
        """Activates all Signal Genrator RF Outputs

        Parameters
        ----------
        state : str/int
            'ON' 1 or 'OFF' 0

        Raises
        ------
        ValueError
            Valid values are: \'ON\', \'OFF\', 1, 0
        """
        state = self._parse_state(state)
        self.write(f":OUTPut:ALL:STATe {state}")

    def set_rf_output(self, state: int | str) -> None:
        """Activates the Signal Genrator RF Output.

        Parameters
        ----------
        state : str/int
            'ON' 1 or 'OFF' 0

        Raises
        ------
        ValueError
            Valid values are: \'ON\', \'OFF\', 1, 0
        """
        state = self._parse_state(state)
        self.write(f":OUTPut {state}")

    def set_output(self, state: int | str) -> None:
        """Activates the Signal Genrator RF Output.

        Parameters
        ----------
        state : str/int
            'ON' 1 or 'OFF' 0

        Raises
        ------
        ValueError
            Valid values are: \'ON\', \'OFF\', 1, 0
        """
        self.set_rf_output(state)

    def set_dc_offset(self, value: int | float) -> None:
        """


        Parameters
        ----------
        value : int/float
            Sets the value of the DC offset.
            Range: -5 to 5
            Increment: 0.001
        """
        if value >= -5 and value <= 5:
            self.write(f":CSYNthesis:OFFSet {value}")
        else:
            raise ValueError("Allowed Offsets are numbers between -5 and 5!")

    def set_cmos_voltage(self, value: int | float) -> None:
        """


        Parameters
        ----------
        value : int/float
            Sets the voltage for the CMOS signal.
            Range: 0.8 to 2.7
            Increment: 0.001

        Raises
        ------
        ValueError
            Wrong range Error.

        """
        if value >= 0.8 and value <= 2.7:
            self.write(f":CSYNthesis:VOLTage {value}")
        else:
            raise ValueError("Wrong Value. Allowed values are between o.8 and 2.7!")

    def set_clock_sig_phase(self, value: int | float) -> None:
        """


        Parameters
        ----------
        value : int/float
            Shifts the phase of the generated clock signal.
            Range: -36000 to 36000
            Increment: 0.1


        Raises
        ------
        ValueError
            Wrong Value Error.

        """
        if value >= -36000 and value <= 36000:
            self.write(f":CSYNthesis:PHASe {value}")
        else:
            raise ValueError("Wrong value range! Allowed values between -36000 and 36000!")

    # =============================================================================
    # SOURce:FREQuency subsystem
    # =============================================================================

    def set_frequency_mode(self, mode: str) -> None:
        """
        Parameters
        ----------
        mode : str
            <Mode> CW | FIXed | SWEep | LIST | COMBined

            CW|FIXed
                Sets the fixed frequency mode. CW and FIXed are synonyms.
                The instrument operates at a defined frequency.

            SWEep
                Sets sweep mode.
                The instrument processes frequency (and level) settings in
                defined sweep steps.

            LIST
                Sets list mode.
                The instrument processes frequency and level settings by
                means of values loaded from a list.

            COMBined
                Sets the combined RF frequency / level sweep mode.
                The instrument processes frequency and level settings in
                defined sweep steps.
        """

        valid_mode = self._check_scpi_param(mode, ["CW", "FIXed", "SWEep", "LIST", "COMBined"])
        self.write(f":FREQuency:MODE {valid_mode}")

    def set_freq_cw(self, value: int | float, unit: str | None = None) -> None:
        """
        Parameters
        ----------
        value : int/float
            Parameter Frequency

        unit : str (optional)
            Frequency Unit: 'GHz' or 'MHz' or 'Hz'

        """

        min_freq = 8e3  # 8 kHz
        max_freq = 72e9  # 67 GHz calibrated, 72 GHz max

        if unit == "Hz" or unit is None:
            unit = "Hz"
            if value <= max_freq and value >= min_freq:
                self.write(f":SOURce:FREQuency:CW {value} {unit}")
            else:
                raise ValueError("Minimum Frequency = 8 kHz and Maximum Frequency = 67 GHz")
        elif unit == "MHz":
            if value * 1e6 <= max_freq and value * 1e6 >= min_freq:
                self.write(f":SOURce:FREQuency:CW {value} {unit}")
            else:
                raise ValueError("Minimum Frequency = 8 kHz and Maximum Frequency = 67 GHz")
        elif unit == "GHz":
            if value * 1e9 <= max_freq and value * 1e9 >= min_freq:
                self.write(f":SOURce:FREQuency:CW {value} {unit}")
            else:
                raise ValueError("Minimum Frequency = 8 kHz and Maximum Frequency = 67 GHz")
        else:
            raise ValueError('Unknown input! Unit must be None or "MHz" or "GHz"!')

    # =============================================================================
    # Activate Commands
    # =============================================================================

    def activate_dc_offset(self, state) -> None:
        """Activates a DC offset.

        Parameters
        ----------
        state : str
            'ON' 1 or 'OFF' 0
        """
        state = self._parse_state(state)
        self.write(f":CSYNthesis:OFFSet:STATe {state}")

    # =============================================================================
    # SOURce:POWer subsystem
    # =============================================================================

    def set_rf_power(self, value: int | float) -> None:
        """Sets the Signal Generator Output Power in dBm.

        Parameters
        ----------
        value : int/float
            Output Power in dBm
        """
        min_val = -20.0
        max_val = 30.0
        if value > max_val or value < min_val:
            raise ValueError(
                f"Power out of range! You can set power between {min_val} and {max_val} dBm!"
            )

        self.write(f"SOURce:POWer:LEVel:IMMediate:AMPlitude {value}")

