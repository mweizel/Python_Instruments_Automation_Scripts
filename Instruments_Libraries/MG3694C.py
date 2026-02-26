#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
    7) After your measurement dont forget to change the IP back to 'automatic'!
"""

import numpy as np
import pyvisa as visa
import pyvisa.constants as vi_const
import functools
import time

from typing import Callable, Any

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
                
                print(f"Connection lost during {getattr(func, '__name__', 'function')}. Reconnecting (Attempt {i+1}/{attempts})...")
                try:
                    self.reconnect()
                except Exception as reconnect_err:
                    print(f"Reconnect failed: {reconnect_err}")
                    time.sleep(1) # Wait a bit before next loop
    return wrapper

from typing import Union, Dict, cast
from .BaseInstrument import BaseInstrument

class MG3694C(BaseInstrument):
    """
    This class uses pyvisa to connect to an Anritsu MG3694C Signal Generator.
    """

    def __init__(
        self,
        resource_str: str = "192.168.0.254",
        visa_library: str = "@ivi",
        **kwargs
    ):
        kwargs.setdefault('read_termination', '\n')
        kwargs.setdefault('query_delay', 0.5)
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
        self._resource = cast(visa.resources.MessageBasedResource, self._rm.open_resource(
            str(self.resource_str), 
            **self._pyvisa_kwargs
        ))
        try:
            self._resource.set_visa_attribute(vi_const.VI_ATTR_TCPIP_KEEPALIVE, True)  # type: ignore
        except visa.errors.VisaIOError:
            pass

    def reconnect(self):
        try:
            self._resource.close()
        except:
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
    def get_output_protection(self):
        """

        Returns
        -------
        TYPE Query str
            Requests the currently programmed state of the MG369xC RF output during
            frequency changes in CW or step sweep mode.

        """
        return self.query(":OUTPut:PROTection?")

    def get_output_retrace(self):
        """


        Returns
        -------
        TYPE Query str
            Requests the currently programmed state of the MG369xC RF output during
            sweep retrace


        """

        return self.query(":OUTPut:PROTection:RETRace?")

    def get_output_impedance(self):
        """


        Returns
        -------
        TYPE Query str
            Description: Queries the MG369xC RF output impedance. The impedance is
            nominally 50 ohms and is not settable.

        """

        return self.query(":OUTPut:IMPedance?")

    def get_output_power_level(self):
        """


        Returns
        -------
        TYPE Query str
            Requests the value currently programmed for the RF output power level

        """

        return float(self.query(":SOURce:POWer:LEVel:IMMediate:AMPLitude?") or 0.0)

    def get_maximal_power_level(self):
        """


        Returns
        -------
        TYPE Query str
            Requests the maximum RF output power level value that can be programmed for the
            particular MG369xC model

        """

        return self.query(":SOURce:POWer? MAX")

    # =============================================================================
    # Ask Source Amplitude Modulation
    # =============================================================================
    def get_am_logsens(self):
        """


        Returns
        -------
        TYPE Query
            Requests the currently programmed AM sensitivity value for the external AM Log mode.

        """

        return self.query(":SOURce:AM:LOGSens?")

    def get_am_logdepth(self):
        """


        Returns
        -------
        TYPE Query str
            Requests the currently programmed modulation depth value for the internal
            AM Log mode.

        """

        return self.query(":SOURce:AM:LOGDepth?")

    def get_am_internal_wave(self):
        """


        Returns
        -------
        TYPE Query str
            Requests the currently selected modulating waveform for the internal AM function.

        """

        return self.query(":SOURce:AM:INTernal:WAVE?")

    def get_am_internal_freq(self):
        """


        Returns
        -------
        TYPE Query str
            Requests the currently programmed modulating waveform frequency value for the
            internal AM function.

        """

        return self.query(":SOURce:AM:INTernal:FREQuency?")

    def get_am_state(self):
        """


        Returns
        -------
        TYPE Query str
           Requests currently programmed amplitude modulation state (on/off)

        """

        return self.query(":SOURce:AM:STATe?")

    def get_am_type(self):
        """


        Returns
        -------
        TYPE Query str
            Requests the currently programmed AM operating mode.

        """

        return self.query(":SOURce:AM:TYPE?")

    # =============================================================================
    # Frequency Modulation
    # =============================================================================
    def get_fm_internal_wave(self):
        """


        Returns
        -------
        TYPE Query str
            Requests the currently selected modulating waveform for the internal FM function.

        """

        return self.query(":SOURce:FM:INTernal:WAVE?")

    def get_fm_internal_freq(self):
        """


        Returns
        -------
        TYPE Query str
            Requests the currently programmed modulating waveform frequency value for the
            internal FM function.

        """
        return self.query(":SOURce:FM:INTernal:FREQuency?")

    def get_fm_mode(self):
        """


        Returns
        -------
        TYPE Query str
             Requests the currently programmed synthesis mode used to generate the FM signal.

        """

        return self.query(":SOURce:FM:MODE?")

    def get_fm_bwidth(self):
        """


        Returns
        -------
        TYPE Query str
            Requests the currently programmed Unlocked FM synthesis mode of operation
            (narrow or wide)

        """

        return self.query(":SOURce:FM:BWIDth?")

    def get_fm_state(self):
        """


        Returns
        -------
        TYPE Query str
            Requests the currently programmed frequency modulation state (on/off).

        """

        return self.query(":SOURce:FM:STATe?")

    # =============================================================================
    # Frequency Commands
    # =============================================================================
    def get_freq_cw(self):
        """


        Returns
        -------
        TYPE Query str
            Requests the current value of the frequency parameter.

        """

        return float(self.query(":SOURce:FREQuency:CW?") or 0.0)

    def get_freq_step(self):
        """


        Returns
        -------
        TYPE Query str
            Requests the current step increment value of the frequency parameter.

        """

        return self.query(":SOURce:FREQuency:CW:STEP:INCRement?")

    def get_freq_center_freq(self):
        """


        Returns
        -------
        TYPE Query str
            Requests the current value of the RF output center frequency.

        """

        return self.query(":SOURce:FREQuency:CENTer?")

    def get_freq_mode(self):
        """


        Returns
        -------
        TYPE Query str
            Requests the currently selected programming mode for frequency control.

        """

        return self.query(":SOURce:FREQuency:MODE?")

    def get_freq_span(self):
        """


        Returns
        -------
        TYPE Query str
            Requests the current value for SWEep[1] sweep span

        """

        return self.query(":SOURce:FREQuencySPAN:?")

    def get_freq_start(self):
        """


        Returns
        -------
        TYPE Query str
            Requests the current value for SWEep[1] start frequency.

        """

        return self.query(":SOURce:FREQuency:STARt?")

    def get_freq_stop(self):
        """


        Returns
        -------
         Query str
            Requests the current value for SWEep[1] stop frequency.

        """

        return self.query(":SOURce:FREQuency:STOP?")

    def get_freq_unit(self):
        """


        Returns
        -------
        Query str
            Requests the currently selected frequency unit.

        """
        return self.query("UNIT:FREQuency?")

    # =============================================================================
    # Pulse Modulation
    # =============================================================================
    def get_pm_bwidth(self):
        """


        Returns
        -------
        TYPE Query str
            Requests the currently programmed phase modulation operating mode.

        """

        return self.query(":SOURce:PM:BWIDth?")

    def get_pm_internal_wave(self):
        """


        Returns
        -------
        TYPE Query str
            Requests the currently selected modulating waveform for the internal phase modulation
            function.

        """

        return self.query(":SOURce:PM:INTernal:WAVE?")

    def get_pm_internal_freq(self):
        """


        Returns
        -------
        TYPE Query str
             Requests the currently programmed modulating waveform frequency value for the
             internal phase modulation function.

        """

        return self.query(":SOURce:PM:INTernal:FREQuency?")

    def get_pm_state(self):
        """


        Returns
        -------
        TYPE Query str
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

        Returns
        -------
        None.

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

        Returns
        -------
        None.

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
        minVal = -20.0
        maxVal = 30.0
        if value > maxVal or value < minVal:
            raise ValueError(f'Power out of range! You can set power between {minVal} and {maxVal} dBm!')

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

        Returns
        -------
        None.

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

        Returns
        -------
        None.

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
                Description: Selects the modulating waveform (from the internal AM generator) for the internal AM
                function, as follows:
                SINE = Sine wave
                GAUSsian = Gaussian noise
                RDOWn = Negative ramp
                RUP = Positive ramp
                SQUare = Square wave
                TRIangle = Triangle wave
                UNIForm = Uniform noiseParameters:
                Parameters: SINE | GAUSsian | RDOWn | RUP | SQUare | TRIangle | UNIForm
                Default: SINE

        Raises
        ------
        ValueError
            Error message

        Returns
        -------
        None.

        """

        stList = ["SINE", "GAUSsian", "RDOWn", "RUP", "SQUare", "TRIangle", "UNIForm"]
        if state in stList:
            self.write(":SOURce:AM:INTernal:WAVE " + state)
        else:
            raise ValueError("Unknown input! See function description for more info.")

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

        Returns
        -------
        None.

        """

        state = self.get_am_internal_freq()
        sinUnit = ["Hz", "kHz", "MHz"]
        if state == "SINE":
            if value >= 0.1 or value <= 1 and unit in sinUnit:
                self.write(":SOURce:AM:INTernal:FREQuency " + str(value) + " " + unit)
            else:
                raise ValueError("Unknown input! See function description for more info.")

        else:
            if value >= 0.1 or value <= 100 and unit in sinUnit[:-1]:
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

        Returns
        -------
        None.

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

        Returns
        -------
        None.

        """

        if state in ["LINear", "LOGarithmic"]:
            self.write(":SOURce:AM:TYPE " + state)
        else:
            raise ValueError("Unknown input! See function description for more info.")

    # =============================================================================
    #     Correction Commands
    # =============================================================================
    def set_correction_commands(self, state):
        """


        Parameters
        ----------
        state : str/int
                Description: Turns the selected user level flatness correction power-offset table on/off.
                Parameters: ON | OFF | 1 | 0
                Default: OFF

        Raises
        ------
        ValueError
            Error message

        Returns
        -------
        None.

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
                Description: Selects the modulating waveform (from the internal FM generator) for the internal
                FM function, as follows:
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

        Returns
        -------
        None.

        """

        stList = ["SINE", "GAUSsian", "RDOWn", "RUP", "SQUare", "TRIangle", "UNIForm"]
        if state in stList:
            self.write(":SOURce:FM:INTernal:WAVE " + state)
        else:
            raise ValueError("Unknown input! See function description for more info.")

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

        Returns
        -------
        None.

        """

        state = self.get_fm_internal_freq()
        sinUnit = ["Hz", "kHz", "MHz"]
        if state == "SINE":
            if value >= 0.1 or value <= 1 and unit in sinUnit:
                self.write(":SOURce:FM:INTernal:FREQuency " + str(value) + " " + unit)
            else:
                raise ValueError("Unknown input! See function description for more info.")

        else:
            if value >= 0.1 or value <= 100 and unit in sinUnit[:-1]:
                self.write(":SOURce:FM:INTernal:FREQuency " + str(value) + " " + unit)
            else:
                raise ValueError("Unknown input! See function description for more info.")

    def set_fm_mode(self, state):
        """


        Parameters
        ----------
        state : str
                Description: Sets the synthesis mode employed in generating the FM signal, as follows:
                LOCKed[1] = Locked Narrow FM
                LOCKed2 = Locked Narrow Low-Noise FM
                UNLocked = Unlocked FM
                If LOCKed[1] or LOCKed2 is set, the YIG phase-locked loop is used in synthesizing the
                FM signal. If UNLocked is set, the YIG phase-lock loop is disabled and the FM signal is
                obtained by applying the modulating signal to the tuning coils of the YIG-tuned
                oscillator.
                Parameters: LOCKed[1] | LOCKed2 | UNLocked
                Default: UNLocked

        Raises
        ------
        ValueError
            Error message

        Returns
        -------
        None.

        """

        modList = ["LOCKed[1]", "LOCKed2", "UNLocked"]
        if state in modList:
            self.write(":SOURce:FM:MODE " + state)
        else:
            raise ValueError("Unknown input! See function description for more info.")

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

        Returns
        -------
        None.

        """

        if state in ["MIN", "MAX"]:
            self.write(":SOURce:FM:BWIDth " + state)
        else:
            raise ValueError("Unknown input! See function description for more info.")

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

        Returns
        -------
        None.

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

        Returns
        -------
        None.

        """

        minFreq = 10e6  # 10 MHz
        maxFreq = 40e9  # 40 GHz

        if unit == 'Hz' or unit is None:
            unit = 'Hz'
            if value <= maxFreq and value >= minFreq:
                self.write(f':SOURce:FREQuency:CW {value} {unit}')
            else:
                raise ValueError('Minimum Frequency = 8 kHz and Maximum Frequency = 67 GHz')
        elif unit == 'MHz':
            if value*1e6 <= maxFreq and value*1e6 >= minFreq:
                self.write(f':SOURce:FREQuency:CW {value} {unit}')
            else:
                raise ValueError('Minimum Frequency = 8 kHz and Maximum Frequency = 67 GHz')
        elif unit == 'GHz':
            if value*1e9 <= maxFreq and value*1e9 >= minFreq:
                self.write(f':SOURce:FREQuency:CW {value} {unit}')
            else:
                raise ValueError('Minimum Frequency = 8 kHz and Maximum Frequency = 67 GHz')
        else:
            raise ValueError(
                'Unknown input! Unit must be None or "MHz" or "GHz"!')

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

        Returns
        -------
        None.

        """

        stUnit = ["Hz", "kHz", "MHz", "GHz"]
        if unit in stUnit and value > 0.01:
            self.write(":SOURce:FREQuency:CW:STEP:INCRement " + str(value) + " " + unit)
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_freq_cent(self, value, unit):
        """


        Parameters
        ----------
        value :  int/float
                   Description: Sets the MG369xC RF output center frequency to the value entered. :CENTER and :SPAN
                   frequencies are coupled values. Entering the value for one will cause the other to be
                   recalculated. (See notes under :FREQuency:SPAN)
        unit : str
            Parameters: Frequency (in Hz)

        Raises
        ------
        ValueError
            Error message

        Returns
        -------
        None.

        """

        stUnit = ["Hz", "kHz", "MHz", "GHz"]
        if unit in stUnit and value > 0.01:
            self.write(":SOURce:FREQuency:CENTer " + str(value) + " " + unit)
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_freq_mode(self, state):
        """


        Parameters
        ----------
        state : str
                Description: Specifies which command subsystem controls the MG369xC frequency, as follows:
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

        Returns
        -------
        None.

        """

        stState = ["CW", "FIXed", "SWEep[1]", "SWCW", "ALSW", "LIST[1]", "LIST2", "LIST3", "LIST4"]
        if state in stState:
            self.write(":SOURce:FREQuency:MODE " + str(state))
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_freq_span(self, value, unit):
        """


        Parameters
        ----------
        value : int/float
            Description: Sets sweep span for SWEep[1] to value entered. :SPAN and :CENTer are coupled values
            Range: 1 kHz to (MAX  MIN)
            Default: MAX  MIN
        unit : str
            Parameters: Frequency (in Hz)

        Raises
        ------
        ValueError
            Error message

        Returns
        -------
        None.

        """
        """
        Description: Sets sweep span for SWEep[1] to value entered. :SPAN and :CENTer are coupled values
        Parameters: Frequency (in Hz)
        Range: 1 kHz to (MAX  MIN)
        Default: MAX  MIN
        """

        stUnit = ["Hz", "kHz", "MHz", "GHz"]
        if unit in stUnit:
            self.write(":SOURce:FREQuency:SPAN " + str(value) + " " + str(unit))
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_freq_start(self, value, unit):
        """


        Parameters
        ----------
        value : int/float
            Description: Sets start frequency for SWEep[1] to the value entered. (MIN is defined in the notes
             Range: MIN to MAX
             Default: MIN
        unit : str
            Parameters: Frequency (in Hz) | MIN

        Raises
        ------
        ValueError
            Error message

        Returns
        -------
        None.

        """

        stUnit = ["Hz", "kHz", "MHz", "GHz"]
        if unit in stUnit:
            self.write(":SOURce:FREQuency:STARt " + str(value) + " " + str(unit))
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_freq_stop(self, value, unit):
        """


        Parameters
        ----------
        value : int/float
                Description: Sets stop frequency for SWEep[1] to the value entered. (MAX is defined in the notes
                under [:SOURce]:FREQuency:CW|FIXed).
                Range: MIN to MAX
                Default: MAX
        unit : str
            Parameters: Frequency (in Hz) | MAX

        Raises
        ------
        ValueError
            Error message


        Returns
        -------
        None.

        """

        stUnit = ["Hz", "kHz", "MHz", "GHz"]
        if unit in stUnit:
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
            Description: Selects the phase modulation (ΦM) operating mode.
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


        Returns
        -------
        None.

        """

        stList = ["MIN", "MAX"]
        if state in stList:
            self.write(":SOURce:PM:BWIDth " + str(state))
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_pm_internal_wave(self, state):
        """


        Parameters
        ----------
        state : str
                Description: Selects the modulating waveform (from the internal ΦM generator) for the internal phase
                modulation function, as follows:
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

        Returns
        -------
        None.

        """

        stList = ["SINE", "GAUSsian", "RDOWn", "RUP", "SQUare", "TRIangle", "UNIForm"]
        if state in stList:
            self.write(":SOURce:PM:INTernal:WAVE " + state)
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_pm_internal_freq(self, value, unit):
        """


        Parameters
        ----------
        value : str
            Parameter: Frequency (in Hz)
        unit : int/float
            Description: Sets the frequency of the modulating waveform for the internal phase modulation
            (see :PM:INTernal:WAVE)
            Range: 0.1 Hz to 1 MHz for sine wave;
            0.1 Hz to 100 kHz for square, triangle, and ramp waveforms.
            Default: 1 kHz

        Raises
        ------
        ValueError
             Error message

        Returns
        -------
        None.

        """

        state = self.get_pm_internal_freq()
        sinUnit = ["Hz", "kHz", "MHz"]
        if state == "SINE":
            if value >= 0.1 or value <= 1 and unit in sinUnit:
                self.write(":SOURce:PM:INTernal:FREQuency " + str(value) + " " + unit)
            else:
                raise ValueError("Unknown input! See function description for more info.")

        else:
            if value >= 0.1 or value <= 100 and unit in sinUnit[:-1]:
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

        Returns
        -------
        None.

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


        Returns
        -------
        OutPut : dict
            Return a dictionary with the measured Power and CW Frequency.

        """
        OutPut = {}
        Freq = self.get_freq_cw()
        Power = self.get_output_power_level()
        OutPut["Power/dBm"] = Power
        OutPut["CW Frequency/" + str(self.get_freq_unit())] = Freq
        return OutPut

    # =============================================================================
    # Aliases for backward compatibility
    # =============================================================================
    getIdn = BaseInstrument.get_idn
    Close = BaseInstrument.close
    reset = BaseInstrument.reset
    ask_output_protection = get_output_protection
    ask_output_retrace = get_output_retrace
    ask_output_impedance = get_output_impedance
    ask_OutputPowerLevel = get_output_power_level
    ask_MaximalPowerLevel = get_maximal_power_level
    ask_am_logsens = get_am_logsens
    ask_am_logDepth = get_am_logdepth
    ask_am_internalWave = get_am_internal_wave
    ask_am_internalFreq = get_am_internal_freq
    ask_am_state = get_am_state
    ask_am_type = get_am_type
    ask_fm_internalWave = get_fm_internal_wave
    ask_fm_internalFreq = get_fm_internal_freq
    ask_fm_mode = get_fm_mode
    ask_fm_Bwidth = get_fm_bwidth
    ask_fm_state = get_fm_state
    ask_freq_CW = get_freq_cw
    ask_freq_step = get_freq_step
    ask_freq_centerFreq = get_freq_center_freq
    ask_freq_mode = get_freq_mode
    ask_freq_span = get_freq_span
    ask_freq_start = get_freq_start
    ask_freq_stop = get_freq_stop
    ask_freq_unit = get_freq_unit
    ask_pm_Bwidth = get_pm_bwidth
    ask_pm_internalWave = get_pm_internal_wave
    ask_pm_internalFreq = get_pm_internal_freq
    ask_pm_state = get_pm_state
    set_OutputPowerLevel = set_output_power_level
    set_am_logDepth = set_am_logdepth
    set_am_internalWave = set_am_internal_wave
    set_am_internalFreq = set_am_internal_freq
    set_correctionCommands = set_correction_commands
    set_fm_internalWave = set_fm_internal_wave
    set_fm_internalFreq = set_fm_internal_freq
    set_fm_Bwidth = set_fm_bwidth
    set_fm_steta = set_fm_state
    set_freq_CW = set_freq_cw
    set_pm_Bwidth = set_pm_bwidth
    set_pm_internalWave = set_pm_internal_wave
    set_pm_internalFreq = set_pm_internal_freq
    get_Data = get_data
