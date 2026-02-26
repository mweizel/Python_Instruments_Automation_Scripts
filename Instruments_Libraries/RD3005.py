# -*- coding: utf-8 -*-
"""
Created on Mon Aug  1 12:14:47 2022

@author: Martin.Mihaylov 
"""

'''
The script is take https://github.com/uberdaff/kd3005p/blob/master/kd3005p.py
and cosmetically preprocessed.
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
'''

import time
import pyvisa
import pyvisa.constants
from typing import Dict, Any, Optional
from .BaseInstrument import BaseInstrument

class RD3005(BaseInstrument):
    
    def __init__(self, resource_str: str, visa_library: str = '@py', **kwargs):
        '''
        Parameters
        ----------
        resource_str : str
            COM Port
        '''
        # Let BaseInstrument handle the pyvisa connection.
        # We enforce serial settings required by RD3005 inline.
        try:
            kwargs.setdefault('baud_rate', 9600)
            kwargs.setdefault('data_bits', 8)
            kwargs.setdefault('parity', pyvisa.constants.Parity.none)
            kwargs.setdefault('stop_bits', pyvisa.constants.StopBits.one)
            kwargs.setdefault('read_termination', "")
            kwargs.setdefault('write_termination', "")
            super().__init__(
                resource_str,
                visa_library=visa_library,
                **kwargs
            )
            self.status: Dict[str, str] = {}
            self.status = self.get_status()
        except pyvisa.errors.VisaIOError as e:
            print("COM port failure:")
            print(e)
    
    def serWriteAndRecieve(self, data: str, delay: float = 0.05) -> Optional[str]: 
        self._resource.write_raw(data.encode())
        time.sleep(delay)
        
        # PyVISA backends provide bytes_in_buffer for Serial/USB profiles.
        target_bytes = getattr(self._resource, 'bytes_in_buffer', 0)
        if target_bytes > 0:
            out = self._resource.read_bytes(target_bytes).decode()
            if out != '':
                return out
        return None

    def _query_local(self, command: str, delay: float = 0.05) -> str:
        resp = self.serWriteAndRecieve(command, delay)
        if resp is None:
            raise TimeoutError(f"No response for command '{command}'")
        return resp

    def _query_float(self, command: str, delay: float = 0.05) -> float:
        return float(self._query_local(command, delay))
    
    def get_idn(self) -> str:
        '''
        Returns
        -------
        str
            Instrument identification 
        '''
        return self._query_local("*IDN?", 0.3)
    
    def set_volt(self, voltage: float, delay: float = 0.01) -> None:
        '''
        Parameters
        ----------
        voltage : int/float
            Set the voltage on the Display
        delay : float
            0.01s Delay 
        '''
        self.serWriteAndRecieve("VSET1:"+"{:1.2f}".format(voltage))
        time.sleep(delay) 
    
    def get_volt(self) -> float:
        '''
        Returns
        -------
        float
            Voltage set.
        '''
        return self._query_float("VSET1?")
    
    def read_volt(self) -> float:
        '''
        Returns
        -------
        float
            Voltage Measured
        '''
        return self._query_float("VOUT1?")
    
    
    def set_amp(self, amp: float, delay: float = 0.01) -> None:
        '''
        Parameters
        ----------
        amp : int/float
            Set the current on the Display
        delay : float
            0.01s Delay 
        '''
        self.serWriteAndRecieve("ISET1:"+"{:1.3f}".format(amp))
        time.sleep(delay) 
    
    def get_amp(self) -> float:
        '''
        Returns
        -------
        float
            current set.
        '''
        return self._query_float("ISET1?")
    
    def read_amp(self) -> float:
        '''
        Returns
        -------
        float
            Current Measured
        '''
        return self._query_float("IOUT1?")
    
    def set_out(self, state: str) -> None:
        '''
        Parameters
        ----------
        state : str (ON/OFF)
            Turn Output ON and OFF
        '''
        state_norm = self._parse_state(state)
        if state_norm == "ON":
            self.serWriteAndRecieve("OUT1")
        elif state_norm == "OFF":
            self.serWriteAndRecieve("OUT0")
    
    def set_ocp(self, state: str) -> None:
        '''
        Parameters
        ----------
        state : str (ON/OFF)
            Set the state of the overcurrent protection ON and OFF
        '''
        state_norm = self._parse_state(state)
        if state_norm == "ON":
            self.serWriteAndRecieve("OCP1")
        elif state_norm == "OFF":
            self.serWriteAndRecieve("OCP0")
    
    def get_status(self) -> Dict[str, str]:
        '''
        Returns
        -------
        dict
            Get the state of the output and CC/CV
        '''
        resp = self._query_local("STATUS?")
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

    def get_data(self) -> Dict[str, float]:
        '''
        Returns
        -------
        OutPut : dict
            Return a dictionary with the measured voltage and current.
        '''
        OutPut = {}
        Voltage = self.read_volt()
        Current = self.read_amp()
        OutPut['Voltage/V'] = Voltage
        OutPut['Current/A'] = Current
        
        return OutPut

    # =============================================================================
    # Aliases for backward compatibility
    # =============================================================================
    getIdn = get_idn
    set_Volt = set_volt
    ask_Volt = get_volt
    read_Volt = read_volt
    set_Amp = set_amp
    ask_Amp = get_amp
    read_Amp = read_amp
    set_Out = set_out
    set_Ocp = set_ocp
    ask_Status = get_status
