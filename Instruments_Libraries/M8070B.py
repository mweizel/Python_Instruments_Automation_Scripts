"""
Created on Mon Jul  21 18:56:32 2025

@author: Maxim Weizel
"""

from typing import Any

import numpy as np

from .BaseInstrument import BaseInstrument

try:
    from typing import deprecated  # type: ignore
except ImportError:
    from typing_extensions import deprecated


# Try to import matlab engine
try:
    import matlab

    MATLAB_AVAILABLE = True
except (ImportError, ModuleNotFoundError) as e:
    MATLAB_AVAILABLE = False
    print("!" * 80)
    print("WARNING: MATLAB Engine for Python is not installed or not working correctly.")
    print("Generic functions will work, but IQTools-related functions will silently fail.")
    print("To install, use pip with the version matching your MATLAB installation:")
    print("  - R2024b: pip install matlabengine==24.2.*")
    print("  - R2025a: pip install matlabengine==25.1.*")
    print("  - R2025b: pip install matlabengine==25.2.*")
    print("  - Other : pip install matlabengine")
    print(f"Detailed Error: {e}")
    print("!" * 80)


class M8070B(BaseInstrument):
    """
    Start the M8070B Software. Go to Utilities-> SCPI Server Information.
    Copy the VISA resource string (usually localhost).
    """

    def __init__(
        self, resource_str="TCPIP0::localhost::hislip0::INSTR", visa_library="@py", **kwargs
    ):
        kwargs.setdefault("write_termination", "\n")
        kwargs.setdefault("timeout", 2000)  # 2s

        super().__init__(resource_str, visa_library=visa_library, **kwargs)
        self._channelLS = [1, 2]  #
        print(self.get_idn())

    # =============================================================================
    # Check functions
    # =============================================================================

    def validate_channel(self, channel: int) -> int:
        channel = int(channel)
        if channel not in self._channelLS:
            raise ValueError("Channel must be 1 or 2")
        return channel

    # =============================================================================
    # M8199B - Get Values and Modes
    # =============================================================================

    def get_amplitude(self, channel: int = 1) -> float:
        """Returns the differential amplitude setting for the selected channel in Volts.

        Parameters
        ----------
        channel : int, optional
            1 or 2, by default 1
        """
        channel = self.validate_channel(channel)
        return float(self.query(f":SOURce:VOLTage:AMPLitude? 'M2.DataOut{channel}'"))

    def get_output_state(self, channel: int) -> int:
        """Returns the output state (0 or 1) for the selected channel.

        Parameters
        ----------
        channel : int
            Channel 1 or 2
        """
        channel = self.validate_channel(channel)
        return int(self.query(f":OUTPut:STATe? 'M2.DataOut{channel}'"))

    def get_delay(self, channel: int) -> float:
        """Returns the delay for the selected channel in seconds.

        Parameters
        ----------
        channel : int
            Channel 1 or 2
        """
        channel = self.validate_channel(channel)
        return float(self.query(f":ARM:DELay? 'M2.DataOut{channel}'"))

    # =============================================================================
    # M8199B - Set Values and Modes
    # =============================================================================

    def set_amplitude(self, channel: int, amplitude: int | float) -> None:
        """Differential amplitude setting for the selected channel.

        Parameters
        ----------
        channel : int
            Channel 1 or 2
        amplitude : int/float
            Amplitude setting in V. Must be between 0.1 and 2.7 V
        """
        channel = self.validate_channel(channel)
        if 0.1 <= amplitude <= 2.7:
            self.write(f":SOURce:VOLTage:AMPLitude 'M2.DataOut{channel}', {amplitude}")
        else:
            raise ValueError(f"Value must be between 0.1 and 2.7 V. You entered: {amplitude} V")

    def set_rf_power(self, channel: int, power_dBm: int | float) -> None:  # noqa: N803
        """Sets the Signal Generator Output Power in dBm. Converts from dBm to V and
        uses ``set_amplitude()`` internally.

        Parameters
        ----------
        channel : int
            Channel 1 or 2
        power_dBm : int/float
            Output Power in dBm
        """
        power_watt = 10 ** (power_dBm / 10) * 1e-3
        v_rms = (50 * power_watt) ** 0.5  # 50 Ohm System
        amplitude = v_rms * np.sqrt(2)
        self.set_amplitude(channel, amplitude)

    def set_output_power_level(self, channel: int, power_dBm: int | float) -> None:  # noqa: N803
        """Sets the Signal Generator Output Power in dBm. Converts from dBm to V and
        uses ``set_amplitude()`` internally. Alias for set_rf_power().

        Parameters
        ----------
        channel : int
            Channel 1 or 2
        value : int/float
            Output Power in dBm
        """
        self.set_rf_power(channel, power_dBm)

    def set_output(self, channel: int, state: int | str) -> None:
        """Activate or deactivate the selected channel output.

        Parameters
        ----------
        channel : int
            Channel 1 or 2
        state : int | str
            One of: 0, 1, "off", "on"

        Raises
        ------
        ValueError
            Channel must be 1 or 2.
            State must be 0 or 1.
        """
        channel = self.validate_channel(channel)
        state_normalized = self._parse_state(state)
        self.write(f":OUTPut:STATe 'M2.DataOut{channel}', {state_normalized}")

    def set_rf_output(self, channel: int, state: int | str) -> None:
        """Activate or deactivate the selected channel output.
        Alias for set_output().
        """
        self.set_output(channel, state)

    def set_delay(self, channel: int, delay: float) -> None:
        """Set the delay for the selected channel in seconds.

        Parameters
        ----------
        channel : int
            Channel 1 or 2
        delay : float
            Delay in seconds.
        """
        channel = self.validate_channel(channel)
        if not (-25e-9 <= delay <= 25e-9):
            raise ValueError(f"Delay must be between -25 and 25ns. You entered: {delay} s")
        self.write(f":ARM:DELay 'M2.DataOut{channel}',{delay}")

    # =============================================================================
    # M8008A Clock Module - Get Values and Modes
    # =============================================================================

    def get_sample_clk_out_frequency(self, channel: int = 1) -> float:
        """Returns the sample clock OUT1 or OUT2 frequency from the M8008A CLK module.
        Both frequencies are the same (in Hz).

        Parameters
        ----------
        channel : int, optional
            1 or 2, by default 1
        """
        channel = self.validate_channel(channel)
        return float(self.query(f":OUTPut:FREQuency? 'M1.SampleClkOut{channel}'"))

    def get_sample_clk_out2_state(self) -> int:
        """Returns the sample clock OUT2 state (0 or 1) from the M8008A CLK module.
        Sample clock OUT1 cannot be turned off.
        """
        return int(self.query(":OUTPut:STATe? 'M1.SampleClkOut2'"))

    def get_sample_clk_out2_power(self) -> float:
        """Returns the sample clock OUT2 Power in dBm from the M8008A CLK module.
        Sample clock OUT1 cannot be influenced.
        """
        return float(self.query(":OUTPut:POWer? 'M1.SampleClkOut2'"))

    # =============================================================================
    # M8008A Clock Module - Set Values and Modes
    # =============================================================================

    def set_sample_clk_out2_state(self, state: int | str) -> None:
        """Sets the sample clock OUT2 state from the M8008A CLK module.
        Sample clock OUT1 cannot be turned off.

        Parameters
        ----------
        state : int | str
            One of: 0, 1, "off", "on"
        """
        state_normalized = self._parse_state(state)
        self.write(f":OUTPut:STATe 'M1.SampleClkOut2', {state_normalized}")

    def set_sample_clk_out2_power(self, power: int | float) -> None:
        """Sets the sample clock OUT2 Power in dBm from the M8008A CLK module.
        Sample clock OUT1 cannot be influenced.

        Parameters
        ----------
        power : int | float
            Sample Clock OUT2 Power in dBm.
            Must be between -5 and 12 dBm
        """
        if not (-5 <= power <= 12):
            raise ValueError(f"Power must be between -5 and 12 dBm. You entered: {power} dBm")
        self.write(f":SOURce:POWer 'M1.SampleClkOut2',{power}")

    # =============================================================================
    # M8199B Calling IQTools Functions
    # =============================================================================

    def set_freq_cw(
        self,
        matlab_engine,
        channel: int,
        frequency: float,
        correction: int = 0,
        run: int = 1,
        fs: float = 256e9,
    ) -> None:
        """Set the CW tone frequency on the AWG via MATLAB engine.

        Parameters
        ----------
        matlab_engine : matlab.engine
            An active MATLAB engine session.
        channel : int
            AWG channel (1 or 2).
        frequency : float
            Tone frequency in Hz.
        correction : int, optional
            Enable correction (default 0).
        run : int, optional
            AWG run number (default 1).
        fs : float, optional
            AWG sample rate (default 256e9).
        """
        # 1) Validate channel
        channel = self.validate_channel(channel)

        if not MATLAB_AVAILABLE:
            self.logger.warning("MATLAB not available. Skipping set_freq_CW.")
            return

        # 2) Define constants
        # magnitude is zeros(1,1) in MATLAB; make it a 1×1 double
        magnitude = matlab.double([[0]])  # in dB

        # fmt: off
        # 3) Build channelMapping
        # MATLAB expects numeric arrays, not raw Python lists
        if channel == 1:
            py_map = [[1, 0],
                    [0, 0]]
        else:
            py_map = [[0, 0],
                    [1, 0]]
        channel_mapping = matlab.double(py_map)

        # 4) Call iqtone to generate the IQ vector
        #    We ask for 5 outputs so that the last one is chMap.
        iqdata, _, _, _, chMap = matlab_engine.iqtone(  # noqa: N806
            'sampleRate',       fs,
            'numSamples',       0,
            'tone',             frequency,
            'phase',            'Random',
            'normalize',        1,
            'magnitude',        magnitude,
            'correction',       correction,
            'channelMapping',   channel_mapping,
            nargout=5
        )

        # 6) Push the generated IQ out to the AWG
        matlab_engine.iqdownload(
            iqdata,
            fs,
            'channelMapping', chMap,
            'segmentNumber',  1,
            'run',            run,
            nargout=0
        )
        # fmt: on

    def iqdownload(
        self,
        matlab_engine,
        iqdata,
        fs: float,
        *,
        segment_number: int = 1,
        normalize: bool = True,
        channel_mapping=None,
        sequence=None,
        marker=None,
        arb_config=None,
        keep_open: bool = False,
        run: bool = True,
        segment_length=None,
        segment_offset=None,
        lo_amplitude=None,
        lo_f_center=None,
        segm_name=None,
        rms=None,
    ) -> Any:
        """
        Download a pre-generated IQ waveform to the AWG.

        Parameters
        ----------
        matlab_engine : matlab.engine
            Active MATLAB engine session.
        iqdata : array-like
            Real or complex samples (each column = one waveform).
            Can be empty for a connection check.
        fs : float
            Sample rate in Hz.
        segment_number : int, optional
            Which segment to download into (default=1).
        normalize : bool, optional
            Auto-scale to DAC range (default=True).
        channel_mapping : array-like, optional
            2xM logical matrix mapping IQ data columns to AWG channels.
        sequence : any, optional
            Sequence table descriptor.
        marker : array-like of int, optional
            Marker bits per sample.
        arb_config : struct, optional
            AWG configuration struct (default from arbConfig file).
        keep_open : bool, optional
            If True, leave connection open after download (default=False).
        run : bool, optional
            If True, start AWG immediately after download (default=True).
        segment_length, segment_offset, lo_amplitude, lo_f_center, segm_name, rms :
            Other advanced options as per MATLAB doc.

        Returns
        -------
        result
            The output of the MATLAB `iqdownload` call (empty or status).
        """
        # fmt: off
        if not MATLAB_AVAILABLE:
            self.logger.warning("MATLAB not available. Skipping iqdownload.")
            return

        # Build the var/val list
        args = [
            'segmentNumber', int(segment_number),
            'normalize',   int(normalize),
            'keepOpen',    int(keep_open),
            'run',         int(run)
        ]
        # fmt: on
        if channel_mapping is not None:
            args += ["channelMapping", channel_mapping]
        if sequence is not None:
            args += ["sequence", sequence]
        if marker is not None:
            args += ["marker", marker]
        if arb_config is not None:
            args += ["arbConfig", arb_config]
        if segment_length is not None:
            args += ["segmentLength", segment_length]
        if segment_offset is not None:
            args += ["segmentOffset", segment_offset]
        if lo_amplitude is not None:
            args += ["loAmplitude", lo_amplitude]
        if lo_f_center is not None:
            args += ["loFcenter", lo_f_center]
        if segm_name is not None:
            args += ["segmName", segm_name]
        if rms is not None:
            args += ["rms", rms]

        # Call MATLAB
        result = matlab_engine.iqdownload(iqdata, fs, *args, nargout=1)
        return result

    def generate_multitone(
        self,
        matlab_engine,
        *,
        channel: int,
        tones: np.ndarray,
        magnitudes_dBm: np.ndarray | None = None,  # noqa: N803
        phases: np.ndarray | str = "Random",
        correction: int = 0,
        run: int = 1,
        fs: float = 256e9,
    ) -> None:
        """Set the CW tone frequency on the AWG via MATLAB engine.

        Parameters
        ----------
        matlab_engine : matlab.engine
            An active MATLAB engine session.
        channel : int
            AWG channel (1 or 2).
        tones : ndarray
            Tone frequency in Hz.
        magnitudes_dBm : ndarray, optional
            Tone magnitude in dBm (default None).
        correction : int, optional
            Enable correction (default 0).
        run : int, optional
            AWG run number (default 1).
        fs : float, optional
            AWG sample rate (default 256e9).
        """
        # 1) Validate channel
        channel = self.validate_channel(channel)

        if not MATLAB_AVAILABLE:
            self.logger.warning("MATLAB not available. Skipping generate_multitone.")
            return

        # 2) Prepare arrays
        frequency = np.asarray(tones, dtype=np.float64)  # 1-D
        if magnitudes_dBm is None:
            magnitudes_dBm = np.zeros_like(frequency, dtype=np.float64)  # dBm  # noqa: N806
        else:
            magnitudes_dBm = np.asarray(magnitudes_dBm, dtype=np.float64)  # noqa: N806

        # phase: either the literal 'Random' or a numeric vector
        if isinstance(phases, str):
            phase_arg = phases  # pass plain string to MATLAB
        else:
            phase_arg = np.asarray(phases, dtype=np.float64)
            # make column vectors if iqtone expects columns
            # phase_arg = matlab.double([[v] for v in phase_arr])

        # If iqtone wants column vectors for tone/magnitude too:
        # tone_arg      = matlab.double([[v] for v in frequency])
        # magnitude_arg = matlab.double([[v] for v in magnitudes_dB])

        # If iqtone wants row vectors for tone/magnitude too:
        tone_arg = frequency
        magnitude_arg = magnitudes_dBm

        # channelMapping already fine
        channel_mapping = matlab.double([[1, 0], [0, 0]] if channel == 1 else [[0, 0], [1, 0]])

        iqdata, _, _, _, chMap = matlab_engine.iqtone(  # noqa: N806
            "sampleRate",
            fs,
            "numSamples",
            0,
            "tone",
            tone_arg,  # explicit column vector
            "phase",
            phase_arg,  # string or column vector
            "normalize",
            1,
            "magnitude",
            magnitude_arg,  # explicit column vector
            "correction",
            correction,
            "channelMapping",
            channel_mapping,
            nargout=5,
        )

        # 6) Push the generated IQ out to the AWG
        matlab_engine.iqdownload(
            iqdata, fs, "channelMapping", chMap, "segmentNumber", 1, "run", run, nargout=0
        )

    # =============================================================================
    # Aliases for backward compatibility
    # =============================================================================
    @deprecated("Use 'close' instead")
    def Close(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for close()"""
        self.logger.warning("Method 'Close()' is deprecated. Please use 'close()' instead.")
        return self.close(*args, **kwargs)

    @deprecated("Use 'set_freq_cw' instead")
    def set_freq_CW(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for set_freq_cw()"""
        self.logger.warning(
            "Method 'set_freq_CW()' is deprecated. Please use 'set_freq_cw()' instead."
        )
        return self.set_freq_cw(*args, **kwargs)

    @deprecated("Use 'validate_channel' instead")
    def _validate_channel(self, *args, **kwargs):
        """Deprecated alias for validate_channel()"""
        self.logger.warning(
            "Method '_validate_channel()' is deprecated. Please use 'validate_channel()' instead."
        )
        return self.validate_channel(*args, **kwargs)

    @deprecated("Use 'set_output_power_level' instead")
    def set_OutputPowerLevel(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for set_output_power_level()"""
        self.logger.warning(
            """Method 'set_OutputPowerLevel()' is deprecated. 
            Please use 'set_output_power_level()' instead."""
        )
        return self.set_output_power_level(*args, **kwargs)
