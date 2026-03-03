"""
Created on Mon Aug  1 12:14:47 2022
The script is taken from https://github.com/uberdaff/kd3005p/blob/master/kd3005p.py
and heavily modified by:
@author: Martin.Mihaylov
@author: Maxim.Weizel

#  Copyright 2017 uberdaff
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#
# Requirement: pyvisa (migrated from pyserial)
#
# get_idn() - Get instrument identification
# set_volt(tal) - Set the voltage on the output
# get_volt() - Get the 'set' voltage
# read_volt() - Get a measurement of the voltage
# set_amp(tal) - Set the current limit
# get_amp() - Get the 'set' current limit
# read_amp() - Get a measurement of the output current
# set_out(bool) - Set the state of the output
# set_ocp(bool) - Set the state of the over current protection
# get_status() - Get the state of the output and CC/CV
"""

import time

import pyvisa
import pyvisa.constants

from .BaseInstrument import BaseInstrument

try:
    from typing import deprecated  # type: ignore
except ImportError:
    from typing_extensions import deprecated


class RD3005(BaseInstrument):
    def __init__(self, resource_str: str, visa_library: str = "@py", **kwargs):
        """
        Parameters
        ----------
        resource_str : str
            COM Port
        """
        # Let BaseInstrument handle the pyvisa connection.
        # We enforce serial settings required by RD3005 inline.
        kwargs.setdefault("baud_rate", 9600)
        kwargs.setdefault("data_bits", 8)
        kwargs.setdefault("parity", pyvisa.constants.Parity.none)
        kwargs.setdefault("stop_bits", pyvisa.constants.StopBits.one)
        kwargs.setdefault("read_termination", "")
        kwargs.setdefault("write_termination", "")
        super().__init__(resource_str, visa_library=visa_library, **kwargs)
        self.status = self.get_status()

    def query(self, command: str, delay: float = 0.05) -> str:
        """
        Send a query and return the response string.
        Override for Korad supplies to read buffer without termination characters.
        """
        self.write(command)
        time.sleep(delay)
        target_bytes = getattr(self._resource, "bytes_in_buffer", 0)
        if target_bytes > 0:
            return self._resource.read_bytes(target_bytes).decode().strip()
        raise TimeoutError(f"No response for command '{command}'")

    def _query_float(self, command: str, delay: float = 0.05) -> float:
        return float(self.query(command, delay))

    def get_idn(self) -> str:
        """
        Returns instrument identification.
        """
        return self.query("*IDN?", 0.3)

    def set_volt(self, voltage: float, delay: float = 0.01) -> None:
        """
        Parameters
        ----------
        voltage : int/float
            Set the voltage on the Display
        delay : float
            0.01s Delay
        """
        self.write(f"VSET1:{voltage:1.2f}")
        time.sleep(delay)

    def get_volt(self) -> float:
        """
        Returns the set voltage.
        """
        return self._query_float("VSET1?")

    def read_volt(self) -> float:
        """
        Returns the measured voltage.
        """
        return self._query_float("VOUT1?")

    def set_amp(self, amp: float, delay: float = 0.01) -> None:
        """
        Parameters
        ----------
        amp : int/float
            Set the current on the Display
        delay : float
            0.01s Delay
        """
        self.write(f"ISET1:{amp:1.3f}")
        time.sleep(delay)

    def get_amp(self) -> float:
        """
        Returns the set current.
        """
        return self._query_float("ISET1?")

    def read_amp(self) -> float:
        """
        Returns the measured current.
        """
        return self._query_float("IOUT1?")

    def set_out(self, state: str) -> None:
        """
        Parameters
        ----------
        state : str (ON/OFF)
            Turn Output ON and OFF
        """
        state_norm = self._parse_state(state)
        if state_norm == "ON":
            self.write("OUT1")
        elif state_norm == "OFF":
            self.write("OUT0")

    def set_ocp(self, state: str) -> None:
        """
        Parameters
        ----------
        state : str (ON/OFF)
            Set the state of the overcurrent protection ON and OFF
        """
        state_norm = self._parse_state(state)
        if state_norm == "ON":
            self.write("OCP1")
        elif state_norm == "OFF":
            self.write("OCP0")

    def get_status(self) -> dict[str, str]:
        """
        Returns a dictionary with the state of the output and CC/CV.
        """
        resp = self.query("STATUS?", 0.05)
        stat = ord(resp[0])
        self.status = {}
        if (stat & (1 << 0)) == 0:
            self.status["Mode"] = "CC"
        else:
            self.status["Mode"] = "CV"
        if (stat & (1 << 6)) == 0:
            self.status["Output"] = "Off"
        else:
            self.status["Output"] = "On"
        return self.status

    def get_data(self) -> dict[str, float]:
        """
        Returns a dictionary with the measured voltage and current.
        """
        output = {}
        voltage = self.read_volt()
        current = self.read_amp()
        output["Voltage/V"] = voltage
        output["Current/A"] = current

        return output

    # =============================================================================
    # Aliases for backward compatibility
    # =============================================================================

    @deprecated("Use 'set_volt' instead")
    def set_Volt(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for set_volt()"""
        self.logger.warning("Method 'set_Volt()' is deprecated. Please use 'set_volt()' instead.")
        return self.set_volt(*args, **kwargs)

    @deprecated("Use 'get_volt' instead")
    def ask_Volt(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for get_volt()"""
        self.logger.warning("Method 'ask_Volt()' is deprecated. Please use 'get_volt()' instead.")
        return self.get_volt(*args, **kwargs)

    @deprecated("Use 'read_volt' instead")
    def read_Volt(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for read_volt()"""
        self.logger.warning("Method 'read_Volt()' is deprecated. Please use 'read_volt()' instead.")
        return self.read_volt(*args, **kwargs)

    @deprecated("Use 'set_amp' instead")
    def set_Amp(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for set_amp()"""
        self.logger.warning("Method 'set_Amp()' is deprecated. Please use 'set_amp()' instead.")
        return self.set_amp(*args, **kwargs)

    @deprecated("Use 'get_amp' instead")
    def ask_Amp(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for get_amp()"""
        self.logger.warning("Method 'ask_Amp()' is deprecated. Please use 'get_amp()' instead.")
        return self.get_amp(*args, **kwargs)

    @deprecated("Use 'read_amp' instead")
    def read_Amp(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for read_amp()"""
        self.logger.warning("Method 'read_Amp()' is deprecated. Please use 'read_amp()' instead.")
        return self.read_amp(*args, **kwargs)

    @deprecated("Use 'set_out' instead")
    def set_Out(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for set_out()"""
        self.logger.warning("Method 'set_Out()' is deprecated. Please use 'set_out()' instead.")
        return self.set_out(*args, **kwargs)

    @deprecated("Use 'set_ocp' instead")
    def set_Ocp(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for set_ocp()"""
        self.logger.warning("Method 'set_Ocp()' is deprecated. Please use 'set_ocp()' instead.")
        return self.set_ocp(*args, **kwargs)

    @deprecated("Use 'get_status' instead")
    def ask_Status(self, *args, **kwargs):  # noqa: N802
        """Deprecated alias for get_status()"""
        self.logger.warning(
            "Method 'ask_Status()' is deprecated. Please use 'get_status()' instead."
        )
        return self.get_status(*args, **kwargs)
