"""
Created on Wed Feb 26 20:21:23 2025

@author: Maxim Weizel
@contributor: Rakibul Islam
"""

import os
from time import sleep, time

import numpy as np
import pandas as pd

from .BaseInstrument import BaseInstrument

try:
    from typing import deprecated  # type: ignore
except ImportError:
    from typing_extensions import deprecated


class FSWP50(BaseInstrument):
    """
    This class is using PyVISA to connect. Requires NI-VISA or Keysight VISA backend.
    """

    def __init__(self, resource_str: str, visa_library: str = "@py", **kwargs):
        kwargs.setdefault("timeout", 5000)  # 5s

        # BaseInstrument handles connection and logging
        super().__init__(resource_str=resource_str, visa_library=visa_library, **kwargs)

        # Internal Variables
        self._freq_Units_List = ["HZ", "KHZ", "MHZ", "GHZ"]
        self._state_List = ["OFF", "ON", 1, 0]
        self._trace_List = [1, 2, 3, 4, 5, 6]  # <t> in documentation
        self._window_List = list(range(1, 17))  # <n> in documentation

    # =============================================================================
    # Communication Wrappers (Inherited from BaseInstrument)
    # =============================================================================

    # =============================================================================
    # Basic Functions
    # =============================================================================

    # get_idn, reset, clear, wait are inherited.

    def abort(self) -> None:
        """Abort the measurement (execute ABORT command)."""
        self.write("ABORt")
        self.wait()

    # =============================================================================
    # Channel & Application Management
    # =============================================================================

    def list_channels(self) -> list:
        """
        Queries all active channels. The query is useful to obtain the names of the existing
        channels, which are required to replace or delete the channels.
        """
        response = self.query("INSTrument:LIST?")
        if not response or response.upper() == "NONE":
            return []
        return [s.strip().strip("'").strip('"') for s in response.split(",")]

    def create_channel(self, channel_type: str, channel_name: str) -> None:
        """
        Creates a new measurement channel.

        Parameters
        ----------
        channel_type : str
            Channel type. Available types are:
                'PNOISE': 'Phase Noise',
                'SMONITOR': 'Spectrum Monitor',
                'SANALYZER': 'Spectrum (R&S FSWP-B1)',
                'IQ': 'I/Q Analyzer',
                'PULSE': 'Pulse Measurement',
                'ADEMOD': 'Analog modulation analysis',
                'NOISE': 'Noise Figure Measurements',
                'SPUR': 'Fast Spur Search',
                'TA': 'Transient Analysis',
                'DDEM': 'VSA - Vector Signal Analysis'
        channel_name : str
            Unique name for the new channel.

        Raises
        ------
        ValueError
            If channel type is invalid or name already exists.
        RuntimeError
            If instrument command fails.
        """
        available_types = [
            "PNOise",
            "SMONitor",
            "SANalyzer",
            "IQ",
            "PULSe",
            "ADEMod",
            "NOISe",
            "SPUR",
            "TA",
            "DDEM",
        ]
        valid_type = self._check_scpi_param(channel_type, available_types)
        self.write(f"INSTrument:CREate {valid_type}, '{channel_name}'")

    def delete_channel(self, channel_name: str) -> None:
        """
        Deletes a channel.
        If you delete the last channel, the default "Phase Noise" channel is activated.

        Parameters
        ----------
        channel_name : str
            Your Channel Name.
        """
        self.write(f":INST:DEL '{channel_name}'")

    def set_multiview_tab(self, state) -> None:
        """
        Toggles the MultiView tab display.

        Parameters
        ----------
        state : bool or int
            True/1 to enable MultiView (ON), False/0 to disable (OFF).
        """
        state = self._parse_state(state)
        self.write(f"DISPlay:ATAB {state}")

    def duplicate_selected_channel(self, channel_name: str):
        """
        Duplicates the specified channel.

        Parameters
        ----------
        channel_name : str
            The name of the channel to duplicate.
        """
        self.write(f"INSTrument:SELect '{channel_name}'")
        sleep(0.1)
        self.write("INSTrument:CREate:DUPLicate")

    # =============================================================================
    # Spectrum Analyzer - Frequency & Span
    # =============================================================================

    def set_center_frequency(self, center_freq: int | float, unit: str = "Hz") -> None:
        """
        Sets the center frequency for pulsed and VCO measurements.

        Parameters
        ----------
        center_freq : int | float
            Frequency value (e.g., 1, 2.5) to be combined with unit.
        unit : str, optional
            Unit of frequency: HZ, KHZ, MHZ, or GHZ. Default is 'Hz'.
        """
        unit = unit.upper()
        if unit in self._freq_Units_List:
            self.write(f"FREQ:CENT {center_freq} {unit}")
        else:
            raise ValueError("Unknown unit! Use one of: HZ, KHZ, MHZ, GHZ")

    def get_center_frequency(self) -> float:
        """Queries the current center frequency in Hz."""
        return self.query_float("FREQ:CENT?")

    def set_start_frequency(self, start_freq: int | float, unit: str = "Hz") -> None:
        """
        This command defines the start frequency offset of the measurement range.

        Parameters
        ----------
        start_freq : float
            Start frequency.
        unit : str, optional
            Unit of frequency. Default is 'Hz'.
        """
        unit = unit.upper()
        if unit in self._freq_Units_List:
            self.write(f":SENS:FREQ:STAR {start_freq}{unit}")
        else:
            raise ValueError("Unknown unit! Should be HZ, KHZ, MHZ or GHZ")

    def get_start_frequency(self) -> float:
        """Queries the current start frequency in Hz."""
        return self.query_float(":SENS:FREQ:STAR?")

    def set_stop_frequency(self, stop_freq: int | float, unit: str = "Hz") -> None:
        """
        This command defines the stop frequency offset of the measurement range.

        Parameters
        ----------
        stop_freq : float
            Stop frequency.
        unit : str, optional
            Unit of frequency. Default is 'Hz'.
        """
        unit = unit.upper()
        if unit in self._freq_Units_List:
            self.write(f":SENS:FREQ:STOP {stop_freq}{unit}")
        else:
            raise ValueError("Unknown unit! Should be HZ, KHZ, MHZ or GHZ")

    def get_stop_frequency(self) -> float:
        """Queries the current stop frequency in Hz."""
        return self.query_float(":SENS:FREQ:STOP?")

    def set_span(self, span: int | float, unit: str = "Hz") -> None:
        """
        Sets the frequency span for the spectrum analyzer.

        Parameters
        ----------
        span : int | float
            Span value.
        unit : str, optional
            Frequency unit: HZ, KHZ, MHZ, or GHZ. Default is 'Hz'.
        """
        unit = unit.upper()
        if unit in self._freq_Units_List:
            self.write(f"FREQ:SPAN {span}{unit}")
        else:
            raise ValueError("Unknown unit! Should be HZ, KHZ, MHZ, or GHZ.")

    def get_span(self) -> float:
        """Queries the current frequency span in Hz."""
        return self.query_float("FREQ:SPAN?")

    # =============================================================================
    # Spectrum Analyzer - Bandwidth & Amplitude
    # =============================================================================

    def set_resolution_bandwidth(self, res_bw: int | float, unit: str = "Hz") -> None:
        """
        Sets the resolution bandwidth.

        Parameters
        ----------
        res_bw : int | float
            Sets the resolution bandwidth.
        unit : str, optional
            Parameters: {HZ | KHZ | MHZ | GHZ}. Default Unit: Hz
        """
        unit = unit.upper()
        if unit in self._freq_Units_List:
            self.write(f":SENS:BAND:RES {res_bw}{unit}")
        else:
            raise ValueError("Unknown unit! Should be HZ, KHZ, MHZ or GHZ")

    def get_resolution_bandwidth(self) -> float:
        """Queries the current resolution bandwidth in Hz."""
        return self.query_float(":SENS:BAND:RES?")

    def set_reference_level(self, ref_level: float) -> None:
        """
        This command defines the maximum level displayed on the y-axis.

        Parameters
        ----------
        ref_level : float
            Default unit: Depending on the selected diagram.
        """
        self.write(f":DISP:WIND:TRAC:Y:SCAL:RLEV {ref_level}")

    def get_reference_level(self) -> float:
        """Queries the current reference level."""
        return self.query_float(":DISP:WIND:TRAC:Y:SCAL:RLEV?")

    def set_reference_level_lower(self, ref_level: float = 0) -> None:
        """
        This command defines the minimum level displayed on the y-axis.

        Parameters
        ----------
        ref_level : float, optional
            Default unit: Depending on the selected diagram.
        """
        self.write(f":DISP:WIND:TRAC:Y:SCAL:RLEV:LOW {ref_level}")

    def get_reference_level_lower(self) -> float:
        """Queries the minimum level displayed on the y-axis."""
        return self.query_float(":DISP:WIND:TRAC:Y:SCAL:RLEV:LOW?")

    def set_input_attenuation_auto(self, state: str | int) -> None:
        """Set the input attenuation auto mode to ON or OFF.

        Parameters
        ----------
        state : str | int
            Can be: [ON, 1, OFF, 0]
        """
        state = self._parse_state(state)
        self.write(f":INP:ATT:AUTO {state}")

    def get_input_attenuation_auto(self) -> str:
        """Queries whether input attenuation auto mode is ON or OFF."""
        raw = self.query(":INP:ATT:AUTO?")
        return "ON" if raw.strip() in ["1", "ON"] else "OFF"

    def set_input_attenuation(self, atten: float) -> None:
        """Set the input attenuation.

        Parameters
        ----------
        atten : float
            Attenuation value.
        """
        self.write(f":INP:ATT {atten}")

    def get_input_attenuation(self) -> float:
        """Queries the input attenuation value."""
        return self.query_float(":INP:ATT?")

    # =============================================================================
    # Sweep & Trigger
    # =============================================================================

    def set_continuous(self, state: int | str) -> None:
        """
        Controls the measurement mode for an individual channel.

        Parameters
        ----------
        state : int or str
            ``ON | OFF | 1 | 0``
        """
        state = self._parse_state(state)
        self.write(f"INITiate:CONT {state}")

    def init_single_measurement(self) -> None:
        """
        Restarts a (single) measurement that has been stopped (using ABORt)
        or finished in single measurement mode.
        """
        self.write("INITiate:CONMeas")

    def init(self) -> None:
        """
        Starts a (single) new measurement.
        """
        self.write("INITiate:IMMediate")

    def set_sweep_points(self, datapoints: int) -> None:
        """
        This command defines the number of measurement points to analyze after a measurement.

        Parameters:
            datapoints (int): Number of data points (101 to 100001).
        """
        if 101 <= datapoints <= 100001:
            self.write(f":SENS:SWE:WIND:POIN {datapoints}")
        else:
            raise ValueError(f"Value must be between 101 and 100001, not {datapoints}")

    def get_sweep_points(self) -> int:
        """Queries the number of measurement points."""
        return int(self.query_float(":SENS:SWE:WIND:POIN?"))

    # =============================================================================
    # Trace Acquisition, Extraction & Export
    # =============================================================================

    def get_trace_data(self, trace_number: int, window_number: int = 1) -> np.ndarray:
        """
        Queries current trace Y-data (Amplitudes) from the instrument.

        Parameters
        ----------
        trace_number : int
            Trace number between 1 and 6
        window_number : int, optional
            Window number between 1 and 16, by default 1
        """
        if trace_number not in self._trace_List:
            raise ValueError(f"Unknown trace number {trace_number}! Should be between 1 and 6.")
        if window_number not in self._window_List:
            raise ValueError(f"Unknown window number {window_number}! Should be between 1 and 16.")

        data = self.query_ascii_values(f":TRAC{window_number}:DATA? TRACE{trace_number}")
        return np.array(data)

    def get_trace_xy(
        self, trace_number: int = 1, window_number: int = 1
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Queries both X (Frequency/Offset) and Y (Amplitude) trace data.
        Often used in Phase Noise application where X-axis spacing is non-linear.

        Parameters
        ----------
        trace_number : int, optional
            The trace number to query. Default is 1.
        window_number : int, optional
            The window number to query. Default is 1.
        """
        trace_str = f"TRACE{trace_number}"
        try:
            x = self.query_ascii_values(f"TRACe{window_number}:DATA:X? {trace_str}")
            y = self.query_ascii_values(f"TRACe{window_number}:DATA:Y? {trace_str}")

            if not x or not y or len(x) != len(y):
                raise RuntimeError("Failed to retrieve or match trace data lengths.")

            return np.array(x), np.array(y)
        except Exception as e:
            self.logger.error(f"Error retrieving XY data: {e}")
            raise

    def measure_and_get_trace(
        self,
        trace_number: int = 1,
        window_number: int = 1,
        clear_trace: bool = True,
        timeout: float = 20,
    ) -> np.ndarray:
        """
        Initiate a new measurement and return the trace Y-data (Blocking).
        Matches standard legacy spectrum analyzer behavior.

        Parameters
        ----------
        trace_number : int
            Trace Number: Can be set to [1,2,3,4,5,6].
        clear_trace : bool, optional
            Clears the trace before taking the data measurement. The default is True.
        timeout : float, optional
            Defines the timeout for the operation. The default is 20s.
        window_number : int, optional
            Window number between 1 and 16, by default 1
        """
        if trace_number not in self._trace_List:
            raise ValueError(f"Invalid trace number: {trace_number}.")

        self.set_continuous("OFF")

        if clear_trace:
            self.abort()
            self.init()
            self.wait()
            start_time = time()
            while True:
                if self.OPC() == 1:
                    break
                if time() - start_time > timeout:
                    raise TimeoutError(f"Operation did not complete within {timeout}s.")
                sleep(0.1)

        return self.get_trace_data(trace_number, window_number)

    def extract_trace_data(
        self,
        trace: int = 1,
        window: int = 1,
        points: bool = False,
        num_of_points: int | None = None,
        export: bool = False,
        filename: str = "trace_export.csv",
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Advanced extraction: Gets X and Y data, with optional downsampling and CSV export.

        Parameters
        ----------
        trace : int
            Trace number (1-6)
        window : int
            Window number (1-16)
        points : bool
            Whether to limit number of points in output (downsample)
        num_of_points : int, optional
            Desired number of output points if points=True
        export : bool
            If True, saves the data to a CSV file
        filename : str
            Output CSV file name (used if export=True)
        """
        x_array, y_array = self.get_trace_xy(trace, window)

        if points:
            if num_of_points is None:
                raise ValueError("When points=True, 'num_of_points' must be specified.")
            if num_of_points < len(x_array):
                indices = np.linspace(0, len(x_array) - 1, num=num_of_points, dtype=int)
                x_array = x_array[indices]
                y_array = y_array[indices]

        self.logger.info(f"Extracted {len(x_array)} points from WINDOW{window}, TRACE{trace}.")

        if export:
            self.export_trace_to_csv(y_array, x_data=x_array, filename=filename)

        return x_array, y_array

    def export_trace_to_csv(
        self,
        y_data: np.ndarray,
        x_data: np.ndarray | None = None,
        filename: str = "trace_output.csv",
    ):
        """
        Exports trace data to a CSV file using pandas.

        Parameters
        ----------
        y_data : np.ndarray
            The amplitude/phase noise data (Y-axis).
        x_data : np.ndarray, optional
            The frequency/offset data (X-axis). If None, an index column is created.
        filename : str, optional
            The name of the CSV file.
        """
        if not isinstance(y_data, np.ndarray):
            raise TypeError("y_data must be a numpy array.")

        try:
            if x_data is not None:
                if len(x_data) != len(y_data):
                    raise ValueError("X and Y data must have the same length.")
                df = pd.DataFrame({"X-Axis": x_data, "Y-Axis": y_data})
            else:
                df = pd.DataFrame({"Index": np.arange(len(y_data)), "Y-Axis": y_data})

            df.to_csv(filename, index=False)
            self.logger.info(f"Trace data exported successfully to '{os.path.abspath(filename)}'")
        except Exception as e:
            self.logger.error(f"Failed to export CSV: {e}")
            raise

    # =============================================================================
    # Trace Display Settings
    # =============================================================================

    def set_trace_mode(
        self, trace_mode: str, trace_number: int = 1, window_number: int = 1
    ) -> None:
        """Selects the trace mode (WRITE, AVERAGE, MAXHOLD, etc)."""
        trace_mode_list = [
            "WRITe",
            "AVERage",
            "MAXHold",
            "MINHold",
            "VIEW",
            "BLANk",
        ]
        valid_mode = self._check_scpi_param(trace_mode, trace_mode_list)
        self.write(f"DISPlay:WINDOW{window_number}:TRACE{trace_number}:MODE {valid_mode}")

    def set_detection_function(
        self, det_func: str, trace_number: int = 1, window_number: int = 1
    ) -> None:
        """
        Defines the trace detector to be used for trace analysis

        Parameters
        ----------
        det_func : str
            detector function: APEAK|NEGATIVE|POSITIVE|RMS|AVERAGE|SAMPLE
        trace_number : int, optional
            Trace number, by default 1.
        window_number : int, optional
            Window number, by default 1.
        """
        det_func_list = [
            "APEak",
            "NEGative",
            "POSitive",
            "RMS",
            "AVERage",
            "SAMPle",
        ]
        valid_det = self._check_scpi_param(det_func, det_func_list)
        self.write(f":SENS:WIND{window_number}:DET{trace_number}:FUNC {valid_det}")

    def set_trace_smoothing(self, window: int = 1, trace: int = 1, state: str | int = "ON") -> None:
        """
        Enables or disables smoothing for a trace.

        SCPI Reference: DISP:WIND<n>:TRAC<t>:SMO:STAT
        """
        state = self._parse_state(state)
        self.write(f"DISP:WIND{window}:TRAC{trace}:SMO:STAT {state}")
        self.logger.info(f"Smoothing set to {state} for TRACE{trace} in WINDOW{window}.")

    def set_spur_hide(self, window: int = 1, trace: int = 1, state: str | int = "ON") -> None:
        """
        Enables or disables hiding of spurs in display

        SCPI Reference: DISP:WIND<n>:TRAC<t>:SPUR:SUPP
        """
        state = self._parse_state(state)
        self.write(f"DISP:WIND{window}:TRAC{trace}:SPUR:SUPP {state}")
        self.logger.info(f"Spur hiding set to {state} for TRACE{trace} in WINDOW{window}.")

    # =============================================================================
    # Phase Noise
    # =============================================================================

    def set_start_offset(self, start_offset: int | float, unit: str = "Hz") -> None:
        """
        Sets the start offset frequency for phase noise measurement.
        Reference: User manual, page number 481

        Parameters
        ----------
        start_offset : int or float
            The numeric value of the start offset.
        unit : str, optional
            Unit of the offset: 'Hz', 'kHz', 'MHz', 'GHz'. Default is 'Hz'.
        """
        unit = unit.upper()
        if unit not in self._freq_Units_List:
            raise ValueError("Unknown unit! Use HZ, KHZ, MHZ, or GHZ.")
        self.write(f"SENSe:FREQuency:STARt {start_offset}{unit}")

    def get_start_offset(self, unit: str = "Hz") -> float:
        """
        Queries the current start offset frequency for phase noise measurement.

        Parameters
        ----------
        unit : str, optional
            Output unit. Accepted values: 'Hz', 'kHz', 'MHz', 'GHz'. Default is 'Hz'.
        """
        unit = unit.upper()
        if unit not in self._freq_Units_List:
            raise ValueError("Invalid unit. Choose from Hz, kHz, MHz, GHz.")

        freq_hz = self.query_float("SENSe:FREQuency:STARt?")

        conversion = {"HZ": 1, "KHZ": 1e3, "MHZ": 1e6, "GHZ": 1e9}
        return freq_hz / conversion[unit]

    def set_stop_offset(self, stop_offset: int | float, unit: str = "Hz") -> None:
        """
        Sets the stop offset frequency for phase noise measurement.
        Reference: User manual, page number 482

        Parameters
        ----------
        stop_offset : int or float
            The numeric value of the stop offset.
        unit : str, optional
            Unit of the offset: 'Hz', 'kHz', 'MHz', 'GHz'. Default is 'Hz'.
        """
        unit = unit.upper()
        if unit not in self._freq_Units_List:
            raise ValueError("Unknown unit! Use HZ, KHZ, MHZ, or GHZ.")
        self.write(f"SENSe:FREQuency:STOP {stop_offset}{unit}")

    def get_stop_offset(self, unit: str = "Hz") -> float:
        """
        Queries the stop offset frequency for phase noise measurement.

        Parameters
        ----------
        unit : str, optional
            Output unit. One of 'Hz', 'kHz', 'MHz', 'GHz'. Default is 'Hz'.
        """
        unit = unit.upper()
        if unit not in self._freq_Units_List:
            raise ValueError("Invalid unit!")

        stop_hz = self.query_float("SENSe:FREQuency:STOP?")
        conversion = {"HZ": 1, "KHZ": 1e3, "MHZ": 1e6, "GHZ": 1e9}
        return stop_hz / conversion[unit]

    def set_rbw_ratio(self, percentage: float) -> None:
        """
        Set RBW as a ratio (%) of start offset (automatic mode).

        Parameters
        ----------
        percentage : float
            RBW ratio in percent (0.1 to 30).
        """
        if not (0.1 <= float(percentage) <= 30):
            raise ValueError("Percentage must be between 0.1 and 30.")

        self.write("SWE:MODE NORM")
        self.write(f"LIST:BWID:RAT {percentage}")

    def set_rbw_absolute(self, half_decade: int, bandwidth: float, unit: str) -> None:
        """
        Set absolute RBW for a specific half-decade (manual mode).

        Parameters
        ----------
        half_decade : int
            Half-decade index (1 ... N).
        bandwidth : float
            RBW value.
        unit : str
            One of: Hz, kHz, MHz
        """
        unit = unit.strip().upper()
        if unit not in ["HZ", "KHZ", "MHZ"]:
            raise ValueError("Invalid unit. Use Hz, kHz, or MHz.")

        self.write("SWE:MODE MAN")
        self.write(f"LIST:RANG{half_decade}:BWID {float(bandwidth)}{unit}")

    def get_rbw_pn(self) -> float | dict:
        """
        Queries the current Resolution Bandwidth (RBW) setting for phase noise.

        - Automatically detects if the mode is 'NORM' (automatic ratio) or 'MAN' (manual).
        - Returns the RBW ratio (%) or manual RBW values per half-decade.

        Reference:
            - RBW Ratio: LIST:BWID:RAT? (Page 485)
            - Manual RBW: LIST:RANG<ri>:BWID? (Page 485)
            - Mode: SWE:MODE? (Page 488)
        """
        mode = self.query("SWE:MODE?").strip().upper()
        if mode == "NORM":
            percentage = float(self.query("LIST:BWID:RAT?"))
            self.logger.info(f"RBW Mode: Automatic Ratio → {percentage}% of start offset")
            return percentage
        elif mode == "MAN":
            rbw_values = {}
            for ri in range(1, 11):  # Half-decades 1 to 10
                try:
                    val = self.query(f"LIST:RANG{ri}:BWID?")
                    rbw_values[ri] = val
                except Exception:
                    continue
            self.logger.info("RBW Mode: Manual (Absolute values per half-decade)")
            return rbw_values
        else:
            raise RuntimeError(f"Unknown RBW mode detected: '{mode}'")

    def set_xcorr_factor_auto(self, factor: int = 1) -> None:
        """
        Sets the cross-correlation factor in automatic (normal) mode for phase noise.

        Reference:
            User Manual, page 490.
            Defining cross-correlation parameters: page 169

        Parameters
        ----------
        factor : int
            Cross-correlation factor. Must be an integer >= 1.
        """
        if factor < 1:
            raise ValueError("XCORR factor must be an integer >= 1.")
        self.write("SWE:MODE NORM")
        self.write(f"SWE:XFAC {factor}")

    def set_xcorr_optimization(self, enable: bool, threshold: float | None = None) -> None:
        """
        Configure XCORR optimization and optional threshold.

        Parameters
        ----------
        enable : bool
            Enable (True) or disable (False) XCORR optimization.
        threshold : float, optional
            Optional threshold in dB.
        """
        state = self._parse_state(enable)
        self.write(f"SWE:XOPT {state}")
        if enable and threshold is not None:
            self.write(f"SWE:XOPT:THR {threshold}")

    def set_capture_range(self, mode: str) -> None:
        """
        Set the Capture Range for Phase Noise measurement.

        Parameters
        ----------
        mode : str
            Capture Range mode. Options: "Normal", "Wide", "40MHz".
        """
        mode_map = {
            "NORMAL": "NORM",
            "NORM": "NORM",
            "WIDE": "WIDE",
            "40MHZ": "R40MHZ",
            "R40MHZ": "R40MHZ",
        }
        mode_key = mode.strip().upper()
        if mode_key not in mode_map:
            raise ValueError(f"Invalid mode '{mode}'. Valid options: Normal, Wide, 40MHz")
        self.write(f"SWE:CAPT:RANG {mode_map[mode_key]}")

    # =============================================================================
    # Integrated Measurements
    # =============================================================================

    def set_integration_manual(self, range_index: int, start_freq: str, stop_freq: str) -> None:
        """
        Sets a custom integration range for the Integrated Measurement tab.
        Reference: Page 173-174.

        Parameters
        ----------
        range_index : int
            Integration range index (1-10).
        start_freq : str
            Start frequency with unit (e.g., '10Hz', '1kHz').
        stop_freq : str
            Stop frequency with unit.
        """
        if range_index not in range(1, 11):
            raise ValueError("Invalid range index. Must be between 1 and 10.")

        self.write(f"CALC1:RANG{range_index}:EVAL:STAT OFF")
        self.write(f"CALC1:RANG{range_index}:EVAL:STAR {start_freq}")
        self.write(f"CALC1:RANG{range_index}:EVAL:STOP {stop_freq}")

    def reset_integration_range_to_meas(self, range_index: int) -> None:
        """
        Resets the integration range to default full measurement range (MEAS).

        Parameters
        ----------
        range_index : int
            The index of the integration range to reset (1-10).
        """
        if range_index not in range(1, 11):
            raise ValueError("Invalid range index. Must be between 1 and 10.")
        self.write(f"CALC1:RANG{range_index}:EVAL:STAT ON")

    # =============================================================================
    # Spot Noise
    # =============================================================================

    def disable_spot_noise(self) -> None:
        """
        Turns off all spot noise information.
        Reference: R&S FSWP User Manual, Page 496.
        """
        self.write("CALC:SNO:AOFF")

    def set_decade_spot_noise(self, state: str, trace: int = 1, display: str = "ON"):
        """
        Enables or disables decade spot noise and assigns it to a trace.

        Parameters
        ----------
        state : str
            "ON" or "OFF".
        trace : int, optional
            Trace number (1-6). Default is 1.
        display : str, optional
            "ON" or "OFF".
        """
        state = self._parse_state(state)
        display = self._parse_state(display)
        self.write(f"CALC:SNO:DEC {state}")
        self.write(f"DISP:SNIN {display}")
        self.write(f"DISP:SNIN:TRAC {trace}")

    def set_manual_spot_noise(
        self, marker: int, offset: str, enable: str = "ON", display: str = "ON", trace: int = 1
    ):
        """
        Enables or disables a custom (manual) spot noise marker.

        Parameters
        ----------
        marker : int
            Spot noise marker index (1-6).
        offset : str
            Frequency offset with unit (e.g., "100kHz").
        enable : str, optional
            "ON" or "OFF".
        display : str, optional
            "ON" or "OFF".
        trace : int, optional
            Trace number (1-6).
        """
        self.write("CALC:SNO:USER ON")
        enable = self._parse_state(enable)
        display = self._parse_state(display)
        if enable == "ON":
            self.write(f"CALC:SNO{marker}:STAT ON")
            self.write(f"CALC:SNO{marker}:X {offset}")
        else:
            self.write(f"CALC:SNO{marker}:STAT OFF")

        self.write(f"DISP:SNIN {display}")
        self.write(f"DISP:SNIN:TRAC {trace}")

    # =============================================================================
    # Spurious
    # =============================================================================

    def enable_spur_removal(self, window: int = 1, trace: int = 1, state: int | str = 1) -> None:
        """
        Enables or disables spur removal for a specific trace.
        Reference: Page 500.
        """
        state = self._parse_state(state)
        self.write(f"DISP:WIND{window}:TRAC{trace}:SPUR:SUPP {state}")

    def set_spur_threshold(
        self,
        window: int = 1,
        trace: int = 1,
        threshold_dB: float = 10.0,  # noqa: N803
    ) -> None:
        """
        Sets the detection threshold for spur removal in dB.
        Reference: Page 500.
        """
        self.write(f"DISP:WIND{window}:TRAC{trace}:SPUR:THR {threshold_dB}")

    def set_spur_sort_order(self, order: str = "POWer") -> None:
        """
        Sets the sorting order of the spurs: "POWer" or "OFFSet".
        Reference: Page 501.
        """
        self.write(f"SPUR:SORT {order}")

    def set_spur_filter_mode(self, mode: str = "OFF") -> None:
        """
        Sets the spurious filter mode: OFF | SUPPress | SHOW.
        Reference: Page 177.
        """
        self.write("INST:SEL 'PNOISE'")
        self.write(f"SENS:SPUR:FILT:MODE {mode}")

    def get_spur_filter_mode(self) -> str:
        """
        Queries the current spur filter mode.
        """
        self.write("INST:SEL 'PNOISE'")
        return self.query("SENS:SPUR:FILT:MOD?")

    def set_spur_filter_harmonics(self, state: str | int = "OFF") -> None:
        """
        Sets whether harmonics are included in the spurious filter.
        """
        state = self._parse_state(state)
        self.write(f"SENS:SPUR:FILT:HARM {state}")

    def get_spur_filter_harmonics(self) -> str:
        """
        Queries whether harmonics are included in the spurious filter.
        """
        raw = self.query("SENS:SPUR:FILT:HARM?")
        return "ON" if raw.strip() in ["1", "ON"] else "OFF"

    def get_spur_filter_name(self) -> str:
        """
        Queries the name of the currently selected spurious filter.
        """
        return self.query("SENS:SPUR:FILT:NAME?")

    # =============================================================================
    # Aliases for backwards compatibility
    # =============================================================================

    @deprecated("Use 'get_center_frequency' instead")
    def ask_center_frequency(self, *args, **kwargs):
        """Deprecated alias for get_center_frequency()"""
        self.logger.warning(
            """Method 'ask_center_frequency()' is deprecated. 
            Please use 'get_center_frequency()' instead."""
        )
        return self.get_center_frequency(*args, **kwargs)

    @deprecated("Use 'get_center_frequency' instead")
    def ask_CenterFreq(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for get_center_frequency()"""
        self.logger.warning(
            "Method 'ask_CenterFreq()' is deprecated. Please use 'get_center_frequency()' instead."
        )
        return self.get_center_frequency(*args, **kwargs)

    @deprecated("Use 'set_center_frequency' instead")
    def set_CenterFreq(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for set_center_frequency()"""
        self.logger.warning(
            "Method 'set_CenterFreq()' is deprecated. Please use 'set_center_frequency()' instead."
        )
        return self.set_center_frequency(*args, **kwargs)

    @deprecated("Use 'set_start_frequency' instead")
    def set_freq_Start(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for set_start_frequency()"""
        self.logger.warning(
            "Method 'set_freq_Start()' is deprecated. Please use 'set_start_frequency()' instead."
        )
        return self.set_start_frequency(*args, **kwargs)

    @deprecated("Use 'get_start_frequency' instead")
    def ask_freq_Start(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for get_start_frequency()"""
        self.logger.warning(
            "Method 'ask_freq_Start()' is deprecated. Please use 'get_start_frequency()' instead."
        )
        return self.get_start_frequency(*args, **kwargs)

    @deprecated("Use 'set_stop_frequency' instead")
    def set_freq_Stop(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for set_stop_frequency()"""
        self.logger.warning(
            "Method 'set_freq_Stop()' is deprecated. Please use 'set_stop_frequency()' instead."
        )
        return self.set_stop_frequency(*args, **kwargs)

    @deprecated("Use 'get_stop_frequency' instead")
    def ask_freq_Stop(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for get_stop_frequency()"""
        self.logger.warning(
            "Method 'ask_freq_Stop()' is deprecated. Please use 'get_stop_frequency()' instead."
        )
        return self.get_stop_frequency(*args, **kwargs)

    @deprecated("Use 'set_span' instead")
    def set_FreqSpan(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for set_span()"""
        self.logger.warning(
            "Method 'set_FreqSpan()' is deprecated. Please use 'set_span()' instead."
        )
        return self.set_span(*args, **kwargs)

    @deprecated("Use 'get_span' instead")
    def ask_FreqSpan(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for get_span()"""
        self.logger.warning(
            "Method 'ask_FreqSpan()' is deprecated. Please use 'get_span()' instead."
        )
        return self.get_span(*args, **kwargs)

    @deprecated("Use 'set_resolution_bandwidth' instead")
    def set_ResBwidth(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for set_resolution_bandwidth()"""
        self.logger.warning(
            """Method 'set_ResBwidth()' is deprecated. 
            Please use 'set_resolution_bandwidth()' instead."""
        )
        return self.set_resolution_bandwidth(*args, **kwargs)

    @deprecated("Use 'get_resolution_bandwidth' instead")
    def ask_ResBwidth(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for get_resolution_bandwidth()"""
        self.logger.warning(
            """Method 'ask_ResBwidth()' is deprecated. 
            Please use 'get_resolution_bandwidth()' instead."""
        )
        return self.get_resolution_bandwidth(*args, **kwargs)

    @deprecated("Use 'get_rbw_pn' instead")
    def ask_rbw(self, *args, **kwargs):
        """Deprecated alias for get_rbw_pn()"""
        self.logger.warning("Method 'ask_rbw()' is deprecated. Please use 'get_rbw_pn()' instead.")
        return self.get_rbw_pn(*args, **kwargs)

    @deprecated("Use 'set_reference_level' instead")
    def set_RefLevel(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for set_reference_level()"""
        self.logger.warning(
            "Method 'set_RefLevel()' is deprecated. Please use 'set_reference_level()' instead."
        )
        return self.set_reference_level(*args, **kwargs)

    @deprecated("Use 'get_reference_level' instead")
    def ask_RefLevel(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for get_reference_level()"""
        self.logger.warning(
            "Method 'ask_RefLevel()' is deprecated. Please use 'get_reference_level()' instead."
        )
        return self.get_reference_level(*args, **kwargs)

    @deprecated("Use 'set_continuous' instead")
    def set_Continuous(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for set_continuous()"""
        self.logger.warning(
            "Method 'set_Continuous()' is deprecated. Please use 'set_continuous()' instead."
        )
        return self.set_continuous(*args, **kwargs)

    @deprecated("Use 'set_continuous' instead")
    def set_ContinuousMeas(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for set_continuous()"""
        self.logger.warning(
            "Method 'set_ContinuousMeas()' is deprecated. Please use 'set_continuous()' instead."
        )
        return self.set_continuous(*args, **kwargs)

    @deprecated("Use 'init' instead")
    def Init(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for init()"""
        self.logger.warning("Method 'Init()' is deprecated. Please use 'init()' instead.")
        return self.init(*args, **kwargs)

    @deprecated("Use 'set_sweep_points' instead")
    def set_DataPointCount(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for set_sweep_points()"""
        self.logger.warning(
            "Method 'set_DataPointCount()' is deprecated. Please use 'set_sweep_points()' instead."
        )
        return self.set_sweep_points(*args, **kwargs)

    @deprecated("Use 'get_sweep_points' instead")
    def ask_DataPointCount(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for get_sweep_points()"""
        self.logger.warning(
            "Method 'ask_DataPointCount()' is deprecated. Please use 'get_sweep_points()' instead."
        )
        return self.get_sweep_points(*args, **kwargs)

    @deprecated("Use 'set_trace_mode' instead")
    def set_TraceType(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for set_trace_mode()"""
        self.logger.warning(
            "Method 'set_TraceType()' is deprecated. Please use 'set_trace_mode()' instead."
        )
        return self.set_trace_mode(*args, **kwargs)

    @deprecated("Use 'set_trace_mode' instead")
    def set_trace_type(self, *args, **kwargs):
        """Deprecated alias for set_trace_mode()"""
        self.logger.warning(
            "Method 'set_trace_type()' is deprecated. Please use 'set_trace_mode()' instead."
        )
        return self.set_trace_mode(*args, **kwargs)

    @deprecated("Use 'set_detection_function' instead")
    def set_detector_type(self, *args, **kwargs):
        """Deprecated alias for set_detection_function()"""
        self.logger.warning(
            """Method 'set_detector_type()' is deprecated. 
            Please use 'set_detection_function()' instead."""
        )
        return self.set_detection_function(*args, **kwargs)

    @deprecated("Use 'set_detector_type' instead")
    def set_DetectorType(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for set_detector_type()"""
        self.logger.warning(
            "Method 'set_DetectorType()' is deprecated. Please use 'set_detector_type()' instead."
        )
        return self.set_detector_type(*args, **kwargs)

    @deprecated("Use 'get_trace_xy' instead")
    def get_phase_noise_data(self, *args, **kwargs):
        """Deprecated alias for get_trace_xy()"""
        self.logger.warning(
            "Method 'get_phase_noise_data()' is deprecated. Please use 'get_trace_xy()' instead."
        )
        return self.get_trace_xy(*args, **kwargs)

    @deprecated("Use 'measure_and_get_trace' instead")
    def ExtractTraceData(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for measure_and_get_trace()"""
        self.logger.warning(
            """Method 'ExtractTraceData()' is deprecated. 
            Please use 'measure_and_get_trace()' instead."""
        )
        return self.measure_and_get_trace(*args, **kwargs)

    @deprecated("Use 'get_start_offset' instead")
    def ask_start_offset(self, *args, **kwargs):
        """Deprecated alias for get_start_offset()"""
        self.logger.warning(
            "Method 'ask_start_offset()' is deprecated. Please use 'get_start_offset()' instead."
        )
        return self.get_start_offset(*args, **kwargs)

    @deprecated("Use 'get_stop_offset' instead")
    def ask_stop_offset(self, *args, **kwargs):
        """Deprecated alias for get_stop_offset()"""
        self.logger.warning(
            "Method 'ask_stop_offset()' is deprecated. Please use 'get_stop_offset()' instead."
        )
        return self.get_stop_offset(*args, **kwargs)

    @deprecated("Use 'get_spur_filter_mode' instead")
    def ask_spur_filter_mode(self, *args, **kwargs):
        """Deprecated alias for get_spur_filter_mode()"""
        self.logger.warning(
            """Method 'ask_spur_filter_mode()' is deprecated. 
            Please use 'get_spur_filter_mode()' instead."""
        )
        return self.get_spur_filter_mode(*args, **kwargs)

    @deprecated("Use 'create_channel' instead")
    def create_new_channel(self, *args, **kwargs):
        """Deprecated alias for create_channel()"""
        self.logger.warning(
            "Method 'create_new_channel()' is deprecated. Please use 'create_channel()' instead."
        )
        return self.create_channel(*args, **kwargs)
