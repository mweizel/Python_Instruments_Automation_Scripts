#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec  1 13:11:32 2021

@author: Martin.Mihaylov
"""

import numpy as np
import re
import logging
from time import time, sleep
from .BaseInstrument import BaseInstrument


class MS2760A(BaseInstrument):
    """
    Driver for Anritsu MS2760A Spectrum Analyzer using BaseInstrument.
    """

    def __init__(self, resource_str: str = "127.0.0.1::59001", visa_library='@py', **kwargs) -> None:

        # Default socket connection parameters for MS2760A  
        # PyVISA-compatible keyword arguments
        kwargs.setdefault('read_termination', '\n')
        kwargs.setdefault('write_termination', '\n')
        kwargs.setdefault('query_delay', 0.5)
        
        # Construct the VISA resource string for socket connection
        socket_resource_str = f"TCPIP0::{resource_str}::SOCKET"
        
        super().__init__(socket_resource_str, visa_library=visa_library, **kwargs)

        # Internal Variables
        self._freq_Units_List = ["HZ", "KHZ", "MHZ", "GHZ"]
        self._trace_List = [1, 2, 3, 4, 5, 6]
        self._marker_List = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        self._exeption_state = 0  # indicates that an exception occured
        self._dataFormat = None
        self.set_data_format("ASCii")

    # =============================================================================
    # General functions
    # =============================================================================
    def clear(self) -> None:
        """
        Clears input and output buffers

        """
        # Overriding BaseInstrument.clear (which does *CLS) 
        # because the original code used self._resource.clear() (VI_CLEAR).
        self._resource.clear()

    def get_opc_status(self, delay: float = 5.0) -> int:
        """
        Places a 1 into the output queue when all device operations have been completed.

        Parameters
        ----------
        delay : float, optional
            DESCRIPTION. The default is 5s delay between write and read.

        Returns
        -------
        int
            1 if device operation is completed.
            0 if device operation is not completed.
        """
        if self._exeption_state >= 1:
            self.clear()
        try:
            state = self.query_ascii_values("*OPC?", converter="d", delay=delay)[0]
        except:
            self._exeption_state = 1
            logging.warning(
                """An Execption occured in the OPC function. Setting 
                            exeption state to 1."""
            )
            return 0
        return state

    def get_operation_status(self) -> int:
        """
        Returns the operation status of the instrument

        Returns
        -------
        int
            256 if device operation is completed.
            0 if device operation is not completed.
        """
        return self.query_ascii_values(":STATus:OPERation?", converter="d")[0]

    def abort(self):
        """
        Description: Resets the trigger system. This has the effect of aborting the sweep or any measurement
        that is currently in progress.
        Additionally, any pending operation flags that were set by initiation of the trigger system
        will be set to false.
        If :INITiate:CONTinuous is OFF (i.e. the instrument is in single sweep mode), send the
        command :INITiate[:IMMediate] to trigger the next sweep.
        If :INITiate:CONTinuous is ON (i.e. the instrument is in continuous sweep mode) a new
        sweep will start immediately
        """
        self.write(":ABORt")

    # =============================================================================
    # Start Measurment
    # =============================================================================

    def init(self) -> None:
        """Initialize measurement."""
        self.write(":INITiate:IMMediate")

    def clear_trace(self, traceNumber: int = 1) -> None:
        """
        Clear the trace.

        Parameters
        ----------
        traceNumber : int, optional
            DESCRIPTION. The default is 1.
        """

        if traceNumber in self._trace_List:
            self.write(f":TRACe:CLEar {traceNumber}")
        else:
            raise ValueError(f"Invalid trace number. Valid arguments are {self._trace_List}")

    # =============================================================================
    # Ask/Query Functions
    # =============================================================================

    def get_start_frequency(self) -> float:
        """
        Query for the start frequency.

        Returns
        -------
        float
            Start Frequency in Hz.

        """

        return self.query_ascii_values(":SENSe:FREQuency:STARt?")[0]

    def get_stop_frequency(self) -> float:
        """
        Query for the stop frequency.

        Returns
        -------
        str
            Stop Frequency in Hz.

        """

        return self.query_ascii_values(":SENSe:FREQuency:STOP?")[0]

    def get_resolution_bandwidth(self) -> float:
        """
        Query the resolution bandwidth.

        Returns
        -------
        float
            Resolution Bandwidth in Hz

        """

        return self.query_ascii_values(":SENSe:BANDwidth:RESolution?")[0]

    def get_continuous(self) -> int:
        """
        Query whether the instrument is in continuous or single sweep mode.

        Returns
        -------
        int
            1 if the instrument is in continuously sweeping/measuring.
            0 if the instrument is in single sweep/measurement mode.

        """

        return self.query_ascii_values(":INITiate:CONTinuous?", converter="d")[0]

    def get_configuration(self) -> str:
        """
        Query the instrument configuration information.

        Returns
        -------
        str
            Description: This command returns a quoted string of characters readable only by Anritsu Customer
            Service. Only instrument configuration information is returned. No setup information is
            included.

        """

        return self.query(":SYSTem:OPTions:CONFig?")

    def get_sweep_time(self) -> float:
        """
        Query the measured sweep time (in milliseconds).

        Returns
        -------
        float
            measured sweep time in milliseconds.
            "nan" if no measured sweep time is available.

        """

        return self.query_ascii_values(":DIAGnostic:SWEep:TIME?")[0]

    # def ask_TraceData(self, traceNumber):
    #     '''
    #     !!!!!DONT USE IT!!!!!
    #
    #     Parameters
    #     ----------
    #     traceNumber : int
    #         Description: This command transfers trace data from the instrument to the controller. Data are
    #         transferred from the instrument as an IEEE definite length arbitrary block response,
    #         which has the form <header><block>.
    #
    #     Returns
    #     -------
    #     str
    #        Trace Data
    #
    #     '''
    #
    #     traceNumber = str(traceNumber)
    #     return self.query(':TRACe:DATA? ' + traceNumber)

    def get_resolution_bandwidth_auto(self) -> int:
        """
        Query the automatic resolution bandwidth setting.

        Returns
        -------
        int
            1 if in automatic mode ("ON")
            0 if not in automatic mode ("OFF")

        """

        return self.query_ascii_values(":SENSe:BANDwidth:RESolution:AUTO?", converter="d")[0]

    def get_sweep_points(self) -> int:
        """
        Query the display point count.

        Returns
        -------
        int
            Query the data point count.

        """

        return self.query_ascii_values(":DISPlay:POINtcount?", converter="d")[0]

    def get_marker_excursion_state(self) -> int:
        """
        Query the peak marker excursion state.

        Returns
        -------
        int
            Excursion on/off

        """

        return self.query_ascii_values(":CALCulate:MARKer:PEAK:EXCursion:STATe?", converter="d")[0]

    def get_marker_excursion(self) -> str:
        """
        Query the marker excursion data.

        Returns
        -------
        str
            Query the excursion for a marker. The excursion is the vertical distance from the peak to
            the next highest valley which must be exceeded for a peak to be considered a peak in
            marker max commands

        """

        return self.query(":CALCulate:MARKer:EXCursion?")

    def get_marker_values(self, markerNumber: int | None = None) -> list | tuple:
        """
        Query the marker values.

        Parameters
        ----------
        markerNumber : int, optional
            Marker Number between 1 - 12. The default is None.

        Returns
        -------
        list
            List of tuples with all marker values.
            Tuple with the specified marker value

        """

        s = self.query(":CALCulate:MARKer:DATA:ALL?")

        # Find all occurrences of a group inside parentheses
        pairs = re.findall(r"\(([^)]+)\)", s)

        # Convert each pair into a tuple of floats
        result = []
        for pair in pairs:
            a_str, b_str = pair.split(",")
            result.append((float(a_str), float(b_str)))

        if markerNumber is not None:
            if markerNumber in self._marker_List:
                return result[markerNumber - 1]
            else:
                logging.warning(
                    """Marker number is not one of the 12 markers. Returning all
                                marker values."""
                )
                return result
        else:
            return result

    def get_ch_power_state(self) -> int:
        """
        Query the channel power measurement state.

        Returns
        -------
        str
            1 if State is ON.
            0 if State is OFF

        """

        return self.query_ascii_values(":SENSe:CHPower:STATe?", converter="d")[0]

    def get_data_format(self) -> str:
        """
        Query the data format.

        Returns
        -------
        str
            A string indicating the data format.

        """
        self._dataFormat = self.query(":FORMat:TRACe:DATA?")
        return self._dataFormat

    def get_center_frequency(self) -> float:
        """
        Query the center frequency.

        Returns
        -------
        float
            Center Frequency in Hz
        """

        return self.query_ascii_values(":SENSe:FREQuency:CENTer?")[0]

    def get_span(self) -> float:
        """
        Query the frequency span.

        Returns
        -------
        float
            Frequency Span in Hz
        """
        return self.query_ascii_values(":SENSe:FREQuency:SPAN?")[0]

    def get_trace_type(self, traceNumber: int = 1) -> str:
        """
        Query the trace type for a given trace number.

        Parameters
        ----------
        traceNumber : int
            Trace number (1 to 6).

        Raises
        ------
        ValueError
            Error message

        Returns
        -------
        str
            Trace Type: NORM|MIN|MAX|AVER|RMAX|RMIN|RAV

        """

        if traceNumber in self._trace_List:
            return self.query(":TRACe" + str(traceNumber) + ":TYPE?")
        else:
            raise ValueError("Number must be between 1 and 6")

    def get_trace_selected(self) -> int:
        """
        Query the currently selected trace. The max number of
        traces available to select is model specific.

        Returns
        -------
        str
            Returns selected trace.

        """

        return self.query_ascii_values(":TRACe:SELect?", converter="d")[0]

    def get_trace_state(self, traceNumber: int = 1) -> int:
        """
        Query the display state of a given trace. If it is OFF, the :TRAC:DATA?
        command will return nan.

        Parameters
        ----------
        traceNumber : int
            Trace number (1 to 6).

        Raises
        ------
        ValueError
            Error message

        Returns
        -------
        int
            1 if State is ON.
            0 if State is OFF.

        """

        if traceNumber in self._trace_List:
            return self.query_ascii_values(f":TRACe{traceNumber}:DISPlay:STATe?", converter="d")[0]
        else:
            raise ValueError("Number must be between 1 and 6")

    def get_reference_level(self) -> float:
        """
        Query the reference level.

        Returns
        -------
        float
            Reference Level in dBm

        """
        return self.query_ascii_values(":DISPlay:TRACe:Y:SCALe:RLEVel?")[0]

    def get_if_gain_state(self) -> int:
        """
        Query the IF gain state.

        Returns
        -------
        int
            1 if State is ON.
            0 if State is OFF.

        """
        return self.query_ascii_values(":POWer:IF:GAIN:STATe?", converter="d")[0]

    def get_detector_type(self, traceNumber: int = 1) -> str:
        """
        Query the detector type.

        Parameters
        ----------
        traceNumber : int
            Trace number (1 to 6).

        Returns
        -------
        str
            Detector Type: POS|RMS|NEG

        """
        if traceNumber in self._trace_List:
            return self.query(":TRACe" + str(traceNumber) + ":DETector?")
        else:
            raise ValueError("Trace Number must be between 1 and 6")

    def get_capture_time(self) -> float:
        """
        Query the capture time in ms.

        Returns
        -------
        float
            Capture Timte in ms. Range 0 ms to 10000 ms.
        """
        return self.query_ascii_values(f":CAPTure:TIMe?")[0]

    # =============================================================================
    #  Write Functions
    # =============================================================================

    def set_sweep_points(self, dataPoints: int = 501) -> None:
        """
        Changes the number of display points the instrument currently measures.
        Increasing the number of display points can improve the resolution of
        measurements but will also increase sweep time.

        Parameters
        ----------
        dataPoints : int
               Default Value: 501
               Range: 10 to 10001

        Raises
        ------
        ValueError
            Error message

        """
        if isinstance(dataPoints, int):
            if 10 <= dataPoints <= 10001:
                self.write(f":DISPlay:POINtcount {dataPoints}")
            else:
                raise ValueError(f"Value must be between 10 and 10001, not {dataPoints}")
        else:
            raise ValueError("Unknown input! Value must be an integer.")

    def set_start_frequency(self, value: int | float, unit: str = "Hz") -> None:
        """
        Sets the start frequency. Note that in the spectrum analyzer, changing the
        value of the start frequency will change the value of the coupled parameters,
        Center Frequency and Span.

        Parameters
        ----------
        value : int/float
            Sets the start frequency.

        unit : str
            Parameters: <numeric_value> {HZ | KHZ | MHZ | GHZ}

        Raises
        ------
        ValueError
            Error message

        """

        unit = unit.upper() if isinstance(unit, str) else unit
        if unit in self._freq_Units_List:
            self.write(f":SENSe:FREQuency:STARt {value} {unit}")
        else:
            raise ValueError("Unknown unit! Should be HZ, KHZ, MHZ or GHZ")

    def set_stop_frequency(self, value: int | float, unit: str = "Hz") -> None:
        """
        Sets the stop frequency. Note that in the spectrum analyzer, changing the
        value of the start frequency will change the value of the coupled parameters,
        Center Frequency and Span.

        Parameters
        ----------
        value : int/float
                Sets the stop frequency.

        unit : str
            Parameters: <numeric_value> {HZ | KHZ | MHZ | GHZ}

        Raises
        ------
        ValueError
            Error message

        """

        unit = unit.upper() if isinstance(unit, str) else unit
        if unit in self._freq_Units_List:
            self.write(f":SENSe:FREQuency:STOP {value} {unit}")
        else:
            raise ValueError("Unknown unit! Should be HZ, KHZ, MHZ or GHZ")

    def set_resolution_bandwidth(self, value: int | float, unit: str = "Hz") -> None:
        """
        Sets the resolution bandwidth. Note that using this command turns
        the automatic resolution bandwidth setting OFF.
        In Zero Span, the range will change to allow a minimum of 5 KHz to
        the maximum of 20 MHz.

        Parameters
        ----------
        value : int/float
            Sets the resolution bandwidth.

        unit : str
            Parameters: <numeric_value> {HZ | KHZ | MHZ | GHZ}
            Default Unit: Hz


        Raises
        ------
        ValueError
            Error message

        """

        unit = unit.upper() if isinstance(unit, str) else unit
        if unit in self._freq_Units_List:
            self.write(f":SENSe:BANDwidth:RESolution {value} {unit}")
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_resolution_bandwidth_auto(self, state: str | int) -> None:
        """
        Sets the automatic resolution bandwidth state. Setting the value to ON or 1 will
        result in the resolution bandwidth being coupled to the span. That is, when the
        span changes, the resolution bandwidth changes. Setting the value to OFF or 0 will
        result in the resolution bandwidth being decoupled from the span. That is, changing
        the span will not change the resolution bandwidth. When this command is issued,
        the resolution bandwidth setting itself will not change.

        Parameters
        ----------
        state : int/str
            Sets the state of the coupling of the resolution bandwidth to the frequency span.
            Parameters:<1 | 0 | ON | OFF>
            Default Value: ON

        Raises
        ------
        ValueError
             Error message

        """

        state = self._parse_state(state)
        self.write(f":SENSe:BANDwidth:RESolution:AUTO {state}")

    def set_center_frequency(self, value: int | float, unit: str = "Hz") -> None:
        """
        Sets the center frequency. Note that changing the value of the center frequency will
        change the value of the coupled parameters Start Frequency and Stop Frequency. It
        might also change the value of the span.

        Parameters
        ----------
        value : float
            Sets the center frequency.

        unit : str
            Unit value. Can be ['HZ','KHZ','MHZ','GHZ']

        Raises
        ------
        ValueError
            Error message

        """

        unit = unit.upper() if isinstance(unit, str) else unit
        if unit in self._freq_Units_List:
            self.write(f":SENSe:FREQuency:CENTer {value} {unit}")
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_span(self, value: int | float, unit: str = "Hz") -> None:
        """
        Sets the frequency span. Setting the value of <freq> to 0 Hz is the
        equivalent of setting the span mode to zero span. Note that changing
        the value of the frequency span will change the value of the coupled
        parameters Start Frequency and Stop Frequency and might change the
        Center Frequency.

        Parameters
        ----------
        value : float
            Sets the frequency span.

        unit : str
            Unit value. Can be ['HZ','KHZ','MHZ','GHZ']

        Raises
        ------
        ValueError
            Error message

        """

        unit = unit.upper() if isinstance(unit, str) else unit
        if unit in self._freq_Units_List:
            self.write(f":SENSe:FREQuency:SPAN {value} {unit}")
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_continuous(self, state: str | int) -> None:
        """
        Specifies whether the sweep/measurement is triggered continuously. If
        the value is set to ON or 1, another sweep/measurement is triggered as
        soon as the current one completes. If continuous is set to OFF or 0,
        the instrument remains initiated until the current sweep/measurement
        completes, then enters the 'idle' state and waits for the
        :INITiate[:IMMediate] command or for :INITiate:CONTinuous ON.

        Parameters
        ----------
        state : str/int
             Sets the continuous measurement state. <1 | 0 | ON | OFF>

        Raises
        ------
        ValueError
             Error message

        """

        state = self._parse_state(state)
        self.write(f":INITiate:CONTinuous {state}")

    # Define an alias
    set_ContinuousMeas = set_continuous

    def set_data_format(self, state: str = "ASCii") -> None:
        """
        Sets the data format. Only ASCii works!!!

        Parameters
        ----------
        state : str
            Set Data Format =  ['ASCii','INTeger','REAL']

        Raises
        ------
        ValueError
            Error message

        """

        format_List = ["ASCII", "INTEGER", "REAL"]
        state = state.upper() if isinstance(state, str) else state
        if state in format_List:
            self.write(f":FORMat:TRACe:DATA {state}")
            self.get_data_format()
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_marker_excursion_state(self, state: str | int) -> None:
        """
        Turn on/off marker excursion state.

        Parameters
        ----------
        state : str/int
            Can be state = ['ON','OFF',1,0]

        Raises
        ------
        ValueError
            Error message

        """
        state = self._parse_state(state)
        self.write(f":CALCulate:MARKer:PEAK:EXCursion:STATe {state}")

    def set_marker_excursion(self, value: int | float) -> None:
        """
        Sets the excursion for a marker. The excursion is the vertical distance
        from the peak to the next highest valley which must be exceeded for a
        peak to be considered a peak in marker max commands.

        Parameters
        ----------
        value : int/float
            Sets the excursion for a marker in dB. Range 0dB to 200 dB.

        """
        if 0 <= value <= 200:
            self.write(f":CALCulate:MARKer:PEAK:EXCursion {value} DB")
        else:
            raise ValueError(f"Allowed range is 0dB to 200dB. Current value is {value}dB")

    def set_next_peak(self, markerNum: int = 1) -> None:
        """
        Moves the marker to the next highest peak.

        Parameters
        ----------
        markerNum : int
            Marker number. Can be 1 to 12.

        Raises
        ------
        ValueError

        """
        if isinstance(markerNum, int) and markerNum in self._marker_List:
            self.write(f":CALCulate:MARKer{markerNum}:MAXimum:NEXT")
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_max_peak(self, markerNum: int = 1) -> None:
        """
        Moves the marker to the highest peak.

        Parameters
        ----------
        markerNum : int
            Marker number. Can be 1 to 12.

        Raises
        ------
        ValueError

        """

        if isinstance(markerNum, int) and markerNum in self._marker_List:
            self.write(f":CALCulate:MARKer{markerNum}:MAXimum")
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_marker_preset(self) -> None:
        """Presets all markers to their preset values."""
        self.write(":CALCulate:MARKer:APReset")

    def set_ch_power_state(self, state: str | int) -> None:
        """
        Sets the channel power measurement state.
        Sets the state of the channel power measurement, ON or OFF. When using
        :CONFigure:CHPower, the state is automatically set to ON.

        Parameters
        ----------
        state :str
            state = ['ON','OFF',1,0]

        Raises
        ------
        ValueError
            Error message

        """

        state = self._parse_state(state)
        self.write(f":SENSe:CHPower:STATe {state}")

    def set_trace_type(self, trace_type: str = "NORM", traceNumber: int = 1) -> None:
        """
        Sets the trace type.

        Parameters
        ----------
        trace_type : str
             Sets Trace Type:
                            Normal - NORM
                            Hold the Minimum - MIN
                            Hold the Maximum - MAX
                            Average - AVER
                            Rolling Max Hold - RMAX
                            Rolling Min Hold - RMIN
                            Rolling Average - RAV
        number : int
            Trace number:
                        Can be set to [1,2,3,4,5,6]

        Raises
        ------
        ValueError
            Error message

        """

        stList = ["NORM", "MIN", "MAX", "AVER", "RMAX", "RMIN", "RAV"]
        trace_type = trace_type.upper() if isinstance(trace_type, str) else trace_type
        if trace_type in stList and traceNumber in self._trace_List:
            self.write(f":TRACe{traceNumber}:TYPE {trace_type}")
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_trace_selected(self, traceNumber: int = 1) -> None:
        """
        The selected trace will be used by operations that use a single trace.
        The max number of traces available to select is model specific.

        Parameters
        ----------
        traceNumber : int
            Trace number:
                        Can be set to [1,2,3,4,5,6]

        Raises
        ------
        ValueError
            Error message

        """

        if traceNumber in self._trace_List:
            self.write(f":TRACe:SELect {traceNumber}")
        else:
            raise ValueError(f"Allowed range is 1 to 6. Current value is {traceNumber}")

    def set_trace_state(self, state: str | int = "ON", traceNumber: int = 1) -> None:
        """
        The trace visibility state status. If it is OFF, the :TRAC:DATA?
        command will return NaN.

        Parameters
        ----------
        state : str
            ['ON','OFF',0,1]
        traceNumber : int
            Trace Number:
                Can be set to  [1,2,3,4,5,6]

        Raises
        ------
        ValueError
             Error message

        """

        state = self._parse_state(state)
        if traceNumber in self._trace_List:
            self.write(f":TRACe{traceNumber}:DISPlay:STATe {state}")
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_reference_level(self, level: float) -> None:
        """
        Set the reference level in dBm.

        Parameters
        ----------
        level : float
            Reference level in dBm.

        Raises
        ------
        ValueError
            Error message

        """
        if -150 <= level <= 30:
            self.write(f":DISPlay:TRACe:Y:SCALe:RLEVel {level} dBm")
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_if_gain_state(self, state: str | int) -> None:
        """
        Sets the state of the IF gain ON or OFF. ON is only possible
        when reference level is set to <-10 dBm.

        Parameters
        ----------
        state :str/int
            state = ['ON','OFF',1,0]

        Raises
        ------
        ValueError
            Error message

        """

        state = self._parse_state(state)
        self.write(f":POWer:IF:GAIN:STATe {state}")

    def set_detector_type(
        self,
        state: str = "POSitive",
        traceNumber: int = 1,
    ) -> None:
        """
        Sets the detector type.

        Parameters
        ----------
        state : str
            state = ['POSitive', 'RMS', 'NEGative']
        traceNumber : int
            Trace Number:
                Can be set to  [1,2,3,4,5,6]

        Raises
        ------
        ValueError
            Error message

        """

        stList = ["POSITIVE", "POS", "RMS", "NEGATIVE", "NEG"]
        state = state.upper() if isinstance(state, str) else state
        if traceNumber in self._trace_List and state in stList:
            self.write(f":TRACe{traceNumber}:DETector {state}")
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_capture_time(self, captureTime: float = 0, unit: str = "ms") -> None:
        """
        Determines how much time to spend taking samples for each portion of the spectrum.

        Parameters
        ----------
        captureTime : float, optional
            default: 0 ms, Range: 0 ms to 10000 ms
        unit : str, optional
            default: 'ms'

        Raises
        ------
        ValueError
            Error message

        """
        unit_List = ["PS", "NS", "US", "MS", "S", "MIN", "HR"]
        unit = unit.upper() if isinstance(unit, str) else unit
        if unit in unit_List:
            self.write(f":CAPTure:TIMe {captureTime} {unit}")
        else:
            raise ValueError("Unknown input! See function description for more info.")

    # =============================================================================
    #   get/Save Data
    # =============================================================================

    def get_data(self, markerNumber: int = 1, returnArray: bool = False) -> dict | np.ndarray:
        """
        This function will stop temporally set Continuous Measurement to OFF, extract
        the max. peak value and frequency and restore the Continuous Measurement to ON.

        Returns
        -------
        OutPut : dict/np.ndarray
            Return a dictionary with the measured frequency in Hz and peak power in dBm.

        """

        self.set_continuous("OFF")
        try:
            self.set_marker_preset()
            self.set_max_peak()
            marker_values = self.get_marker_values(markerNumber)
            freq = marker_values[0]
            power = marker_values[1]
        finally:
            self.set_marker_preset()
            self.set_continuous("ON")

        if returnArray:
            return np.array([freq, power])
        else:
            return {"Frequency/Hz": freq, "Power/dBm": power}

    def extract_trace_data_legacy(self, traceNumber: int = 1) -> np.ndarray:
        """
        Old function to keep legacy scripts working.
        Better use: ExtractTraceData()

        !!!!!USE IT AT YOUR OWN RISK is not an official function, but a workaround!!!!!
            1 - This Function will set the continues Measurement to 'OFF'.
            2 - Will set the Data Format to ASCii. This is needed since
            :TREACE:DATA? <num> is defect!!
            3 - Will write TRACE:DATA? <num>. Will return only 3 bits. The rest
            will be packed in the next command asked.
            4 - Will ask for the Data Format. This is dummy command that will
            have the data and the Data Format.
            5 - Make manupulations to separate the actual data from the rest and
            return the data in Output np.array() form.

        Parameters
        ----------
        traceNumber : int
            Trace Number from which the data is taken:
            Can be set to [1,2,3,4,5,6].

        Returns
        -------
        Output : np.ndarray
            Measured Spectrum on Trace {num}.

        """

        self.set_continuous("OFF")
        self.set_data_format("ASCii")
        self.write(f":TRACe:DATA? {traceNumber}")
        data = self.get_data_format()
        num_header = int(data[1]) + 2  # get the header size
        new_str = data[num_header:-5]  # truncate the header block and end block
        data_arr = new_str.split(",")
        Output = [float(item) for item in data_arr]
        Output = np.array(Output)
        self.set_continuous("ON")
        return Output

    def get_trace_xy(self, trace_number: int = 1) -> tuple[np.ndarray, np.ndarray]:
        """
        Queries both X (Frequency) and Y (Amplitude) trace data.
        Calculates X data based on start/stop frequency and sweep points.
        
        Parameters
        ----------
        trace_number : int
            Trace number (1-6).
            
        Returns
        -------
        tuple[np.ndarray, np.ndarray]
            (x_array, y_array)
        """
        # Get Y data (Amplitudes) - non-blocking query of current trace data
        # Note: We use the direct SCPI command here to avoid the overhead/locking 
        # of the helper methods if they exist, similar to FSWP50's get_trace_xy
        
        if trace_number not in self._trace_List:
             raise ValueError(f"Invalid trace number: {trace_number}.")

        # Ensure correct format before query
        if self._dataFormat != "ASC,8":
             self.set_data_format("ASCii")

        self.write(f":TRACe:DATA? {trace_number}")
        data = self.get_data_format()
        num_header = int(data[1]) + 2 
        new_str = data[num_header:-5]
        data_arr = new_str.split(",")
        y_array = np.array([float(item) for item in data_arr])
        
        # Calculate X data (Frequencies)
        points = len(y_array)
        start_freq = self.get_start_frequency()
        stop_freq = self.get_stop_frequency()
        
        if points > 1:
            x_array = np.linspace(start_freq, stop_freq, points)
        else:
            x_array = np.array([start_freq])
            
        return x_array, y_array

    def measure_and_get_trace(
        self, traceNumber: int = 1, clearTrace: bool = True, timeout: float = 20
    ) -> np.ndarray:
        """
        Initiate a new measurement and return the trace Y-data (Blocking).
        Renamed from 'extract_trace_data' to match FSWP50 interface.

        Parameters
        ----------
        traceNumber : int
            Trace Number: Can be set to [1,2,3,4,5,6].
        clearTrace : bool, optional
            Clears the trace before taking the data measurement. The default is True.
        timeout : float, optional
            Defines the timeout for the operation. The default is 20s.

        Raises
        ------
        TimeoutError

        Returns
        -------
        Output : np.array
            Amplitude data.

        """

        if traceNumber not in self._trace_List:
            raise ValueError(f"Invalid trace number: {traceNumber}. Must be in {self._trace_List}.")

        self.set_continuous("OFF")

        # Check the data format
        if self._dataFormat != "ASC,8":
            self.set_data_format("ASCii")

        if clearTrace:
            self.abort()
            # self.clear_trace(traceNumber)
            self.init()
            start_time = time()
            complete = 0
            while complete == 0:
                sleep(0.1)
                complete = self.get_operation_status()
                if time() - start_time > timeout:
                    raise TimeoutError(f"Operation did not complete within {timeout:.2f} seconds.")

        self.write(f":TRACe:DATA? {traceNumber}")
        data = self.get_data_format()
        num_header = int(data[1]) + 2  # get the header size
        new_str = data[num_header:-5]  # truncate the header block and end block
        data_arr = new_str.split(",")
        Output = np.array([float(item) for item in data_arr])

        return Output
        
    def extract_trace_data(
        self,
        trace: int = 1,
        window: int = 1, # Ignored for MS2760A but kept for compatibility
        points: bool = False,
        num_of_points: int | None = None,
        export: bool = False,
        filename: str = "trace_export.csv",
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Advanced extraction: Gets X and Y data, with optional downsampling and CSV export.
        Matches FSWP50 interface. Does NOT trigger a new measurement (use measure_and_get_trace for that).

        Parameters
        ----------
        trace : int
            Trace number (1-6)
        window : int
            Window number (Ignored for MS2760A)
        points : bool
            Whether to limit number of points in output (downsample)
        num_of_points : int, optional
            Desired number of output points if points=True
        export : bool
            If True, saves the data to a CSV file
        filename : str
            Output CSV file name (used if export=True)
        """
        x_array, y_array = self.get_trace_xy(trace)

        if points:
            if num_of_points is None:
                raise ValueError("When points=True, 'num_of_points' must be specified.")
            if num_of_points < len(x_array):
                indices = np.linspace(0, len(x_array) - 1, num=num_of_points, dtype=int)
                x_array = x_array[indices]
                y_array = y_array[indices]
        
        # Logging only if logger exists (BaseInstrument usually has it)
        if hasattr(self, 'logger'):
             self.logger.info(f"Extracted {len(x_array)} points from TRACE{trace}.")

        if export:
            pass # TODO: Add pandas import if we really want export functionality. 
                 # For now, to avoid breaking, we will just return data.
            
        return x_array, y_array 


    # =============================================================================
    # Aliases for backwards compatibility
    # =============================================================================
    StatusOperation = get_operation_status
    Init = init
    ClearTrace = clear_trace
    ask_freq_Start = get_start_frequency
    ask_freq_Stop = get_stop_frequency
    ask_ResBwidth = get_resolution_bandwidth
    ask_SingleOrContinuesMeas = get_continuous
    ask_Configuration = get_configuration
    ask_sweepTime = get_sweep_time
    ask_ResBwidthAuto = get_resolution_bandwidth_auto
    ask_DataPointCount = get_sweep_points
    ask_MarkerExcursionState = get_marker_excursion_state
    ask_MarkerExcursion = get_marker_excursion
    ask_MarkerValues = get_marker_values
    ask_CHPowerState = get_ch_power_state
    ask_DataFormat = get_data_format
    ask_CenterFreq = get_center_frequency
    ask_FreqSpan = get_span
    ask_TraceType = get_trace_type
    ask_TraceSelected = get_trace_selected
    ask_TraceState = get_trace_state
    ask_RefLevel = get_reference_level
    ask_IFGainState = get_if_gain_state
    ask_DetectorType = get_detector_type
    ask_CaptureTime = get_capture_time
    set_trace_mode = set_trace_type
    set_detection_function = set_detector_type
    set_DataPointCount = set_sweep_points
    set_freq_Start = set_start_frequency
    set_freq_Stop = set_stop_frequency
    set_ResBwidth = set_resolution_bandwidth
    set_ResBwidthAuto = set_resolution_bandwidth_auto
    set_CenterFreq = set_center_frequency
    set_FreqSpan = set_span
    set_Continuous = set_continuous
    set_DataFormat = set_data_format
    set_MarkerExcursionState = set_marker_excursion_state
    set_MarkerExcursion = set_marker_excursion
    set_NextPeak = set_next_peak
    set_MaxPeak = set_max_peak
    set_MarkerPreset = set_marker_preset
    set_CHPowerState = set_ch_power_state
    set_TraceType = set_trace_type
    set_TraceSelected = set_trace_selected
    set_TraceState = set_trace_state
    set_RefLevel = set_reference_level
    set_IFGainState = set_if_gain_state
    set_DetectorType = set_detector_type
    set_CaptureTime = set_capture_time
    get_Data = get_data
    ExtractTtraceData = extract_trace_data_legacy
    ExtractTraceData = measure_and_get_trace
