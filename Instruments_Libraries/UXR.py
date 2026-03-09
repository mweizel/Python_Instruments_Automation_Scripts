"""
Created on Mon Dec  1 20:17:32 2024

@author: Maxim Weizel
"""

from datetime import datetime
from os.path import splitext
from typing import Any

import numpy as np

from .BaseInstrument import BaseInstrument


class UXR(BaseInstrument):
    """
    This class is using pyvisa to connect to Instruments. Please install PyVisa before using it.
    """

    def __init__(
        self,
        resource_str: str = "TCPIP0::KEYSIGH-Q75EBO9.local::hislip0::INSTR",
        visa_library: str = "@ivi",  # If you have problems try "@py"!
        num_channel: int = 2,
        **kwargs,
    ):
        kwargs.setdefault("read_termination", "\n")
        kwargs.setdefault("query_delay", 0.5)
        super().__init__(str(resource_str), visa_library=visa_library, **kwargs)
        print(self.get_idn())

        # Internal Variables and Predefined Lists
        self._types_channel = list(range(1, num_channel + 1))
        self._waveform_format = "ASC"

        # Default Settings
        self.system_header("off")  # Default is off and should stay off!!!
        self.waveform_byteorder("LSBFirst")
        self.waveform_format("WORD")  # Data Aquisition is only implemented for WORD yet.
        self.waveform_streaming("off")

    def query_binary_values(
        self,
        message: str,
        datatype: Any = "h",
        container: Any = np.array,
        data_points: int = 0,
        **kwargs,
    ) -> Any:
        return self._resource.query_binary_values(
            message,
            datatype=datatype,
            container=container,
            data_points=data_points,
            **kwargs,
        )

    # =============================================================================
    # Checks and Validations
    # =============================================================================

    def _validate_channel(self, channel: int) -> int:
        channel = int(float(channel))
        if channel not in self._types_channel:
            raise ValueError(
                f"Invalid channel number given! Channel Number can be one of {self._types_channel}."
            )
        return channel

    # =============================================================================
    # : (Root Level) Commands
    # =============================================================================
    def aquisition_done(self) -> int:
        """The :ADER? query reads the Acquisition Done Event Register and returns 1 or 0.
        After the Acquisition Done Event Register is read, the register is cleared. The
        returned value 1 indicates an acquisition completed event has occurred and 0
        indicates an acquisition completed event has not occurred.

        Returns
        -------
        int
            {1 | 0}
        """
        return int(self.query(":ADER?"))

    def aquisition_state(self) -> str:
        """The :ASTate? query returns the acquisition state.

        Returns
        -------
        str
            {ARM | TRIG | ATRIG | ADONE}
        """
        return self.query(":ASTate?")

    def autoscale(self) -> None:
        """The :AUToscale command causes the oscilloscope to evaluate all input waveforms
        and find the optimum conditions for displaying the waveform.
        """
        self.write(":AUToscale")

    def autoscale_channels(self, value: str | None = None) -> str | None:
        """The :AUToscale:CHANnels command selects whether to apply autoscale to all of
        the input channels or just the input channels that are currently displayed.

        Parameters
        ----------
        value : str, optional
            {ALL | DISPlayed}, if None then query

        Returns
        -------
        str
            {ALL | DISP}

        Raises
        ------
        ValueError
            Expected one of: {ALL | DISP | DISPlayed }
        """
        _types = ["ALL", "DISPlayed"]
        if value is not None:
            value = self._check_scpi_param(value, _types)
            self.write(f":AUToscale:CHANnels {value}")
        else:  # Query
            return self.query(":AUToscale:CHANnels?")

    def digitize(self, channel_num: int | None = None) -> None:
        """This command initializes the selected channels or functions, then acquires
        them according to the current oscilloscope settings. When all waveforms are
        completely acquired, the oscilloscope is stopped.
        To Do: input can be: [CHANnel<N> | DIFF<D> | COMMonmode<C>]

        Parameters
        ----------
        channel_num : int
            Number of the Channel

        Raises
        ------
        channel_numError
            Expected one of: channel number
        """
        if channel_num is not None:
            channel_num = self._validate_channel(channel_num)
            self.write(f":DIGitize CHANnel{channel_num}")
        else:
            self.write(":DIGitize")

    def run_state(self) -> str:
        """The :RSTate? query returns the run state:

        Returns
        -------
        str
            {RUN | STOP | SING}
        """
        return self.query(":RSTate?")

    def run(self) -> None:
        """
        Set the scope in run mode.
        """

        self.write(":RUN")

    def single(self) -> None:
        """
        Take a single acquisition
        """
        self.write(":SING")

    def status(self, key: str | None = None, value: int | None = None) -> int | None:
        """The :STATus? query shows whether the specified channel, function, wmemory,
        histogram, measurement trend, measurement spectrum, or equalized waveform is
        on or off.
        TODO: Each type has a different range of values that is excepted. No Checking
        is implemented.

        Parameters
        ----------
        key : str, optional
            if None return status of Channel1
        value : int, optional
            For Channel [1,2], for Function <=16

        Returns
        -------
        int
            A return value of 1 means on and a return value of 0 means off

        Raises
        ------
        ValueError
            Expected one of: CHANNEL, FUNCTION, HIST, ... etc.
        """
        _types_key = [
            "CHANnel",
            "DIFF",
            "COMMonmode",
            "FUNCtion",
            "HISTogram",
            "WMEMory",
            "CLOCkmtr",
            "MTRend",
            "MSPectrum",
            "EQUalized",
            "XT",
        ]
        if key is not None:
            key = self._check_scpi_param(key, _types_key)
            if value is not None and int(value) <= 16:  # For CHAN <=2, for FUNC <=16, ... etc.
                return int(self.query(f":STATus? {key}{value}"))
        else:
            return int(self.query(":STATus? CHANnel1"))

    def stop(self) -> None:
        """
        Set the scope in stop mode.
        """
        self.write(":STOP")

    # =============================================================================
    # :CHANnel<N> Commands
    # =============================================================================

    def channel_display(self, channel: int, state: int | str | None = None) -> int | None:
        """The :CHANnel<N>:DISPlay command turns the display of the specified channel on
        or off.

        Parameters
        ----------
        channel : int
            An integer, analog input channel 1 or 2
        state : int, str, optional
            ON, 1, OFF, 0


        Returns
        -------
        int
            The :CHANnel<N>:DISPlay? query returns the current display condition for the
            specified channel
        """
        channel = self._validate_channel(channel)
        if state is not None:
            state = self._parse_state(state)
            self.write(f":CHANnel{channel}:DISPlay {state}")
        else:  # query
            return int(self.query(f":CHANnel{channel}:DISPlay?"))

    def channel_range(self, channel: int, range_value: float | None = None) -> float | None:
        """The :CHANnel<N>:RANGe command defines the full-scale vertical axis of the
        selected channel. The values represent the full-scale deflection factor of the
        vertical axis in volts. These values change as the probe attenuation factor is changed.

        Parameters
        ----------
        channel : int
            An integer, analog input channel 1 or 2
        range_value : float, optional
            A real number for the full-scale voltage of the specified channel number,
            by default None

        Returns
        -------
        float
            full-scale vertical axis of the selected channel

        Raises
        ------
        ValueError
            For Channel expected one of: num_channels
        ValueError
            For range_value expected to be < 2V
        """
        channel = self._validate_channel(channel)
        if range_value is not None:
            if range_value <= 4:  # 2V Full Scale Range
                self.write(f":CHANnel{channel}:RANGe {range_value}")
            else:
                raise ValueError("Invalid Argument. Expected to be <= 4V")
        else:  # query
            return float(self.query(f":CHANnel{channel}:RANGe?"))

    def channel_scale(self, channel: int, scale_value: float | None = None) -> float | None:
        """The :CHANnel<N>:SCALe command sets the vertical scale, or units per division, of
        the selected channel. This command is the same as the front-panel channel scale.

        Parameters
        ----------
        channel : int
            An integer, analog input channel 1 or 2
        scale_value : float, optional
            A real number for the vertical scale of the channel in units per division,
            by default None

        Returns
        -------
        float
            A real number for the vertical scale of the channel in units per division

        Raises
        ------
        ValueError
            For Channel expected one of: num_channels
        ValueError
            For range_value expected to be < 500mV/div
        """
        channel = self._validate_channel(channel)
        if scale_value is not None:
            if scale_value <= 0.5:  # 500mV/div Scale
                self.write(f":CHANnel{channel}:SCALe {scale_value}")
            else:
                raise ValueError("Invalid Argument. Expected to be <= 500mV/div")
        else:  # query
            return float(self.query(f":CHANnel{channel}:SCALe?"))

    # =============================================================================
    # :DISPlay Commands
    # =============================================================================

    def screenshot(
        self,
        path: str = "./screenshot.png",
        with_time: bool = True,
        time_fmt: str = "%Y-%m-%d_%H-%M-%S",
        divider: str = "_",
        timeout: float = 5000,
    ):
        """Save screen to {path} with {image_type}: bmp, jpg, gif, tif, png
        Adapted from:
        https://github.com/microsoft/Qcodes/blob/main/src/qcodes/instrument_drivers/Keysight/Infiniium.py
        """

        time_str = datetime.now().strftime(time_fmt) if with_time else ""
        img_name, img_type = splitext(path)
        img_path = f"{img_name}{divider if with_time else ''}{time_str}{img_type.lower()}"

        old_timeout = self._resource.timeout  # save current timeout
        self._resource.timeout = timeout  # 5 seconds in milliseconds
        try:
            with open(img_path, "wb") as f:
                screen_bytes = self.query_binary_values(
                    f":DISPlay:DATA? {img_type.upper()[1:]}",  # without .
                    # https://docs.python.org/3/library/struct.html#format-characters
                    datatype="B",  # Capitcal B for unsigned byte
                    container=bytes,
                )
                f.write(screen_bytes)
            print(f"Screen image written to {img_path}")
        except Exception as e:
            self._resource.timeout = old_timeout  # restore original timeout
            print(f"Failed to save screenshot, Error occurred: \n{e}")
        finally:
            self._resource.timeout = old_timeout  # restore original timeout

    # =============================================================================
    # :FUNCtion Commands
    # =============================================================================

    def function_display(self, function_num: int, state: int | str | None = None) -> int | None:
        """The :FUNCtion<N>:DISPlay command turns the display of the specified function_num on
        or off.

        Parameters
        ----------
        function_num : int
            Function Number
        state : int, str, optional
            ON, 1, OFF, 0


        Returns
        -------
        int
            The :FUNCtion<N>:DISPlay? query returns the current display condition for the
            specified function_num

        Raises
        ------
        ValueError
            For function_num expected one of: 1-16
        """
        if int(function_num) < 1 or int(function_num) > 16:
            raise ValueError("Invalid Argument. Expected one of: 1-16")
        if state is not None:
            state = self._parse_state(state)
            self.write(f":FUNCtion{function_num}:DISPlay {state}")
        else:  # query
            return int(self.query(f":FUNCtion{function_num}:DISPlay?"))

    # =============================================================================
    # :SYSTem Commands
    # =============================================================================

    def system_header(self, state: int | str | None = None) -> int | None:
        """!!!! SHOULD BE OFF !!!!
        The :SYSTem:HEADer command specifies whether the instrument will output a
        header for query responses. When :SYSTem:HEADer is set to ON, the query
        responses include the command header.

        Parameters
        ----------
        state : int | str | None, optional
            {{ON | 1} | {OFF | 0}}, by default None

        Returns
        -------
        int
            {1 | 0}

        Raises
        ------
        ValueError
            Expected one of: {{ON | 1} | {OFF | 0}}
        """
        if state is not None:
            state = self._parse_state(state)
            self.write(f":SYSTem:HEADer {state}")
        else:  # query
            return int(self.query(":SYSTem:HEADer?"))

    # =============================================================================
    # :WAVeform Commands
    # =============================================================================

    def waveform_byteorder(self, value: str | None = "LSBFIRST") -> str | None:
        """The :WAVeform:BYTeorder command selects the order in which bytes are
        transferred from (or to) the oscilloscope using WORD and LONG formats

        Parameters
        ----------
        value : str, optional
            byteorder {MSBF, LSBF}, by default LSBFIRST

        Returns
        -------
        str
            byteorder {MSBF, LSBF}

        Raises
        ------
        ValueError
            Expected one of: MSBFIRST, LSBFIRST
        """
        _types = ["MSBFirst", "LSBFirst"]
        if value is not None:
            value = self._check_scpi_param(value, _types)
            self.write(f":WAVeform:BYTeorder {value}")
        else:  # Query
            return self.query(":WAVeform:BYTeorder?")

    def waveform_data(
        self,
        start: int | None = None,
        size: int | None = None,
        datatype: str = "h",
        container: Any = np.array,
        data_points: int = 0,
        **kwargs,
    ) -> Any:
        """
        The :WAVeform:DATA? query outputs waveform data to the computer over the
        remote interface. The data is copied from a waveform memory, function, or
        channel previously specified with the :WAVeform:SOURce command.

        Parameters
        ----------
        start : int, optional
            Starting point in the source memory for the first waveform point to transfer,
            by default None.
        size : int, optional
            Number of points in the source memory to transfer. If larger than available data,
            size is adjusted to the maximum available, by default None.
        datatype : str, optional
            Data type for binary values as defined in Python struct, by default "h" (short).
        container : type, optional
            Type of container to hold the data, by default np.array.
        data_points : int, optional
            Expected number of data points, by default 0.
        kwargs : dict, optional
            Additional arguments passed to the query_binary_values method.

        Returns
        -------
        np.ndarray
            Acquired data.

        Raises
        ------
        ValueError
            If `start` or `size` are invalid (non-integers or negative).
        NotImplementedError
            If the waveform format is not "WORD".
        """
        # Validate start and size
        if start is not None and (not isinstance(start, int) or start < 0):
            raise ValueError("`start` must be a non-negative integer.")
        if size is not None and (not isinstance(size, int) or size < 0):
            raise ValueError("`size` must be a non-negative integer.")

        # Construct the SCPI message
        if start is not None and size is not None:
            message = f":WAVeform:DATA? {start},{size}"
        elif start is not None:
            message = f":WAVeform:DATA? {start}"
        else:
            message = ":WAVeform:DATA?"

        # Query the waveform data
        if self._waveform_format == "WORD":
            try:
                return self.query_binary_values(
                    message,
                    datatype=datatype,
                    container=container,
                    data_points=data_points,
                    **kwargs,
                )
            except Exception as e:
                print("Error:", e)

        else:
            raise NotImplementedError(
                f"Unsupported waveform format: {self._waveform_format}. "
                "Only 'WORD' format is currently supported."
            )

    def waveform_format(self, value: str | None = None) -> str | None:
        """The :WAVeform:FORMat command sets the data transmission mode for waveform
        data output. This command controls how the data is formatted when it is sent from
        the oscilloscope, and pertains to all waveforms.
        To Do: Only WORD is tested. There is a FLOAT type?

        Parameters
        ----------
        value : str, optional
            One of {ASCii | BINary | BYTE | WORD }, by default None

        Returns
        -------
        str
            {ASC | BIN | BYTE | WORD }

        Raises
        ------
        ValueError
            Expected one of: {ASCii | BINary | BYTE | WORD}
        """
        _types = ["ASCii", "BINary", "BYTE", "WORD"]
        if value is not None:
            value = self._check_scpi_param(value, _types)
            self.write(f":WAVeform:FORMat {value}")
            self._waveform_format = self.query(":WAVeform:FORMat?").upper()
        else:  # Query
            self._waveform_format = self.query(":WAVeform:FORMat?").upper()
            return self._waveform_format

    def waveform_points(self) -> int:
        """The :WAVeform:POINts? query returns the points value in the current waveform
        preamble.

        Returns
        -------
        int
            Number of points in the current waveform
        """
        return int(self.query(":WAVeform:POINts?"))

    def waveform_source(self, key: str | None = None, value: int | None = None) -> str | None:
        """The :WAVeform:SOURce command selects a channel, function, waveform
        memory, or histogram as the waveform source
        TODO: No checks implemented

        Parameters
        ----------
        key : str | None, optional
            One of: {CHANnel<N> | DIFF<D> | COMMonmode<C> | FUNCtion<F> | HISTogram |
            WMEMory<R> | CLOCk | MTRend | MSPectrum | EQUalized | XT<X> | PNOise |
            INPut | CORRected | ERRor | LFPR | NREDuced}, by default None
        value : int | None, optional
            Number e.g. 1 for Channel1, by default None

        Returns
        -------
        str
            The :WAVeform:SOURce? query returns the currently selected waveform source.
        """
        if key is not None and value is not None:
            self.write(f":WAVeform:SOURce {key}{value}")
        else:
            return self.query(":WAVeform:SOURce?")

    def waveform_streaming(self, state: int | str | None = None) -> int | None:
        """When enabled, :WAVeform:STReaming allows more than 999,999,999 bytes of
        data to be transferred from the Infiniium oscilloscope to a PC when using the
        :WAVeform:DATA? query.

        Parameters
        ----------
        state : int | str | None, optional
            {{ON | 1} | {OFF | 0}}, by default None

        Returns
        -------
        int
            {1 | 0}
        """
        if state is not None:
            state = self._parse_state(state)
            self.write(f":WAVeform:STReaming {state}")
        else:  # query
            return int(self.query(":WAVeform:STReaming?"))

    def waveform_x_increment(self) -> float:
        """The :WAVeform:XINCrement? query returns the duration between consecutive
        data points for the currently specified waveform source.

        Returns
        -------
        float
            A real number representing the duration between data points on the X axis.
        """
        return float(self.query(":WAVeform:XINCrement?"))

    def waveform_x_origin(self) -> float:
        """The :WAVeform:XORigin? query returns the X-axis value of the first data point in
        the data record.

        Returns
        -------
        float
            A real number representing the X-axis value of the first data point in the data
            record.
        """
        return float(self.query(":WAVeform:XORigin?"))

    def waveform_y_increment(self) -> float:
        """The :WAVeform:YINCrement? query returns the y-increment voltage value for the
        currently specified source.

        Returns
        -------
        float
            A real number in exponential format.
        """
        return float(self.query(":WAVeform:YINCrement?"))

    def waveform_y_origin(self) -> float:
        """The :WAVeform:YORigin? query returns the y-origin voltage value for the currently
        specified source. The voltage value returned is the voltage value represented by
        the waveform data digital code 00000.

        Returns
        -------
        float
            A real number in exponential format.
        """
        return float(self.query(":WAVeform:YORigin?"))
