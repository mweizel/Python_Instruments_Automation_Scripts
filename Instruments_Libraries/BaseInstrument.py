
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 27 2025

@author: Refactoring Bot
"""

import logging
from typing import List, cast, Any
import pyvisa
from pyvisa.resources import MessageBasedResource

class BaseInstrument:
    """
    Base class for all instrument drivers.
    Handles VISA connection, communication, logging, and error handling.
    """

    def __init__(self, resource_str: str, visa_library: str = "@py", **kwargs):
        """
        Initialize the instrument connection.

        Parameters
        ----------
        resource_str : str
            The VISA resource string (e.g., 'TCPIP::192.168.1.1::INSTR') or just an IP address.
        visa_library : str, optional
            VISA library to use (e.g., '@ivi', '@py'). Default is '@py'.
        **kwargs : dict
            Additional arguments passed to `open_resource`.
        """
        # Auto-format IP address if needed
        # We assume it's an IP address if no '::' is present AND it's not a Serial/COM port
        upper_res = resource_str.upper()
        if "::" not in resource_str and not upper_res.startswith("COM") and "ASRL" not in upper_res:
             resource_str = f"TCPIP::{resource_str}::INSTR"
        
        self.resource_str = resource_str
        self.logger = logging.getLogger(f"{self.__class__.__name__}({resource_str})")
        
        # Ensure a basic handler exists if none are configured
        if not self.logger.hasHandlers() and not logging.getLogger().handlers:
             logging.basicConfig(level=logging.INFO)

        try:
            self._rm = pyvisa.ResourceManager(visa_library)
            self._resource = cast(MessageBasedResource, self._rm.open_resource(resource_str, **kwargs))
            self.logger.info(f"Connected to {resource_str}")
        except Exception as e:
            self.logger.error(f"Failed to connect to {resource_str}: {e}")
            raise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # =============================================================================
    # Communication Wrappers
    # =============================================================================

    def write(self, command: str) -> None:
        """
        Send a command to the instrument.

        Parameters
        ----------
        command : str
            SCPI command string.
        """
        try:
            self.logger.debug(f"Write: {command}")
            self._resource.write(command)
        except Exception as e:
            self.logger.error(f"Write failed: '{command}', Error: {e}")
            raise

    def query(self, command: str) -> str:
        """
        Send a query and return the response string.

        Parameters
        ----------
        command : str
            SCPI query string.

        Returns
        -------
        str
            The instrument's response, stripped of whitespace.
        """
        try:
            self.logger.debug(f"Query: {command}")
            response = self._resource.query(command).strip()
            self.logger.debug(f"Response: {response}")
            return response
        except Exception as e:
            self.logger.error(f"Query failed: '{command}', Error: {e}")
            raise

    def read(self) -> str:
        """
        Read raw string from the instrument.

        Returns
        -------
        str
            Raw response from the instrument.
        """
        try:
            self.logger.debug("Reading from instrument...")
            response = self._resource.read()
            self.logger.debug(f"Read: {response.strip()}")
            return response
        except Exception as e:
            self.logger.error(f"Read failed: {e}")
            raise

    def query_ascii_values(self, command: str, **kwargs) -> List[Any]:
        """
        Query for a list of ASCII values (e.g., trace data).

        Parameters
        ----------
        command : str
            SCPI query command.
        **kwargs : dict
            Additional arguments passed to `query_ascii_values`.

        Returns
        -------
        list
            List of values.
        """
        try:
            self.logger.debug(f"Query ASCII: {command}")
            return cast(List[Any], self._resource.query_ascii_values(command, **kwargs))
        except Exception as e:
            self.logger.error(f"Query ASCII failed: '{command}', Error: {e}")
            raise

    def query_str_list(self, command: str) -> List[str]:
        """
        Query the instrument and return a list of strings.
        Automatically removes SCPI quotes (' or ") and strips whitespace.
        """
        response = self.query(command)
        if not response or response.upper() == "NONE":
            return []
        return [s.strip().strip("'").strip('"') for s in response.split(",")]

    def query_float(self, command: str) -> float:
        """
        Convenience method to query a single float value.

        Parameters
        ----------
        command : str
            SCPI query string.

        Returns
        -------
        float
            Parsed float value.
        """
        return float(self.query(command))

    def query_int(self, command: str) -> int:
        """
        Convenience method to query a single integer value.

        Parameters
        ----------
        command : str
            SCPI query string.

        Returns
        -------
        int
            Parsed integer value.
        """
        return int(float(self.query(command)))

    # =============================================================================
    # Common Instrument Commands
    # =============================================================================

    def get_idn(self) -> str:
        """
        Get the instrument identification string (*IDN?).

        Returns
        -------
        str
            Identification string.
        """
        return self.query("*IDN?")

    def reset(self) -> None:
        """
        Reset the instrument (*RST).
        """
        self.write("*RST")
        self.logger.info("Instrument reset (*RST)")

    def clear(self) -> None:
        """
        Clear the instrument status (*CLS).
        """
        self.write("*CLS")

    def get_opc(self) -> int:
        """
        Wait until operation complete (*OPC?).

        Returns
        -------
        int
            1 when operation is complete.
        """
        return self.query_int("*OPC?")

    def wait(self) -> None:
        """
        Wait for operation to complete (*WAI).
        """
        self.write("*WAI")

    def close(self) -> None:
        """
        Close the connection to the instrument.
        """
        try:
            if hasattr(self, '_resource'):
                self._resource.close()
            if hasattr(self, '_rm'):
                self._rm.close()
            self.logger.info(f"Connection to {self.resource_str} closed.")
        except Exception as e:
            self.logger.error(f"Error closing connection: {e}")

    # =============================================================================
    # Validate Variables
    # =============================================================================

    def _parse_state(self, state) -> str:
        """
        Helper to parse various input types into SCPI 'ON' or 'OFF' strings.
        Supports bool (True/False), numeric (1/0, 1.0/0.0), and strings ('ON'/'OFF', '1'/'0').
        """
        if isinstance(state, bool):
            return "ON" if state else "OFF"

        if isinstance(state, (int, float)):
            if state == 1:
                return "ON"
            elif state == 0:
                return "OFF"

        s = str(state).strip().upper()
        if s in ["ON", "1", "1.0"]:
            return "ON"
        elif s in ["OFF", "0", "0.0"]:
            return "OFF"
        else:
            raise ValueError(f"Invalid state: '{state}'. Use True/False, 1/0, or 'ON'/'OFF'.")

    # =============================================================================
    # Common aliases
    # =============================================================================

    Close = close
    idn = get_idn
    IDN = get_idn
    opc = get_opc
    OPC = get_opc
