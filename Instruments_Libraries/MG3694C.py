"""
Created on Wed Dec  1 07:00:19 2021

@author: Martin.Mihylov

Currently the Anritsu MG3694C Signal Generator is in dynamic DHCP mode!!!
    1) Make sure Instrument and PC are connected vie ethernet cable.
    2) In the Windows terminal run: arp -a
    3) Find the IP-Adress corresponding to the MAC:Adress printed on the device
    4) If it does not show up try opening NI-MAX and run auto-discover.
    5) Try "arp -a" again.

Legacy instructions (not applicable as of 13.01.2026):
    1) Go to Network Adapter Settings -> 'Internetprotocoll, Version 4(TCP/IPv4)'
    2) Change the IP-Address from 'automatic' to 'static' and give the IP:192.168.0.1
    3) DNS will be filled automatically! Press 'OK' and leave.
    4) The standard IP of the instrument is: 192.168.0.254
    5) After your measurement dont forget to change the IP back to 'automatic'!
"""

import functools
import time
from collections.abc import Callable
from typing import Any, cast

import numpy as np
import pyvisa as visa
import pyvisa.constants as vi_const

from .BaseInstrument import BaseInstrument

try:
    from typing import deprecated  # type: ignore
except ImportError:
    from typing_extensions import deprecated


def auto_reconnect(func: Callable) -> Callable:
    """
    Decorator that catches VISA errors, reconnects, and retries the command.
    """

    @functools.wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> Any:
        attempts = 3
        for i in range(attempts):
            try:
                # Try to execute the function (write/query)
                return func(self, *args, **kwargs)
            except (visa.errors.VisaIOError, OSError) as e:
                # If it's the last attempt, raise the error
                if i == attempts - 1:
                    print(f"Failed after {attempts} attempts. Error: {e}")
                    raise e

                print(
                    f"""Connection lost during {getattr(func, "__name__", "function")}. 
                    Reconnecting (Attempt {i + 1}/{attempts})..."""
                )
                try:
                    self.reconnect()
                except Exception as reconnect_err:
                    print(f"Reconnect failed: {reconnect_err}")
                    time.sleep(1)  # Wait a bit before next loop

    return wrapper


class MG3694C(BaseInstrument):
    """
    This class uses pyvisa to connect to an Anritsu MG3694C Signal Generator.
    """

    def __init__(self, resource_str: str = "192.168.0.254", visa_library: str = "@ivi", **kwargs):
        kwargs.setdefault("read_termination", "\n")
        kwargs.setdefault("query_delay", 0.5)
        self._pyvisa_kwargs = kwargs
        super().__init__(str(resource_str), visa_library=visa_library, **kwargs)
        self.visa_library = visa_library

        try:
            self._resource.set_visa_attribute(vi_const.VI_ATTR_TCPIP_KEEPALIVE, True)  # type: ignore
        except visa.errors.VisaIOError:
            pass

        print(f"Connected to: {self.get_idn()}")

    def connect(self):
        self._rm = visa.ResourceManager(self.visa_library)
        self._resource = cast(
            visa.resources.MessageBasedResource,
            self._rm.open_resource(str(self.resource_str), **self._pyvisa_kwargs),
        )
        try:
            self._resource.set_visa_attribute(vi_const.VI_ATTR_TCPIP_KEEPALIVE, True)  # type: ignore
        except visa.errors.VisaIOError:
            pass

    def reconnect(self):
        try:
            self._resource.close()
        except Exception:
            pass
        time.sleep(1)
        self.connect()

    @auto_reconnect
    def write(self, command: str) -> None:
        super().write(command)

    @auto_reconnect
    def query(self, command: str) -> str:
        return super().query(command)

    @auto_reconnect
    def read(self) -> str:
        return self._resource.read()

    # =============================================================================
    # Abort Command
    # =============================================================================
    def abort(self):
        """
        Description: Forces the trigger system to the idle state. Any sweep in
        progress is aborted as soon as possible

        Parameters: None
        """
        return self.write(":ABORt")

    # =============================================================================
    # Ask Instrument about Stats and Parameters
    # =============================================================================
    def get_output_protection(self) -> str:
        """
        Requests the currently programmed state of the MG369xC RF output during
        frequency changes in CW or step sweep mode.
        """
        return self.query(":OUTPut:PROTection?")

    def get_output_retrace(self) -> str:
        """
        Requests the currently programmed state of the MG369xC RF output during
        sweep retrace.
        """

        return self.query(":OUTPut:PROTection:RETRace?")

    def get_output_impedance(self) -> float:
        """
        Queries the MG369xC RF output impedance. The impedance is
        nominally 50 ohms and is not settable.
        """

        return float(self.query(":OUTPut:IMPedance?"))

    def get_output_power_level(self) -> float:
        """
        Requests the value currently programmed for the RF output power level.
        """

        return float(self.query(":SOURce:POWer:LEVel:IMMediate:AMPLitude?") or 0.0)

    def get_maximal_power_level(self) -> float:
        """
        Requests the maximum RF output power level value that can be programmed for the
        particular MG369xC model.
        """

        return float(self.query(":SOURce:POWer? MAX"))

    # =============================================================================
    # Ask Source Amplitude Modulation
    # =============================================================================
    def get_am_logsens(self) -> float:
        """
        Requests the currently programmed AM sensitivity value for the external AM Log mode.
        """

        return float(self.query(":SOURce:AM:LOGSens?"))

    def get_am_logdepth(self) -> float:
        """
        Requests the currently programmed modulation depth value for the internal
        AM Log mode.
        """

        return float(self.query(":SOURce:AM:LOGDepth?"))

    def get_am_internal_wave(self) -> str:
        """
        Requests the currently selected modulating waveform for the internal AM function.
        """

        return self.query(":SOURce:AM:INTernal:WAVE?")

    def get_am_internal_freq(self) -> float:
        """Requests the currently programmed modulating waveform frequency value for the
        internal AM function.
        """

        return float(self.query(":SOURce:AM:INTernal:FREQuency?"))

    def get_am_state(self) -> str:
        """Requests currently programmed amplitude modulation state (on/off)"""

        return self.query(":SOURce:AM:STATe?")

    def get_am_type(self) -> str:
        """Requests the currently programmed AM operating mode."""

        return self.query(":SOURce:AM:TYPE?")

    # =============================================================================
    # Frequency Modulation
    # =============================================================================
    def get_fm_internal_wave(self) -> str:
        """
        Requests the currently selected modulating waveform for the internal FM function.
        """

        return self.query(":SOURce:FM:INTernal:WAVE?")

    def get_fm_internal_freq(self) -> float:
        """
        Requests the currently programmed modulating waveform frequency value for the
        internal FM function.
        """
        return float(self.query(":SOURce:FM:INTernal:FREQuency?"))

    def get_fm_mode(self) -> str:
        """
        Requests the currently programmed synthesis mode used to generate the FM signal.
        """

        return self.query(":SOURce:FM:MODE?")

    def get_fm_bwidth(self) -> str:
        """
        Requests the currently programmed Unlocked FM synthesis mode of operation
        (narrow or wide).
        """

        return self.query(":SOURce:FM:BWIDth?")

    def get_fm_state(self) -> str:
        """
        Requests the currently programmed frequency modulation state (on/off).
        """

        return self.query(":SOURce:FM:STATe?")

    # =============================================================================
    # Frequency Commands
    # =============================================================================
    def get_freq_cw(self) -> float:
        """
        Requests the current value of the frequency parameter.
        """

        return float(self.query(":SOURce:FREQuency:CW?") or 0.0)

    def get_freq_step(self) -> float:
        """
        Requests the current step increment value of the frequency parameter.
        """

        return float(self.query(":SOURce:FREQuency:CW:STEP:INCRement?") or 0.0)

    def get_freq_center_freq(self) -> float:
        """
        Requests the current value of the RF output center frequency.
        """

        return float(self.query(":SOURce:FREQuency:CENTer?") or 0.0)

    def get_freq_mode(self) -> str:
        """
        Requests the currently selected programming mode for frequency control.
        """

        return self.query(":SOURce:FREQuency:MODE?")

    def get_freq_span(self) -> float:
        """
        Requests the current value for SWEep[1] sweep span.
        """

        return float(self.query(":SOURce:FREQuencySPAN:?") or 0.0)

    def get_freq_start(self) -> float:
        """
        Requests the current value for SWEep[1] start frequency.
        """

        return float(self.query(":SOURce:FREQuency:STARt?") or 0.0)

    def get_freq_stop(self) -> float:
        """
        Requests the current value for SWEep[1] stop frequency.
        """

        return float(self.query(":SOURce:FREQuency:STOP?") or 0.0)

    def get_freq_unit(self) -> str:
        """
        Requests the currently selected frequency unit.
        """
        return self.query("UNIT:FREQuency?")

    # =============================================================================
    # Pulse Modulation
    # =============================================================================
    def get_pm_bwidth(self) -> str:
        """
        Requests the currently programmed phase modulation operating mode.
        """

        return self.query(":SOURce:PM:BWIDth?")

    def get_pm_internal_wave(self) -> str:
        """
        Requests the currently selected modulating waveform for the internal phase
        modulation function.
        """

        return self.query(":SOURce:PM:INTernal:WAVE?")

    def get_pm_internal_freq(self) -> float:
        """
        Requests the currently programmed modulating waveform frequency value for the
        internal phase modulation function.
        """

        return float(self.query(":SOURce:PM:INTernal:FREQuency?") or 0.0)

    def get_pm_state(self) -> str:
        """
        Requests the currently programmed phase modulation state (on/off).
        """

        return self.query(":SOURce:PM:STATe?")

    # =============================================================================
    # Set Output
    # =============================================================================
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
        self.write(f":OUTPut:STATe {state}")

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

    def set_output_protection(self, state):
        """


        Parameters
        ----------
        state : str/int
               Description: ON causes the MG369xC RF output to be turned off (blanked)
               during frequency changes in CW or step sweep mode.
               OFF leaves RF output turned on (un blanked).
               Parameters: ON | OFF | 1 | 0
               Default: ON

        Raises
        ------
        ValueError
            Error message
        """

        if state in ["ON", "OFF", 1, 0]:
            self.write(":OUTPut:PROTection " + str(state))
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_output_retrace(self, state):
        """


        Parameters
        ----------
        state :  str/int
                Description: ON causes the MG369xC RF output to be turned off during
                sweep retrace.
                OFF leaves RF output turned on
                Parameters: ON | OFF | 1 | 0
                Default: OFF

        Raises
        ------
        ValueError
            Error message
        """

        if state in ["ON", "OFF", 1, 0]:
            self.write(":OUTPut:PROTection:RETRace " + str(state))
        else:
            raise ValueError("Unknown input! See function description for more info.")

    # =============================================================================
    # SOURce:POWer subsystem
    # =============================================================================

    def set_rf_power(self, value):
        """Sets the Signal Generator Output Power in dBm.

        Parameters
        ----------
        value : float/int
            Output Power in dBm
        """
        min_val = -20.0
        max_val = 30.0
        if value > max_val or value < min_val:
            raise ValueError(
                f"Power out of range! You can set power between {min_val} and {max_val} dBm!"
            )

        self.write(f":SOURce:POWer:LEVel:IMMediate:AMPLitude {str(value)} dBm")

    def set_output_power_level(self, value: int | float) -> None:
        """Sets the Signal Generator Output Power in dBm. Alias for set_rf_power().

        Parameters
        ----------
        value : int/float
            Output Power in dBm
        """
        self.set_rf_power(value)

    # =============================================================================
    # Set Control system commands:
    #            Amplitude Modulation
    #            Correction Commands
    #            Frequency Modulation
    #            Frequency Commands
    #            Pulse Modulation
    #
    # =============================================================================
    # =============================================================================
    #   Source - AM
    # =============================================================================
    def set_am_logsens(self, value):
        """


        Parameters
        ----------
        value : int/float
                Description: Sets the AM sensitivity for the external AM Log mode.
                Parameters: Sensitivity (in dB/V)
                Range: 0 to 25 dB/V
                Default: 3 dB/V

        Raises
        ------
        ValueError
            Error message
        """

        if int(value) in np.arange(0, 26, 1):
            self.write(":SOURce:AM:LOGSens " + str(value) + " dB/V")
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_am_logdepth(self, value):
        """


        Parameters
        ----------
        value : int/float
                Description: Sets the modulation depth of the AM signal in the internal AM Log mode.
                Parameters: Modulation depth (in dB)
                Range: 0 to 25 dB
                Default: 3 dB

        Raises
        ------
        ValueError
             Error message
        """

        if int(value) in np.arange(0, 26, 1):
            self.write(":SOURce:AM:LOGDepth " + str(value) + " dB")
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_am_internal_wave(self, state):
        """


        Parameters
        ----------
        state : str
                Description: Selects the modulating waveform (from the internal AM generator)
                for the internal AM function, as follows:
                SINE = Sine wave
                GAUSsian = Gaussian noise
                RDOWn = Negative ramp
                RUP = Positive ramp
                SQUare = Square wave
                TRIangle = Triangle wave
                UNIForm = Uniform noiseParameters

        Raises
        ------
        ValueError
            Error message
        """

        valid_list = ["SINE", "GAUSsian", "RDOWn", "RUP", "SQUare", "TRIangle", "UNIForm"]
        valid_state = self._check_scpi_param(state, valid_list)
        self.write(":SOURce:AM:INTernal:WAVE " + valid_state)

    def set_am_internal_freq(self, value, unit):
        """


        Parameters
        ----------
        value : str
            Description: Sets the frequency of the modulating waveform for the internal AM function
            (see :AM:INTernal:WAVE).
            Parameters: Frequency
        unit : int/float
            Range: 0.1 Hz to 1 MHz for sine wave
            0.1 Hz to 100 kHz for square, triangle, and ramp waveforms
            Default: 1 kHz

         Raises
        ------
        ValueError
            Error message
        """

        state = self.get_am_internal_freq()
        unit_list = ["Hz", "kHz", "MHz"]
        if state == "SINE":
            if value >= 0.1 or value <= 1 and unit in unit_list:
                self.write(":SOURce:AM:INTernal:FREQuency " + str(value) + " " + unit)
            else:
                raise ValueError("Unknown input! See function description for more info.")

        else:
            if value >= 0.1 or value <= 100 and unit in unit_list[:-1]:
                self.write(":SOURce:AM:INTernal:FREQuency " + str(value) + " " + unit)
            else:
                raise ValueError("Unknown input! See function description for more info.")

    def set_am_state(self, state):
        """


        Parameters
        ----------
        state : str/int
                Description: Enable/disable amplitude modulation of MG369xC RF output signal.
                Parameters: ON | OFF | 1 | 0
                Default: OFF

        Raises
        ------
        ValueError
            Error message
        """

        if state in ["ON", "OFF", 1, 0]:
            self.write(":SOURce:AM:STATe " + str(state))
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_am_type(self, state):
        """


        Parameters
        ----------
        state : str
                Description: Selects the AM operating mode.
                Parameters: LINear | LOGarithmic
                Default: LINear

        Raises
        ------
        ValueError
            Error message
        """

        valid_state = self._check_scpi_param(state, ["LINear", "LOGarithmic"])
        self.write(":SOURce:AM:TYPE " + valid_state)

    # =============================================================================
    #     Correction Commands
    # =============================================================================
    def set_correction_commands(self, state):
        """
        Description: Turns the selected user level flatness correction power-offset table on/off.

        Parameters
        ----------
        state : str/int
                Parameters: ON | OFF | 1 | 0
                Default: OFF

        Raises
        ------
        ValueError
            Error message
        """

        if state in ["ON", "OFF", 1, 0]:
            self.write(":SOURce:CORRection:STATe " + str(state))
        else:
            raise ValueError("Unknown input! See function description for more info.")

    # =============================================================================
    # Frequency Modulation
    # =============================================================================
    def set_fm_internal_wave(self, state):
        """

        Parameters
        ----------
        state : str
                Description: Selects the modulating waveform (from the internal FM generator)
                for the internal FM function, as follows:
                SINE = Sine wave
                GAUSsian = Gaussian noise
                RDOWn = Negative ramp
                RUP =Positive ramp
                SQUare = Square wave
                TRIangle = Triangle wave
                UNIForm = Uniform noise
                Parameters: SINE | GAUSsian | RDOWn | RUP | SQUare | TRIangle | UNIForm
                Default: SINE

        Raises
        ------
        ValueError
            Error message
        """

        valid_list = ["SINE", "GAUSsian", "RDOWn", "RUP", "SQUare", "TRIangle", "UNIForm"]
        valid_state = self._check_scpi_param(state, valid_list)
        self.write(":SOURce:FM:INTernal:WAVE " + valid_state)

    def set_fm_internal_freq(self, value, unit):
        """


        Parameters
        ----------
        value : int/float
            Range: 0.1 Hz to 1 MHz for sine wave
        unit : str
            Parameters: Frequency
            Description: Sets the frequency of the modulating waveform for the internal FM function
            (see :FM:INTernal:WAVE).
            Default: 1 kHz

        Raises
        ------
        ValueError
            Error message
        """

        state = self.get_fm_internal_freq()
        unit_list = ["Hz", "kHz", "MHz"]
        if state == "SINE":
            if value >= 0.1 or value <= 1 and unit in unit_list:
                self.write(":SOURce:FM:INTernal:FREQuency " + str(value) + " " + unit)
            else:
                raise ValueError("Unknown input! See function description for more info.")

        else:
            if value >= 0.1 or value <= 100 and unit in unit_list[:-1]:
                self.write(":SOURce:FM:INTernal:FREQuency " + str(value) + " " + unit)
            else:
                raise ValueError("Unknown input! See function description for more info.")

    def set_fm_mode(self, state):
        """


        Parameters
        ----------
        state : str
                Sets the synthesis mode employed in generating the FM signal, as follows:
                LOCKed[1] = Locked Narrow FM
                LOCKed2 = Locked Narrow Low-Noise FM
                UNLocked = Unlocked FM
                If LOCKed[1] or LOCKed2 is set, the YIG phase-locked loop is used in synthesizing
                the FM signal. If UNLocked is set, the YIG phase-lock loop is disabled and the FM
                signal is obtained by applying the modulating signal to the tuning coils of the
                YIG-tuned oscillator.
                Parameters: LOCKed[1] | LOCKed2 | UNLocked
                Default: UNLocked

        Raises
        ------
        ValueError
            Error message
        """

        valid_state = self._check_scpi_param(state, ["LOCKed[1]", "LOCKed2", "UNLocked"])
        self.write(":SOURce:FM:MODE " + valid_state)

    def set_fm_bwidth(self, state):
        """


        Parameters
        ----------
        state : str
            Description: Sets the Unlocked FM synthesis mode to wide or narrow mode of operation.
            The Unlocked Wide FM synthesis mode allows maximum deviations of ±100 MHz for
            DC to 100 Hz rates.
            The Unlocked Narrow FM synthesis mode allows maximum deviations of ±10 MHz for
            DC to 8 MHz rates.
            Parameters: MIN | MAX
            Range: MIN = narrow mode; MAX = wide mode
            Default: MIN

        Raises
        ------
        ValueError
            Error message
        """

        valid_state = self._check_scpi_param(state, ["MIN", "MAX"])
        self.write(":SOURce:FM:BWIDth " + valid_state)

    def set_fm_state(self, state):
        """


        Parameters
        ----------
        state : str/int
                Description: Enable/disable frequency modulation of MG369xC RF output signal.
                Parameters: ON | OFF | 1 | 0
                Default: OFF

        Raises
        ------
        ValueError
            Error message
        """

        if state in ["ON", "OFF", 1, 0]:
            self.write(":SOURce:FM:STATe " + str(state))
        else:
            raise ValueError("Unknown input! See function description for more info.")

    # =============================================================================
    # Frequency Commands
    # =============================================================================
    def set_freq_cw(self, value: int | float, unit: str | None = None) -> None:
        """
        Parameters
        ----------
        value : int/float
            Parameter Frequency

        unit : str (optional)
            Frequency Unit: 'GHz' or 'MHz' or 'Hz'
        """

        min_freq = 10e6  # 10 MHz
        max_freq = 40e9  # 40 GHz

        if unit == "Hz" or unit is None:
            unit = "Hz"
            if value <= max_freq and value >= min_freq:
                self.write(f":SOURce:FREQuency:CW {value} {unit}")
            else:
                raise ValueError("Minimum Frequency = 10 MHz and Maximum Frequency = 40 GHz")
        elif unit == "MHz":
            if value * 1e6 <= max_freq and value * 1e6 >= min_freq:
                self.write(f":SOURce:FREQuency:CW {value} {unit}")
            else:
                raise ValueError("Minimum Frequency = 10 MHz and Maximum Frequency = 40 GHz")
        elif unit == "GHz":
            if value * 1e9 <= max_freq and value * 1e9 >= min_freq:
                self.write(f":SOURce:FREQuency:CW {value} {unit}")
            else:
                raise ValueError("Minimum Frequency = 10 MHz and Maximum Frequency = 40 GHz")
        else:
            raise ValueError('Unknown input! Unit must be None or "MHz" or "GHz"!')

    def set_freq_step(self, value, unit):
        """


        Parameters
        ----------
        value : int/float
                 Description: Sets the step increment size used with the :FREQuency:CW command.
                 Range: 0.01 Hz to (MAX  MIN)
                 Default: 0.1 GHz
        unit : str
                Parameters: Frequency (in Hz)

        Raises
        ------
        ValueError
            Error message
        """

        unit_list = ["Hz", "kHz", "MHz", "GHz"]
        if unit in unit_list and value > 0.01:
            self.write(":SOURce:FREQuency:CW:STEP:INCRement " + str(value) + " " + unit)
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_freq_cent(self, value, unit):
        """


        Parameters
        ----------
        value :  int/float
                   Description: Sets the MG369xC RF output center frequency to the value entered.
                   :CENTER and :SPAN frequencies are coupled values. Entering the value for one
                   will cause the other to be recalculated. (See notes under :FREQuency:SPAN)
        unit : str
            Parameters: Frequency (in Hz)

        Raises
        ------
        ValueError
            Error message
        """

        unit_list = ["Hz", "kHz", "MHz", "GHz"]
        if unit in unit_list and value > 0.01:
            self.write(":SOURce:FREQuency:CENTer " + str(value) + " " + unit)
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_freq_mode(self, state):
        """


        Parameters
        ----------
        state : str
                Specifies which command subsystem controls the MG369xC frequency, as follows:
                CW|FIXed = [:SOURce]:FREQuency:CW|FIXed
                SWEep[1] = [:SOURce]:SWEep[1] (see Datasheet)
                SWCW = (see notes)
                ALSW = (see notes)
                LIST<n> = [:SOURce]:LIST<n> (see DataSheet)
                :SWEep and :SWEep1may be used interchangeably

                Parameters: CW | FIXed | SWEep[1] | SWCW | ALSW | LIST[1] | LIST2 | LIST3 | LIST4
                Default: CW

        Raises
        ------
        ValueError
            Error message
        """

        valid_list = [
            "CW",
            "FIXed",
            "SWEep[1]",
            "SWCW",
            "ALSW",
            "LIST[1]",
            "LIST2",
            "LIST3",
            "LIST4",
        ]
        valid_state = self._check_scpi_param(state, valid_list)
        self.write(":SOURce:FREQuency:MODE " + valid_state)

    def set_freq_span(self, value, unit):
        """


        Parameters
        ----------
        value : int/float
            Sets sweep span for SWEep[1] to value entered. :SPAN and :CENTer are coupled values
            Range: 1 kHz to (MAX  MIN)
            Default: MAX  MIN
        unit : str
            Parameters: Frequency (in Hz)

        Raises
        ------
        ValueError
            Error message
        """
        """
        Sets sweep span for SWEep[1] to value entered. :SPAN and :CENTer are coupled values
        Parameters: Frequency (in Hz)
        Range: 1 kHz to (MAX  MIN)
        Default: MAX  MIN
        """

        unit_list = ["Hz", "kHz", "MHz", "GHz"]
        if unit in unit_list:
            self.write(":SOURce:FREQuency:SPAN " + str(value) + " " + str(unit))
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_freq_start(self, value, unit):
        """


        Parameters
        ----------
        value : int/float
            Sets start frequency for SWEep[1] to the value entered. (MIN is defined in the notes)
            Range: MIN to MAX
            Default: MIN
        unit : str
            Parameters: Frequency (in Hz) | MIN

        Raises
        ------
        ValueError
            Error message
        """

        unit_list = ["Hz", "kHz", "MHz", "GHz"]
        if unit in unit_list:
            self.write(":SOURce:FREQuency:STARt " + str(value) + " " + str(unit))
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_freq_stop(self, value, unit):
        """


        Parameters
        ----------
        value : int/float
            Sets stop frequency for SWEep[1] to the value entered. (MAX is defined in the notes
            under [:SOURce]:FREQuency:CW|FIXed).
            Range: MIN to MAX
            Default: MAX
        unit : str
            Parameters: Frequency (in Hz) | MAX

        Raises
        ------
        ValueError
            Error message
        """

        unit_list = ["Hz", "kHz", "MHz", "GHz"]
        if unit in unit_list:
            self.write(":SOURce:FREQuency:STOP " + str(value) + " " + str(unit))
        else:
            raise ValueError("Unknown input! See function description for more info.")

    # =============================================================================
    # Pulse Modulation
    # =============================================================================
    def set_pm_bwidth(self, state):
        """


        Parameters
        ----------
        state : str
            Selects the phase modulation (ΦM) operating mode.
            The Narrow ΦM mode allows maximum deviations of ±3 radians for DC to 8 MHz rates.
            The Wide ΦM mode allows maximum deviations of ±400 radians for DC to 1 MHz rates.
            Parameters: MIN | MAX
            Range: MIN = narrow mode
            MAX = wide mode
            Default: MIN

        Raises
        ------
        ValueError
            Error message
        """

        valid_state = self._check_scpi_param(state, ["MIN", "MAX"])
        self.write(":SOURce:PM:BWIDth " + valid_state)

    def set_pm_internal_wave(self, state):
        """


        Parameters
        ----------
        state : str
                Selects the modulating waveform (from the internal ΦM generator) for the internal
                phase modulation function, as follows:
                SINE = Sine wave
                GAUSsian = Gaussian noise
                RDOWn = Negative ramp
                RUP = Positive ramp
                SQUare = Square wave
                TRIangle = Triangle wave
                UNIForm = Uniform noise
                Parameters: SINE | GAUSsian | RDOWn | RUP | SQUare | TRIangle | UNIForm
                Default: SINE

        Raises
        ------
        ValueError
             Error message
        """

        valid_list = ["SINE", "GAUSsian", "RDOWn", "RUP", "SQUare", "TRIangle", "UNIForm"]
        valid_state = self._check_scpi_param(state, valid_list)
        self.write(":SOURce:PM:INTernal:WAVE " + valid_state)

    def set_pm_internal_freq(self, value, unit):
        """


        Parameters
        ----------
        value : str
            Parameter: Frequency (in Hz)
        unit : int/float
            Description: Sets the frequency of the modulating waveform for the internal
            phase modulation (see :PM:INTernal:WAVE)
            Range: 0.1 Hz to 1 MHz for sine wave;
            0.1 Hz to 100 kHz for square, triangle, and ramp waveforms.
            Default: 1 kHz

        Raises
        ------
        ValueError
             Error message
        """

        state = self.get_pm_internal_freq()
        unit_list = ["Hz", "kHz", "MHz"]
        if state == "SINE":
            if value >= 0.1 or value <= 1 and unit in unit_list:
                self.write(":SOURce:PM:INTernal:FREQuency " + str(value) + " " + unit)
            else:
                raise ValueError("Unknown input! See function description for more info.")

        else:
            if value >= 0.1 or value <= 100 and unit in unit_list[:-1]:
                self.write(":SOURce:PM:INTernal:FREQuency " + str(value) + " " + unit)
            else:
                raise ValueError("Unknown input! See function description for more info.")

    def set_pm_state(self, state):
        """


        Parameters
        ----------
        state : str/int
            Description: Enable/disable phase modulation of the MG369xC RF output signal.
            Parameters: ON | OFF | 1 | 0
            Default: OFF

        Raises
        ------
        ValueError
            v
        """

        if state in ["ON", "OFF", 1, 0]:
            self.write(":SOURce:PM:STATe " + str(state))
        else:
            raise ValueError("Unknown input! See function description for more info.")

    # =============================================================================
    # Get/Save Data
    # =============================================================================
    def get_data(self):
        """
        Return a dictionary with the measured Power and CW Frequency.
        """
        output = {}
        freq = self.get_freq_cw()
        power = self.get_output_power_level()
        output["Power/dBm"] = power
        output["CW Frequency/" + str(self.get_freq_unit())] = freq
        return output

    # =============================================================================
    # Aliases for backward compatibility
    # =============================================================================
    @deprecated("Use 'get_idn' instead")
    def getIdn(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for get_idn()"""
        self.logger.warning("Method 'getIdn()' is deprecated. Please use 'get_idn()' instead.")
        return self.get_idn(*args, **kwargs)

    @deprecated("Use 'close' instead")
    def Close(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for close()"""
        self.logger.warning("Method 'Close()' is deprecated. Please use 'close()' instead.")
        return self.close(*args, **kwargs)

    @deprecated("Use 'reset' instead")
    def reset(self, *args, **kwargs):
        """Deprecated alias for reset()"""
        self.logger.warning("Method 'reset()' is deprecated. Please use 'reset()' instead.")
        return self.reset(*args, **kwargs)

    @deprecated("Use 'get_output_protection' instead")
    def ask_output_protection(self, *args, **kwargs):
        """Deprecated alias for get_output_protection()"""
        self.logger.warning(
            """Method 'ask_output_protection()' is deprecated. 
            Please use 'get_output_protection()' instead."""
        )
        return self.get_output_protection(*args, **kwargs)

    @deprecated("Use 'get_output_retrace' instead")
    def ask_output_retrace(self, *args, **kwargs):
        """Deprecated alias for get_output_retrace()"""
        self.logger.warning(
            """Method 'ask_output_retrace()' is deprecated. 
            Please use 'get_output_retrace()' instead."""
        )
        return self.get_output_retrace(*args, **kwargs)

    @deprecated("Use 'get_output_impedance' instead")
    def ask_output_impedance(self, *args, **kwargs):
        """Deprecated alias for get_output_impedance()"""
        self.logger.warning(
            """Method 'ask_output_impedance()' is deprecated. 
            Please use 'get_output_impedance()' instead."""
        )
        return self.get_output_impedance(*args, **kwargs)

    @deprecated("Use 'get_output_power_level' instead")
    def ask_OutputPowerLevel(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for get_output_power_level()"""
        self.logger.warning(
            """Method 'ask_OutputPowerLevel()' is deprecated. 
            Please use 'get_output_power_level()' instead."""
        )
        return self.get_output_power_level(*args, **kwargs)

    @deprecated("Use 'get_maximal_power_level' instead")
    def ask_MaximalPowerLevel(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for get_maximal_power_level()"""
        self.logger.warning(
            """Method 'ask_MaximalPowerLevel()' is deprecated. 
            Please use 'get_maximal_power_level()' instead."""
        )
        return self.get_maximal_power_level(*args, **kwargs)

    @deprecated("Use 'get_am_logsens' instead")
    def ask_am_logsens(self, *args, **kwargs):
        """Deprecated alias for get_am_logsens()"""
        self.logger.warning(
            "Method 'ask_am_logsens()' is deprecated. Please use 'get_am_logsens()' instead."
        )
        return self.get_am_logsens(*args, **kwargs)

    @deprecated("Use 'get_am_logdepth' instead")
    def ask_am_logDepth(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for get_am_logdepth()"""
        self.logger.warning(
            "Method 'ask_am_logDepth()' is deprecated. Please use 'get_am_logdepth()' instead."
        )
        return self.get_am_logdepth(*args, **kwargs)

    @deprecated("Use 'get_am_internal_wave' instead")
    def ask_am_internalWave(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for get_am_internal_wave()"""
        self.logger.warning(
            """Method 'ask_am_internalWave()' is deprecated. 
            Please use 'get_am_internal_wave()' instead."""
        )
        return self.get_am_internal_wave(*args, **kwargs)

    @deprecated("Use 'get_am_internal_freq' instead")
    def ask_am_internalFreq(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for get_am_internal_freq()"""
        self.logger.warning(
            """Method 'ask_am_internalFreq()' is deprecated. 
            Please use 'get_am_internal_freq()' instead."""
        )
        return self.get_am_internal_freq(*args, **kwargs)

    @deprecated("Use 'get_am_state' instead")
    def ask_am_state(self, *args, **kwargs):
        """Deprecated alias for get_am_state()"""
        self.logger.warning(
            "Method 'ask_am_state()' is deprecated. Please use 'get_am_state()' instead."
        )
        return self.get_am_state(*args, **kwargs)

    @deprecated("Use 'get_am_type' instead")
    def ask_am_type(self, *args, **kwargs):
        """Deprecated alias for get_am_type()"""
        self.logger.warning(
            "Method 'ask_am_type()' is deprecated. Please use 'get_am_type()' instead."
        )
        return self.get_am_type(*args, **kwargs)

    @deprecated("Use 'get_fm_internal_wave' instead")
    def ask_fm_internalWave(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for get_fm_internal_wave()"""
        self.logger.warning(
            """Method 'ask_fm_internalWave()' is deprecated. 
            Please use 'get_fm_internal_wave()' instead."""
        )
        return self.get_fm_internal_wave(*args, **kwargs)

    @deprecated("Use 'get_fm_internal_freq' instead")
    def ask_fm_internalFreq(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for get_fm_internal_freq()"""
        self.logger.warning(
            """Method 'ask_fm_internalFreq()' is deprecated. 
            Please use 'get_fm_internal_freq()' instead."""
        )
        return self.get_fm_internal_freq(*args, **kwargs)

    @deprecated("Use 'get_fm_mode' instead")
    def ask_fm_mode(self, *args, **kwargs):
        """Deprecated alias for get_fm_mode()"""
        self.logger.warning(
            "Method 'ask_fm_mode()' is deprecated. Please use 'get_fm_mode()' instead."
        )
        return self.get_fm_mode(*args, **kwargs)

    @deprecated("Use 'get_fm_bwidth' instead")
    def ask_fm_Bwidth(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for get_fm_bwidth()"""
        self.logger.warning(
            "Method 'ask_fm_Bwidth()' is deprecated. Please use 'get_fm_bwidth()' instead."
        )
        return self.get_fm_bwidth(*args, **kwargs)

    @deprecated("Use 'get_fm_state' instead")
    def ask_fm_state(self, *args, **kwargs):
        """Deprecated alias for get_fm_state()"""
        self.logger.warning(
            "Method 'ask_fm_state()' is deprecated. Please use 'get_fm_state()' instead."
        )
        return self.get_fm_state(*args, **kwargs)

    @deprecated("Use 'get_freq_cw' instead")
    def ask_freq_CW(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for get_freq_cw()"""
        self.logger.warning(
            "Method 'ask_freq_CW()' is deprecated. Please use 'get_freq_cw()' instead."
        )
        return self.get_freq_cw(*args, **kwargs)

    @deprecated("Use 'get_freq_step' instead")
    def ask_freq_step(self, *args, **kwargs):
        """Deprecated alias for get_freq_step()"""
        self.logger.warning(
            "Method 'ask_freq_step()' is deprecated. Please use 'get_freq_step()' instead."
        )
        return self.get_freq_step(*args, **kwargs)

    @deprecated("Use 'get_freq_center_freq' instead")
    def ask_freq_centerFreq(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for get_freq_center_freq()"""
        self.logger.warning(
            """Method 'ask_freq_centerFreq()' is deprecated. 
            Please use 'get_freq_center_freq()' instead."""
        )
        return self.get_freq_center_freq(*args, **kwargs)

    @deprecated("Use 'get_freq_mode' instead")
    def ask_freq_mode(self, *args, **kwargs):
        """Deprecated alias for get_freq_mode()"""
        self.logger.warning(
            "Method 'ask_freq_mode()' is deprecated. Please use 'get_freq_mode()' instead."
        )
        return self.get_freq_mode(*args, **kwargs)

    @deprecated("Use 'get_freq_span' instead")
    def ask_freq_span(self, *args, **kwargs):
        """Deprecated alias for get_freq_span()"""
        self.logger.warning(
            "Method 'ask_freq_span()' is deprecated. Please use 'get_freq_span()' instead."
        )
        return self.get_freq_span(*args, **kwargs)

    @deprecated("Use 'get_freq_start' instead")
    def ask_freq_start(self, *args, **kwargs):
        """Deprecated alias for get_freq_start()"""
        self.logger.warning(
            "Method 'ask_freq_start()' is deprecated. Please use 'get_freq_start()' instead."
        )
        return self.get_freq_start(*args, **kwargs)

    @deprecated("Use 'get_freq_stop' instead")
    def ask_freq_stop(self, *args, **kwargs):
        """Deprecated alias for get_freq_stop()"""
        self.logger.warning(
            "Method 'ask_freq_stop()' is deprecated. Please use 'get_freq_stop()' instead."
        )
        return self.get_freq_stop(*args, **kwargs)

    @deprecated("Use 'get_freq_unit' instead")
    def ask_freq_unit(self, *args, **kwargs):
        """Deprecated alias for get_freq_unit()"""
        self.logger.warning(
            "Method 'ask_freq_unit()' is deprecated. Please use 'get_freq_unit()' instead."
        )
        return self.get_freq_unit(*args, **kwargs)

    @deprecated("Use 'get_pm_bwidth' instead")
    def ask_pm_Bwidth(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for get_pm_bwidth()"""
        self.logger.warning(
            "Method 'ask_pm_Bwidth()' is deprecated. Please use 'get_pm_bwidth()' instead."
        )
        return self.get_pm_bwidth(*args, **kwargs)

    @deprecated("Use 'get_pm_internal_wave' instead")
    def ask_pm_internalWave(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for get_pm_internal_wave()"""
        self.logger.warning(
            """Method 'ask_pm_internalWave()' is deprecated. 
            Please use 'get_pm_internal_wave()' instead."""
        )
        return self.get_pm_internal_wave(*args, **kwargs)

    @deprecated("Use 'get_pm_internal_freq' instead")
    def ask_pm_internalFreq(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for get_pm_internal_freq()"""
        self.logger.warning(
            """Method 'ask_pm_internalFreq()' is deprecated. 
            Please use 'get_pm_internal_freq()' instead."""
        )
        return self.get_pm_internal_freq(*args, **kwargs)

    @deprecated("Use 'get_pm_state' instead")
    def ask_pm_state(self, *args, **kwargs):
        """Deprecated alias for get_pm_state()"""
        self.logger.warning(
            "Method 'ask_pm_state()' is deprecated. Please use 'get_pm_state()' instead."
        )
        return self.get_pm_state(*args, **kwargs)

    @deprecated("Use 'set_output_power_level' instead")
    def set_OutputPowerLevel(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for set_output_power_level()"""
        self.logger.warning(
            """Method 'set_OutputPowerLevel()' is deprecated. 
            Please use 'set_output_power_level()' instead."""
        )
        return self.set_output_power_level(*args, **kwargs)

    @deprecated("Use 'set_am_logdepth' instead")
    def set_am_logDepth(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for set_am_logdepth()"""
        self.logger.warning(
            "Method 'set_am_logDepth()' is deprecated. Please use 'set_am_logdepth()' instead."
        )
        return self.set_am_logdepth(*args, **kwargs)

    @deprecated("Use 'set_am_internal_wave' instead")
    def set_am_internalWave(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for set_am_internal_wave()"""
        self.logger.warning(
            """Method 'set_am_internalWave()' is deprecated. 
            Please use 'set_am_internal_wave()' instead."""
        )
        return self.set_am_internal_wave(*args, **kwargs)

    @deprecated("Use 'set_am_internal_freq' instead")
    def set_am_internalFreq(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for set_am_internal_freq()"""
        self.logger.warning(
            """Method 'set_am_internalFreq()' is deprecated. 
            Please use 'set_am_internal_freq()' instead."""
        )
        return self.set_am_internal_freq(*args, **kwargs)

    @deprecated("Use 'set_correction_commands' instead")
    def set_correctionCommands(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for set_correction_commands()"""
        self.logger.warning(
            """Method 'set_correctionCommands()' is deprecated. 
            Please use 'set_correction_commands()' instead."""
        )
        return self.set_correction_commands(*args, **kwargs)

    @deprecated("Use 'set_fm_internal_wave' instead")
    def set_fm_internalWave(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for set_fm_internal_wave()"""
        self.logger.warning(
            """Method 'set_fm_internalWave()' is deprecated. 
            Please use 'set_fm_internal_wave()' instead."""
        )
        return self.set_fm_internal_wave(*args, **kwargs)

    @deprecated("Use 'set_fm_internal_freq' instead")
    def set_fm_internalFreq(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for set_fm_internal_freq()"""
        self.logger.warning(
            """Method 'set_fm_internalFreq()' is deprecated. 
            Please use 'set_fm_internal_freq()' instead."""
        )
        return self.set_fm_internal_freq(*args, **kwargs)

    @deprecated("Use 'set_fm_bwidth' instead")
    def set_fm_Bwidth(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for set_fm_bwidth()"""
        self.logger.warning(
            "Method 'set_fm_Bwidth()' is deprecated. Please use 'set_fm_bwidth()' instead."
        )
        return self.set_fm_bwidth(*args, **kwargs)

    @deprecated("Use 'set_fm_state' instead")
    def set_fm_steta(self, *args, **kwargs):
        """Deprecated alias for set_fm_state()"""
        self.logger.warning(
            "Method 'set_fm_steta()' is deprecated. Please use 'set_fm_state()' instead."
        )
        return self.set_fm_state(*args, **kwargs)

    @deprecated("Use 'set_freq_cw' instead")
    def set_freq_CW(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for set_freq_cw()"""
        self.logger.warning(
            "Method 'set_freq_CW()' is deprecated. Please use 'set_freq_cw()' instead."
        )
        return self.set_freq_cw(*args, **kwargs)

    @deprecated("Use 'set_pm_bwidth' instead")
    def set_pm_Bwidth(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for set_pm_bwidth()"""
        self.logger.warning(
            "Method 'set_pm_Bwidth()' is deprecated. Please use 'set_pm_bwidth()' instead."
        )
        return self.set_pm_bwidth(*args, **kwargs)

    @deprecated("Use 'set_pm_internal_wave' instead")
    def set_pm_internalWave(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for set_pm_internal_wave()"""
        self.logger.warning(
            """Method 'set_pm_internalWave()' is deprecated. 
            Please use 'set_pm_internal_wave()' instead."""
        )
        return self.set_pm_internal_wave(*args, **kwargs)

    @deprecated("Use 'set_pm_internal_freq' instead")
    def set_pm_internalFreq(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for set_pm_internal_freq()"""
        self.logger.warning(
            """Method 'set_pm_internalFreq()' is deprecated. 
            Please use 'set_pm_internal_freq()' instead."""
        )
        return self.set_pm_internal_freq(*args, **kwargs)

    @deprecated("Use 'get_data' instead")
    def get_Data(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for get_data()"""
        self.logger.warning("Method 'get_Data()' is deprecated. Please use 'get_data()' instead.")
        return self.get_data(*args, **kwargs)
