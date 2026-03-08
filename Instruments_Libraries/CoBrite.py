"""
Created on Mon Feb 14 13:54:49 2022

@author: Martin.Mihaylov
"""

from .BaseInstrument import BaseInstrument

try:
    from typing import deprecated  # type: ignore
except ImportError:
    from typing_extensions import deprecated


class CoBrite(BaseInstrument):
    def __init__(self, resource_str: str, visa_library: str = "@py", **kwargs):
        """
        This Class is using PyVisa to connect to CoBrite Laser, please install PyVisa.
        """
        kwargs.setdefault("query_delay", 0.5)
        kwargs.setdefault("read_termination", "\n")
        super().__init__(str(resource_str), visa_library=visa_library, **kwargs)
        print(self.get_idn())

    def _validate_channel(self, channel: int | float | str) -> int:
        channel = int(float(channel))
        if channel not in [1, 2]:
            raise ValueError("Invalid channel number given! CoBrite has only 2 channels (1 or 2).")
        return channel

    # =============================================================================
    # Identify
    # =============================================================================

    def get_identification(self) -> str:
        """
        Identification name and model of the instrument.
        """
        return self.query("*IDN?")

    # =============================================================================
    # ASK
    # =============================================================================

    def get_freq_thz(self, chan: int) -> float:
        """
        Queries the wavelength setting of a tunable laser port.
        Value format is in THz.

        Parameters
        ----------
        chan : int
            Channel number. Can be 1 or 2. CoBrite have only 2 channels!

        Raises
        ------
        ValueError
            Error message.
        """
        chan = self._validate_channel(chan)

        freq = self.query(f"FREQ? 1,1,{chan}")
        return float(freq.split(";")[0])

    def get_wavelength(self, chan: int) -> float:
        """
        Queries the wavelength setting of a tunable laser port.
        Value format is in Nanometer.

        Parameters
        ----------
        chan : int
            Channel number. Can be 1 or 2. CoBrite have only 2 channels!

        Raises
        ------
        ValueError
            Error message.
        """
        chan = self._validate_channel(chan)

        wav = self.query(f"WAV? 1,1,{chan}")
        return float(wav.split(";")[0])

    def get_offset(self, chan: int) -> float:
        """
        Queries the frequency offset setting of a tunable laser port.
        Value format is in GHz.

        Parameters
        ----------
        chan : int
            Channel number. Can be 1 or 2. CoBrite have only 2 channels!

        Raises
        ------
        ValueError
            Error message.
        """
        chan = self._validate_channel(chan)

        freq = self.query(f"OFF? 1,1,{chan}")
        return float(freq.split(";")[0])

    def get_laser_output(self, chan: int) -> str:
        """
        Query if laser is ON or OFF.

        Parameters
        ----------
        chan : int
            Channel number. Can be 1 or 2. CoBrite have only 2 channels!

        Raises
        ------
        ValueError
            Error message.
        """
        chan = self._validate_channel(chan)

        out = float(self.query(f"STATe? 1,1,{chan}").split(";")[0])
        return "ON" if out != 0 else "OFF"

    def get_power(self, chan: int) -> float:
        """
        Queries the optical output power target setting of a tunable laser
        port. Value format is in dBm.

        Parameters
        ----------
        chan : int
            Channel number. Can be 1 or 2. CoBrite have only 2 channels!

        Raises
        ------
        ValueError
            Error message.
        """
        chan = self._validate_channel(chan)

        power = self.query(f"POW? 1,1,{chan}")
        return float(power.split(";")[0])

    def get_actual_power(self, chan: int) -> float:
        """
        Queries the current optical output power reading of a tunable laser
        port. Value format is in dBm.

        Parameters
        ----------
        chan : int
            Channel number. Can be 1 or 2. CoBrite have only 2 channels!

        Raises
        ------
        ValueError
            Error message.
        """
        chan = self._validate_channel(chan)

        apow = self.query(f"APOW? 1,1,{chan}")
        return float(apow.split(";")[0])

    def get_laser_lim(self, chan: int) -> dict[str, float]:
        """
        Query maximum tuning Parameters of Laser in location C-S-D in csv
        format.

        Parameters
        ----------
        chan : int
            Channel number. Can be 1 or 2. CoBrite have only 2 channels!

        Raises
        ------
        ValueError
            Error message.
        """
        chan = self._validate_channel(chan)

        lim = self.query(f"LIM? 1,1,{chan}")
        datasep = lim.split(";")[0].split(",")

        data_dict: dict[str, float] = {}
        labels = [
            "Minimum Frequency",
            "Maximum Frequency",
            "Fine tuning Range",
            "Minimum Power",
            "Maximum Power",
        ]
        for i in range(len(datasep)):
            data_dict[labels[i]] = float(datasep[i])
        return data_dict

    def get_configuration(self, chan: int) -> dict[str, float | str]:
        """
        Query current configuration of Laser in location C-S-D in csv format

        Parameters
        ----------
        chan : int
            Channel number. Can be 1 or 2. CoBrite have only 2 channels!.

        Raises
        ------
        ValueError
            Error message.
        """
        chan = self._validate_channel(chan)

        config = self.query(f":SOURce:CONFiguration? 1,1,{chan}")
        datasep = config.split(";")[0].split(",")
        if datasep[-1] == "-1":
            datasep[-1] = "NO"
        else:
            datasep[-1] = "YES"

        data_dict: dict[str, float | str] = {}
        labels = [
            "Wavelength",
            "Offset",
            "Output Power",
            "Output state",
            "Busy state",
            "Dither state",
        ]
        for i in range(int(len(datasep) - 1)):
            data_dict[labels[i]] = float(datasep[i])
        data_dict["Dither supported"] = datasep[-1]
        return data_dict

    # =============================================================================
    # SET
    # =============================================================================

    def set_power(self, chan: int, value: float) -> None:
        """
        Sets the optical output power target setting of a tunable laser port.
        Value format is in dBm.

        Parameters
        ----------
        chan : int
            Channel number. Can be 1 or 2. CoBrite have only 2 channels!.
        value : float
            Sets the optical output power target setting of a tunable laser port.
            Value format is in dBm.

        Raises
        ------
        ValueError
            Error message.
        """
        chan = self._validate_channel(chan)
        self.write(f"POW 1,1,{chan},{value}")

    def set_wavelength(self, chan: int, value: float) -> None:
        """
        Sets the wavelength setting of a tunable laser port. Value format
        is in Nanometer.

        Parameters
        ----------
        chan : int
            Channel number. Can be 1 or 2. CoBrite have only 2 channels!.
        value : float
            Sets the wavelength setting of a tunable laser port. Value format
            is in Nanometer.

        Raises
        ------
        ValueError
            Error message.
        """
        chan = self._validate_channel(chan)
        self.write(f"WAV 1,1,{chan},{value}")

    def set_freq_thz(self, chan: int, value: float) -> None:
        """
        Sets or queries the wavelength setting of a tunable laser port.
        Value format is in Tera Hertz.

        Parameters
        ----------
        chan : int
            Channel number. Can be 1 or 2. CoBrite have only 2 channels!.
        value : float
            Sets or queries the wavelength setting of a tunable laser port.
            Value format is in Tera Hertz.

        Raises
        ------
        ValueError
            Error message.
        """
        chan = self._validate_channel(chan)
        self.write(f"FREQ 1,1,{chan},{value}")

    def set_laser_output(self, chan: int, state: str | int) -> None:
        """
        Set if laser is ON or OFF.

        Parameters
        ----------
        chan : int
            Channel number. Can be 1 or 2. CoBrite have only 2 channels!.
        state : float/int
            Set if laser is ON or OFF. Can be integer 0 or 1, but can be a str
            ON and OFF.

        Raises
        ------
        ValueError
            Error message.
        """
        parsed_state = self._parse_state(state)
        state_val = "1" if parsed_state == "ON" else "0"

        chan = self._validate_channel(chan)
        self.write(f"STATe 1,1,{chan},{state_val}")

    def set_offset(self, chan: int, value: float) -> None:
        """
        Sets the frequency offset setting of a tunable laser port.
        Value format is in Giga Hertz.

        Parameters
        ----------
        chan : int
            Channel number. Can be 1 or 2. CoBrite have only 2 channels!.
        value : float
            Sets the frequency offset setting of a tunable laser port.
            Value format is in Giga Hertz.

        Raises
        ------
        ValueError
            Error message.
        """
        chan = self._validate_channel(chan)
        self.write(f"OFF 1,1,{chan},{value}")

    def set_configuration(self, chan: int, freq: float, power: float, offset: float) -> None:
        """
        Parameters
        ----------
        chan : int
            Channel number. Can be 1 or 2. CoBrite have only 2 channels!
        freq : float
            Sets frequency in Thz format. For example freq = 192.2345
        power : float
            Sets the power to dBm. For example power = 9.8.
            min Power = 8.8
            max Power = 17.8
            Check ask_LaserLim() for more info.
        offset : float
            Sets offset Freq in range Ghz.

        Raises
        ------
        ValueError
            Error message.
        """
        chan = self._validate_channel(chan)
        self.set_freq_thz(chan, freq)
        self.set_power(chan, power)
        self.set_offset(chan, offset)

    # =============================================================================
    # Aliases for backward compatibility
    # =============================================================================
    @deprecated("Use 'close' instead")
    def Close(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for close()"""
        self.logger.warning("Method 'Close()' is deprecated. Please use 'close()' instead.")
        return self.close(*args, **kwargs)

    @deprecated("Use 'get_identification' instead")
    def Identification(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for get_identification()"""
        self.logger.warning(
            "Method 'Identification()' is deprecated. Please use 'get_identification()' instead."
        )
        return self.get_identification(*args, **kwargs)

    @deprecated("Use 'get_freq_thz' instead")
    def ask_FreqTHz(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for get_freq_thz()"""
        self.logger.warning(
            "Method 'ask_FreqTHz()' is deprecated. Please use 'get_freq_thz()' instead."
        )
        return self.get_freq_thz(*args, **kwargs)

    @deprecated("Use 'get_wavelength' instead")
    def ask_Wavelength(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for get_wavelength()"""
        self.logger.warning(
            "Method 'ask_Wavelength()' is deprecated. Please use 'get_wavelength()' instead."
        )
        return self.get_wavelength(*args, **kwargs)

    @deprecated("Use 'get_offset' instead")
    def ask_Offset(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for get_offset()"""
        self.logger.warning(
            "Method 'ask_Offset()' is deprecated. Please use 'get_offset()' instead."
        )
        return self.get_offset(*args, **kwargs)

    @deprecated("Use 'get_laser_output' instead")
    def ask_LaserOutput(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for get_laser_output()"""
        self.logger.warning(
            "Method 'ask_LaserOutput()' is deprecated. Please use 'get_laser_output()' instead."
        )
        return self.get_laser_output(*args, **kwargs)

    @deprecated("Use 'get_power' instead")
    def ask_Power(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for get_power()"""
        self.logger.warning("Method 'ask_Power()' is deprecated. Please use 'get_power()' instead.")
        return self.get_power(*args, **kwargs)

    @deprecated("Use 'get_actual_power' instead")
    def ask_ActualPower(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for get_actual_power()"""
        self.logger.warning(
            "Method 'ask_ActualPower()' is deprecated. Please use 'get_actual_power()' instead."
        )
        return self.get_actual_power(*args, **kwargs)

    @deprecated("Use 'get_laser_lim' instead")
    def ask_LaserLim(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for get_laser_lim()"""
        self.logger.warning(
            "Method 'ask_LaserLim()' is deprecated. Please use 'get_laser_lim()' instead."
        )
        return self.get_laser_lim(*args, **kwargs)

    @deprecated("Use 'get_configuration' instead")
    def ask_Configuration(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for get_configuration()"""
        self.logger.warning(
            "Method 'ask_Configuration()' is deprecated. Please use 'get_configuration()' instead."
        )
        return self.get_configuration(*args, **kwargs)

    @deprecated("Use 'set_power' instead")
    def set_Power(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for set_power()"""
        self.logger.warning("Method 'set_Power()' is deprecated. Please use 'set_power()' instead.")
        return self.set_power(*args, **kwargs)

    @deprecated("Use 'set_wavelength' instead")
    def set_Wavelength(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for set_wavelength()"""
        self.logger.warning(
            "Method 'set_Wavelength()' is deprecated. Please use 'set_wavelength()' instead."
        )
        return self.set_wavelength(*args, **kwargs)

    @deprecated("Use 'set_freq_thz' instead")
    def set_FreqTHz(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for set_freq_thz()"""
        self.logger.warning(
            "Method 'set_FreqTHz()' is deprecated. Please use 'set_freq_thz()' instead."
        )
        return self.set_freq_thz(*args, **kwargs)

    @deprecated("Use 'set_laser_output' instead")
    def set_LaserOutput(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for set_laser_output()"""
        self.logger.warning(
            "Method 'set_LaserOutput()' is deprecated. Please use 'set_laser_output()' instead."
        )
        return self.set_laser_output(*args, **kwargs)

    @deprecated("Use 'set_offset' instead")
    def set_Offset(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for set_offset()"""
        self.logger.warning(
            "Method 'set_Offset()' is deprecated. Please use 'set_offset()' instead."
        )
        return self.set_offset(*args, **kwargs)

    @deprecated("Use 'set_configuration' instead")
    def set_Configuration(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for set_configuration()"""
        self.logger.warning(
            "Method 'set_Configuration()' is deprecated. Please use 'set_configuration()' instead."
        )
        return self.set_configuration(*args, **kwargs)
