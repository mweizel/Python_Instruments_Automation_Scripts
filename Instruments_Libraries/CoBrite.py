# -*- coding: utf-8 -*-
"""
Created on Mon Feb 14 13:54:49 2022

@author: Martin.Mihaylov
"""

import numpy as np
import pyvisa as visa
from typing import Dict, Union
from .BaseInstrument import BaseInstrument

    
class CoBrite(BaseInstrument):
    def __init__(self, resource_str: str, visa_library: str = '@py', **kwargs):
        '''
        This Class is using PyVisa to connect to CoBrite Laser, please install PyVisa and Numpy first!
        '''
        kwargs.setdefault('query_delay', 0.5)
        super().__init__(str(resource_str), visa_library=visa_library, **kwargs)
        print(self.get_idn())
        
    def read(self) -> bytes:  # type: ignore[override]
        '''
        Returns
        -------
        None
            This function must be set after each set_() function. CoBrite 
            writes the set_() to register and returns ;/r/n to the user. The
            ;/r/n command will mess up the next data sent to CoBrite from the user.
            An empty read() is required to be sended after each set_() function to the
            laser. 
        '''
        return self._resource.read_raw()
        
# =============================================================================
# Identify       
# =============================================================================

    def get_identification(self) -> str:
        '''
        Returns
        -------
        float
            Identification name and model of the instrument. 
        '''
        return self.query('*IDN?')

# =============================================================================
# ASK 
# =============================================================================
    
    def get_freq_thz(self, chan: int) -> float:
        '''
        Parameters
        ----------
        chan : int
            Channel number. Can be 1 or 2. CoBrite have only 2 channels!

        Raises
        ------
        ValueError
            Error message.

        Returns
        -------
        float
            Queries the wavelength setting of a tunable laser port.
            Value format is in THz.
        '''
        if chan not in [1, 2]:
            raise ValueError('Unknown input! See function description for more info.') 
        
        freq = self.query(f'FREQ? 1,1,{chan}')
        return float(freq.split(';')[0])
    
    def get_wavelength(self, chan: int) -> float:
        '''
        Parameters
        ----------
        chan : int
            Channel number. Can be 1 or 2. CoBrite have only 2 channels!

        Raises
        ------
        ValueError
            Error message.

        Returns
        -------
        float
            Queries the wavelength setting of a tunable laser port. 
            Value format is in Nanometer.
        '''
        if chan not in [1, 2]:
            raise ValueError('Unknown input! See function description for more info.') 
        
        wav = self.query(f'WAV? 1,1,{chan}')
        return float(wav.split(';')[0])

    def get_offset(self, chan: int) -> float:
        '''
        Parameters
        ----------
        chan : int
            Channel number. Can be 1 or 2. CoBrite have only 2 channels!

        Raises
        ------
        ValueError
            Error message.

        Returns
        -------
        float
            Queries the frequency offset setting of a tunable laser port. 
            Value format is in GHz.
        '''
        if chan not in [1, 2]:
            raise ValueError('Unknown input! See function description for more info.') 
        
        freq = self.query(f'OFF? 1,1,{chan}')
        return float(freq.split(';')[0])

    def get_laser_output(self, chan: int) -> str:
        '''
        Parameters
        ----------
        chan : int
            Channel number. Can be 1 or 2. CoBrite have only 2 channels!

        Raises
        ------
        ValueError
            Error message.

        Returns
        -------
        str
            Query if laser is ON or OFF. 
        '''
        if chan not in [1, 2]:
            raise ValueError('Unknown input! See function description for more info.') 
        
        out = float(self.query(f'STATe? 1,1,{chan}').split(';')[0])
        return 'ON' if out != 0 else 'OFF'
        
    def get_power(self, chan: int) -> float:
        '''
        Parameters
        ----------
        chan : int
            Channel number. Can be 1 or 2. CoBrite have only 2 channels!

        Raises
        ------
        ValueError
            Error message.

        Returns
        -------
        float
            Queries the optical output power target setting of a tunable laser
            port. Value format is in dBm.
        '''
        if chan not in [1, 2]:
            raise ValueError('Unknown input! See function description for more info.') 
        
        power = self.query(f'POW? 1,1,{chan}')
        return float(power.split(';')[0])
    
    def get_actual_power(self, chan: int) -> float:
        '''
        Parameters
        ----------
        chan : int
            Channel number. Can be 1 or 2. CoBrite have only 2 channels!

        Raises
        ------
        ValueError
            Error message.

        Returns
        -------
        float
            Queries the current optical output power reading of a tunable laser
            port. Value format is in dBm.
        '''
        if chan not in [1, 2]:
            raise ValueError('Unknown input! See function description for more info.') 
        
        apow = self.query(f'APOW? 1,1,{chan}')
        return float(apow.split(';')[0])

    def get_laser_lim(self, chan: int) -> Dict[str, float]:
        '''
        Parameters
        ----------
        chan : int
            Channel number. Can be 1 or 2. CoBrite have only 2 channels!

        Raises
        ------
        ValueError
            Error message.

        Returns
        -------
        DataDic : dictionary
            Query maximum tuning Parameters of Laser in location C-S-D in csv 
            format.
        '''
        if chan not in [1, 2]:
            raise ValueError('Unknown input! See function description for more info.') 
        
        lim = self.query(f'LIM? 1,1,{chan}')
        datasep = lim.split(';')[0].split(',')
        
        DataDic: Dict[str, float] = {}
        labels = ['Minimum Frequency','Maximum Frequency','Fine tuning Range','Minimum Power','Maximum Power']
        for i in range(len(datasep)):
            DataDic[labels[i]] = float(datasep[i])
        return DataDic
    
    def get_configuration(self, chan: int) -> Dict[str, Union[float, str]]:
        '''
        Parameters
        ----------
        chan : int
            Channel number. Can be 1 or 2. CoBrite have only 2 channels!.

        Raises
        ------
        ValueError
            Error message.

        Returns
        -------
        DataDic : dictionary
            Query current configuration of Laser in location C-S-D in csv format
        '''
        if chan not in [1, 2]:
            raise ValueError('Unknown input! See function description for more info.') 
        
        config = self.query(f':SOURce:CONFiguration? 1,1,{chan}')
        datasep = config.split(';')[0].split(',')
        if datasep[-1] == '-1':  
            datasep[-1] = 'NO'
        else:
            datasep[-1] = 'YES'
            
        DataDic: Dict[str, Union[float, str]] = {}
        labels = ['Wavelength','Offset','Output Power','Output state','Busy state','Dither state']
        for i in range(int(len(datasep)-1)):
            DataDic[labels[i]] = float(datasep[i])
        DataDic['Dither supported'] = datasep[-1]
        return DataDic

# =============================================================================
# SET
# =============================================================================
    
    def set_power(self, chan: int, value: float) -> None:
        '''
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

        Returns
        -------
        None.
        '''
        if chan not in [1, 2]:
            raise ValueError('Unknown input! See function description for more info.') 
        self.write(f'POW 1,1,{chan},{value}')
     
    def set_wavelength(self, chan: int, value: float) -> None:
        '''
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

        Returns
        -------
        None.
        '''
        if chan not in [1, 2]:
            raise ValueError('Unknown input! See function description for more info.') 
        self.write(f'WAV 1,1,{chan},{value}')
        
    def set_freq_thz(self, chan: int, value: float) -> None:
        '''
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

        Returns
        -------
        None.
        '''
        if chan not in [1, 2]:
            raise ValueError('Unknown input! See function description for more info.') 
        self.write(f'FREQ 1,1,{chan},{value}')
   
    def set_laser_output(self, chan: int, state: Union[str, int]) -> None:
        '''
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

        Returns
        -------
        None.
        '''
        parsed_state = self._parse_state(state)
        state_val = '1' if parsed_state == 'ON' else '0'
            
        if chan in [1, 2]:
            self.write(f'STATe 1,1,{chan},{state_val}')
        else:
            raise ValueError('Unknown input! See function description for more info.') 
                
    def set_offset(self, chan: int, value: float) -> None:
        '''
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

        Returns
        -------
        None.
        '''
        if chan not in [1, 2]:
            raise ValueError('Unknown input! See function description for more info.') 
        self.write(f'OFF 1,1,{chan},{value}')
        
    def set_configuration(self, chan: int, freq: float, power: float, offset: float) -> None:
        '''
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

        Returns
        -------
        None.
        '''
        if chan in [1, 2]:
            self.set_freq_thz(chan, freq)
            self.set_power(chan, power)
            self.set_offset(chan, offset)
        else:
            raise ValueError('Unknown input! See function description for more info.') 

    # =============================================================================
    # Aliases for backward compatibility
    # =============================================================================
    Close = BaseInstrument.close
    Identification = get_identification
    ask_FreqTHz = get_freq_thz
    ask_Wavelength = get_wavelength
    ask_Offset = get_offset
    ask_LaserOutput = get_laser_output
    ask_Power = get_power
    ask_ActualPower = get_actual_power
    ask_LaserLim = get_laser_lim
    ask_Configuration = get_configuration
    set_Power = set_power
    set_Wavelength = set_wavelength
    set_FreqTHz = set_freq_thz
    set_LaserOutput = set_laser_output
    set_Offset = set_offset
    set_Configuration = set_configuration
