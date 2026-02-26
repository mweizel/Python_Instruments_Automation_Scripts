# -*- coding: utf-8 -*-
"""
Created on Tue Feb 15 10:57:49 2022

@author: Martin.Mihaylov
"""


import numpy as np
import pyvisa as visa
from .BaseInstrument import BaseInstrument
from typing import List, Dict, Union


    
class APPH(BaseInstrument):
    def __init__(self, resource_str: str, visa_library: str = '@py', **kwargs):
        kwargs.setdefault('query_delay', 0.5)
        kwargs.setdefault('read_termination', '\n')
        super().__init__(str(resource_str), visa_library=visa_library, **kwargs)
        print(self.get_idn())

        

    
        
        
# =============================================================================
# Initiate System
# =============================================================================
    def init(self):
        '''
        

        Returns
        -------
        None.
            Initialize the measurement

        '''
        self.write(':INITiate:IMMediate')
        
# =============================================================================
# Abort
# =============================================================================

    def abort(self):
        '''
        

        Returns
        -------
        None.
            Abort measurement

        '''
        
        self.write(':ABORt')
        
# =============================================================================
# ASK
# =============================================================================

    def get_calc_freq(self):
        '''
        

        Returns
        -------
        TYPE float 
            Reads back the detected frequency from a frequency search.

        '''
        return float(self.query(':CALCulate:FREQuency?').split('\n')[0])




    def get_calc_power(self):
        '''
        

        Returns
        -------
        TYPE float
            Reads back the detected power level from a frequency search.

        '''
        
        return float(self.query(':CALCulate:POWer?').split('\n')[0])  
    


    
    def get_dut_port_voltage(self):
        '''
        

        Returns
        -------
        TYPE float
           Sets/gets the voltage at the DUT TUNE port. Returns the configured value. If the output is
           turned off, it doesn’t necessarily return 0, as an internal voltage may be configured.

        '''
        return float(self.query(':SOURce:TUNE:DUT:VOLT?').split('\n')[0])
    
    
    
    
    def get_dut_port_status(self):
        '''
        

        Returns
        -------
        stat : str
           Query the status of the DUT TUNE port.

        '''
        
        stat = self.query('SOURce:TUNE:DUT:STAT?').split('\n')[0]
        if stat == '0':
            stat = 'OFF'
        else:
            stat = 'ON'
        return stat
    
    
    
    
    def get_sys_meas_mode(self):
        '''
        

        Returns
        -------
        TYPE str
            Gets the active measurement mode.

        '''
        return self.query('SENSe:MODE?')
    
    
    
    
    def get_system_error(self):
        '''
        

        Returns
        -------
        TYPE list
            Return parameters: List of integer error numbers. This query is a request for all 
            entries in the instrument’s error queue. Error messages in the queue contain an 
            integer in the range [-32768,32768] denoting an error code and associated descriptive
            text. This query clears the instrument’s error queue.

        '''
        
        return self.query(':SYSTem:ERRor:ALL?')
    
    
# =============================================================================
# Ask Phase Noise
# =============================================================================

    def get_pm_trace_jitter(self):
        '''
        

        Returns
        -------
        TYPE str
            Returns the RMS jitter of the current trace.

        '''
            
        return self.query(':CALCulate:PN:TRACE:SPURious:JITTer?')
        
        
        
        
        
    def get_pm_trace_noise(self):
        '''
        

        Returns
        -------
        TYPE list
            Returns a list of phase noise points of the most recent measurement as block data.

        '''
        return self.query(':CALCulate:PN:TRACe:NOISe?')  
    
    
    
    
    
    def get_pn_if_gain(self):
        '''
        

        Returns
        -------
        TYPE float
            Range: 0-60
            Query the IF gain for the measurement.

        '''
        return float(self.query(':SENSe:PN:IFGain?'))
    
    
    
    
    def get_pn_start_freq(self):
        '''
        

        Returns
        -------
        TYPE float
            Query the start offset frequency

        '''
        return float(self.query(':SENSe:PN:FREQuency:STARt?').split('\n')[0])
    
    
    
    
    
    def get_pn_stop_freq(self):
        '''
        

        Returns
        -------
        TYPE float
            Query the stop offset frequency

        '''
        return float(self.query(':SENSe:PN:FREQuency:STOP?').split('\n')[0])
    
    
    
    def get_pn_spot(self,value):
        '''
        

        Parameters
        ----------
        value : float 
            The parameter is given as offset frequency in [Hz]
            Unit Hz
            Value - float

        Returns
        -------
        TYPE str
            Returns the phase noise value of the last measurement at the offset frequency 
            defined in <value>. The parameter is given as offset frequency in [Hz]
            Unit Hz
            Value - float

        '''
        
        return self.query('CALCulate:PN:TRACE:SPOT? '+str(value))
    
    
# =============================================================================
# Ask Amplitude Noise
# =============================================================================

    
    def get_an_trace_freq(self):
        '''
        

        Returns
        -------
        TYPE str
            Returns a list of offset frequency values of the current measurement as block data.
            Hz

        '''
        
        return self.query(':CALCulate:AN:TRACe:FREQuency?')
    
    
    
    def get_an_trace_noise(self):
        '''
        

        Returns
        -------
        TYPE str
            Returns a list of amplitude noise spectrum values of the current measurement as block data
            Unit dBc/Hz

        '''
       
        return self.query('CALCulate:AN:TRACe:NOISe?')
    
    
    
    
    def get_an_trace_spur_freq(self):
        '''
        

        Returns
        -------
        TYPE str
            Returns a list of offset frequencies of the spurs in the active trace as block data.
            Unit Hz

        '''
        
        return self.query(':CALCulate:AN:TRACe:SPURious:FREQuency?')
    
    
    
    
    def get_an_trace_spur_power(self):
        '''
        

        Returns
        -------
        TYPE str
            Returns a list of power values of the spurs in the active trace as block data.
            Unit dBc

        '''
        
        return self.query(':CALCulate:AN:TRACe:SPURious:POWer?')
    
    
    
    
    def get_an_spot(self,value):
        '''
        

        Parameters
        ----------
        value : TYPE
            The parameter is given as offset frequency in [Hz]
                Unit Hz
                Value - float

        Returns
        -------
        TYPE str
            Returns the phase noise value of the last measurement at the offset frequency 
            defined in <value>. The parameter is given as offset frequency in [Hz]
            Unit Hz
            Value - float

        '''
       
        return self.query('CALCulate:AN:TRACE:SPOT? '+str(value))
    
    
# =============================================================================
# Ask Frequency Noise
# =============================================================================


    def get_fn_trace_freq(self):
        '''
        

        Returns
        -------
        TYPE list
            Returns a list of offset frequency values of the current measurement as block data.
            Unit Hz

        '''
       
        return self.query(':CALCulate:FN:TRACe:FREQuency?')
    
    
    
    def get_fn_trace_noise(self):
        '''
        

        Returns
        -------
        TYPE list
             Returns a list of phase noise spectrum values of the current measurement as block data.
             Units are in Hz.
        '''
        
        return self.query(':CALCulate:FN:TRACe:NOISe?')
    
    
    
    def get_fn_trace_spur_freq(self):
        '''
        

        Returns
        -------
        TYPE list
            Returns a list of offset frequencies of the spurs in the active trace as block data.
            Units are in Hz.
        '''
        
        return self.query(':CALCulate:FN:TRACe:SPURious:FREQuency?')
    
    
    
    def get_fn_trace_spur_power(self):
        '''
        

        Returns
        -------
        TYPE list
               Returns a list of power values of the spurs in the active trace as block data.
               Units are in Hz

        '''
        
        return self.query(':CALCulate:FN:TRACe:SPURious:POWer?')
    
    
    
    def get_fn_spot(self,value):
        '''
        

        Parameters
        ----------
        value : float
            The parameters defines the spot noise offset frequency in [Hz].
                Units are in Hz.
                Value - float

        Returns
        -------
        TYPE str
            Returns the spot noise value at the specified offset frequency. 

        '''
        
        return self.query('CALCulate:FN:TRACE:SPOT? '+str(value))
    
    
    
# =============================================================================
# Ask Voltage controlled Oscillator
# =============================================================================

    def get_vco_trace_freq(self):
        '''
        

        Returns
        -------
        TYPE list
            Returns a list of frequency values measured at each tune voltage point of the 
            current measurement as block data2.

        '''
       
        return self.query('CALCulate:VCO:TRACE:FREQuency?')
    
    
    
    def get_vco_trace_p_noise(self,chan):
        '''
        

        Parameters
        ----------
        chan : list
            Can be set to [1,2,3,4]

        Raises
        ------
        ValueError
            Error massage

        Returns
        -------
        TYPE list
            Returns a list of phase noise values measured at each tune voltage point of 
            the current measurement as block data. The parameter 1-4 selects the offset 
            frequency from the set defined by the SENS:VCO:TEST:PN:OFFS <list> command

        '''
        chanLS = [1,2,3,4]
        if chan in chanLS:
            return self.query('CALCulate:VCO:TRACE:PNoise? '+str(chan))
        else:
            raise ValueError('Unknown input! See function description for more info.')
            
            
            
            
    def get_vco_trace_power(self):
        '''
        

        Returns
        -------
        TYPE list 
            Returns a list of power values measured at each tune voltage point of the current 
            measurement as block data.

        '''
       
        return self.query('CALCulate:VCO:TRACE:POWer?')
    
    
    
    def get_vco_trace_voltage(self):
        '''
        

        Returns
        -------
        TYPE list
            Returns a list of tune voltage values measured at each tune voltage point of the 
            current measurement as block data.

        '''
        
        return self.query('CALCulate:VCO:TRACE:VOLTage?')
    
    
    
    
    def get_vso_test_freq(self):
        '''
        

        Returns
        -------
        TYPE str
            Query the frequency parameter for the measurement.

        '''
        return self.query(':SENSe:VCO:TEST:FREQuency?')   
    
    
    
    
    def get_vso_test_noise(self):
        '''
        

        Returns
        -------
        TYPE str
            Query the phase noise parameter for the measurement.

        '''
       
        return self.query(':SENSe:VCO:TEST:PNoise?')   
    
    
    
    
    def get_vco_test_power(self):
        '''
        

        Returns
        -------
        TYPE str
            Query the power parameter for the measurement.

        '''

        return self.query(':SENSe:VCO:TEST:POWer?')   
    
    
    
    
    def get_vco_test_start(self):
        '''
        

        Returns
        -------
        TYPE str
             Query the start tuning voltage for the measurement.
             Units are in V.

        '''
        
        return self.query(':SENSe:VCO:VOLTage:STARt?')
    
    
    
    
    def get_vco_test_stop(self):
        '''
        

        Returns
        -------
        TYPE str
            Query the stop tuning voltage for the measurement.
            Units are in V

        '''
        
        return self.query(':SENSe:VCO:VOLTage:STOP?')
    
    
    
    
    def get_vco_test_i_supply(self):
        '''
        

        Returns
        -------
        TYPE str
            Query the supply current parameter for the measurement

        '''
        
        return self.query(':SENSe:VCO:TEST:ISUPply?')
    
    
    
    def get_vcok_pu_shing(self):
        '''
        

        Returns
        -------
        TYPE str
            Query the pushing parameter for the measurement

        '''
        
        return self.query(':SENSe:VCO:TEST:KPUShing?')
    
    
    
    
    def get_vcokvco(self):
        '''
        

        Returns
        -------
        TYPE str
            Query the tune sensitivity parameter for the measurement.

        '''
       
        return self.query(':SENSe:VCO:TEST:KVCO?')
        
    
    
        
    def get_vcotype(self):
        '''
        

        Returns
        -------
        TYPE str
            Query the DUT type for the measurement.

        '''
        
        return self.query(':SENSe:VCO:TYPE?')
    
    
    
    def get_vco_test_p_noise(self):
        '''
        

        Returns
        -------
        TYPE str
            Query the phase noise parameter for the measurement.

        '''
        
        return self.query(':SENSe:VCO:TEST:PNoise?')
    
    
    
    def get_vco_test_pnoise_off_set(self,state):
        '''
        

        Parameters
        ----------
        state : int
            Can be set to [1,2,3,4]

        Raises
        ------
        ValueError
            Error massage

        Returns
        -------
        TYPE str
            Query the 4 offset frequencies at which the phase noise is measured

        '''
        
    
        stateLs = [1,2,3,4]
        if state in stateLs:
            return self.query(':SENSe:VCO:TEST:Pnoise:OFFSet'+str(state)+'?')
        else:
            raise ValueError('Unknown input! See function description for more info.')
    
    
    
    def get_vco_test_point(self):
        '''
        

        Returns
        -------
        TYPE str
            Query the number rof voltage points to use in the measurement

        '''
        return self.query(':SENSe:VCO:VOLTage:POINts?')
        
        
# =============================================================================
# SET
# =============================================================================

    def set_output(self,status):
        '''
        

        Parameters
        ----------
        status : str
            Set Output ON and OFF.  CAn be ['ON','OFF']

        Raises
        ------
        ValueError
            Error massage

        Returns
        -------
        None.

        '''
        
        statusLs = ['ON','OFF']
        if status in statusLs:
            self.write(':OUTput '+status)
        else:
            raise ValueError('Unknown input! See function description for more info.')
    
    
    
    
    def set_sys_meas_mode(self,state):
        '''
        

        Parameters
        ----------
        state : str
            Sets/gets the active measurement mode. Can be ['PN','AN','FN','BB','TRAN','VCO']
                • PN: phase noise measurement
                • AN: amplitude noise measurement
                • FN: frequency noise measurement (results are converted to phase noise)
                • BB: base band measurement (not yet available)
                • TRAN: transient analysis (not yet available)
                • VCO: voltage controlled oscillator characterization

        Raises
        ------
        ValueError
            Error massage


        Returns
        -------
        None.

        '''
        
        stateLs = ['PN','AN','FN','BB','TRAN','VCO']
        if state in stateLs:
            self.write('SENSe:MODE '+str(state))
        else:
            raise ValueError('Unknown input! See function description for more info.')
            
            
            
            
    def set_freq_execute(self):
        '''
        

        Returns
        -------
        None.
            Starts the frequency search. See function calculate subsystem on how to read out the result.

        '''
        
        self.write('SENSe:FREQuency:EXECute?')
        
        
        
        
    def set_power_execute(self):
        '''
        

        Returns
        -------
        None.
            Starts the power measurement. When performing SENS:FREQ:EXEC, this measurement 
            will be automatically run at the end (if a signal is detected

        '''
        
        self.write('SENSe:POWer:EXECute?')
        
        
        
    def set_calc_average(self,event):
        '''
        
        
        Parameters
        ----------
        event : str
                Waits for the defined event 
                NEXT: next iteration complete 
                ALL: measurement complete
                <value>: specified iteration complete 
                Optionally, a timeout in milliseconds can be specified as a second parameter. 
                This command will block further SCPI requests until the specified event or the
                specified timeout has occurred. If no timeout is specified, the timeout will be 
                initiated.

        Returns
        -------
        None.

        '''
        self.write('CALCulate:WAIT:AVERage '+str(event))
        


    def set_dut_port_voltage(self,value):
        '''
        

        Parameters
        ----------
        value : float
            Sets the voltage at the DUT TUNE port. Returns the configured value.
            If the output is turned off, it doesn’t necessarily return 0, as an internal
            voltage may be configured
            
            
        Returns
        -------
        None.

        '''
        
        self.write(':SOURce:TUNE:DUT:VOLT '+str(value))
        
    
    def set_dut_port_status(self,state):
        '''
        

        Parameters
        ----------
        state : str
            Enables/disables the DUT TUNE port. Can be ['ON','OFF']

        Raises
        ------
        ValueError
            Error massage

        Returns
        -------
        None.

        '''
        
        stateLs = ['ON','OFF']
        if state in stateLs:
            self.write(':SOURce:TUNE:DUT:STAT '+str(state))
        else:
            raise ValueError('Unknown input! See function description for more info.')
            
        
            
    
# =============================================================================
# Set Phase Noise
# =============================================================================

    def set_pnif_gain(self,value):
        '''
        

        Parameters
        ----------
        value : float
            Range: 0-60
            Sets the IF gain for the measurement.

        Raises
        ------
        ValueError
            Error massage

        Returns
        -------
        None.

        '''
        
        if value>60.0:
            raise ValueError('Unknown input! See function description for more info.')
        else:
            self.write(':SENSe:PN:IFGain '+str(value))
            
            
            
            
    def set_pn_start_freq(self,value):
        '''
        

        Parameters
        ----------
        value : float
                    Unit HZ
                    Sets the start offset frequency.

        Returns
        -------
        None.

        '''
        
        self.write(':SENSe:PN:FREQuency:STARt '+str(value))
        
        
    def set_pn_stop_freq(self,value):
        '''
        

        Parameters
        ----------
        value : float
            Unit HZ
            Sets the stop offset frequency.

        Returns
        -------
        None.

        '''
       
        self.write(':SENSe:PN:FREQuency:STOP '+str(value))
        
        
        
# =============================================================================
# Set Voltage controlled Oscillators
# =============================================================================
        

    def set_vco_wait(self,state,value):
        '''
        

        Parameters
        ----------
        state : str
            Can be ['ALL','NEXT']
        value : float
            This command requests a preliminary result during the measurement and blocks until 
            the result is ready. The first parameter (required) specifies the target iteration
            to be saved. NEXT specifies the next possible iteration, ALL specifies the last 
            iteration of the measurement (i.e. waits for the measurement to finish) and an 
            integer specifies the specific iteration requested.The second parameter (optional)
            defines a timeout in milliseconds. If the command terminates without generating a 
            preliminary result. It will produce an error. This error can be queried with
            SYST:ERR? or SYST:ERR:ALL?.

        Returns
        -------
        TYPE
            DESCRIPTION.

        '''
        
        
        stateLs = ['ALL','NEXT']
        if state in stateLs:
            return self.query('CALCulate:VCO:WAIT '+str(state)+' '+str(value))
        
        
        
        
    def set_vco_test_freq(self,state):
        '''
        

        Parameters
        ----------
        state : str 
            Enables/Disables the frequency parameter for the measurement.
            Can be ['ON','OFF']

        Raises
        ------
        ValueError
            Error massage

        Returns
        -------
        None.

        '''
        
        stateLs = ['ON','OFF']
        if state in stateLs:
            self.write(':SENSe:VCO:TEST:FREQuency ' +str(state))
        else:
            raise ValueError('Unknown input! See function description for more info.')
            
            
            
            
    def set_vco_test_noise(self,state):
        '''
        

        Parameters
        ----------
        state : str
            Enables/Disables the phase noise parameter for the measurement.
            Can be  ['ON','OFF']

        Raises
        ------
        ValueError
            Error massage

        Returns
        -------
        None.

        '''
        
        stateLs = ['ON','OFF']
        if state in stateLs:
            self.write(':SENSe:VCO:TEST:PNoise ' +str(state))
        else:
            raise ValueError('Unknown input! See function description for more info.')
        
    
    
    
    
    def set_vco_test_power(self,state):
        '''
        

        Parameters
        ----------
        state : str
            Enables/Disables the power parameter for the measurement.
            Can be ['ON','OFF']

        Raises
        ------
        ValueError
            Error massage

        Returns
        -------
        None.

        '''
    
        stateLs = ['ON','OFF']
        if state in stateLs:
            self.write(':SENSe:VCO:TEST:POWer ' +str(state))
        else:
            raise ValueError('Unknown input! See function description for more info.')
            
            
            
            
            
    
    def set_vco_test_start(self,value):
        '''
        

        Parameters
        ----------
        value : float
            Sets the start tuning voltage for the measurement.
            Unit V

        Returns
        -------
        None.

        '''
        
        self.write(':SENSe:VCO:VOLTage:STARt '+ str(value))
        
        
        
    
    def set_vco_test_stop(self,value):
        '''
        

        Parameters
        ----------
        value : float
            Sets the stop tuning voltage for the measurement.
            Units are in V.

        Returns
        -------
        None.

        '''
        
        self.write(':SENSe:VCO:VOLTage:STOP '+ str(value))
        
        
        
        
    def set_vco_test_i_supply(self,state):
        '''
        

        Parameters
        ----------
        state : str
            Enables/disables the supply current parameter for the measurement.
            Can be ['ON','OFF']

        Raises
        ------
        ValueError
            Error massage

        Returns
        -------
        None.

        '''
        
        stateLs = ['ON','OFF']
        if state in stateLs:
            self.write(':SENSe:VCO:TEST:ISUPply ' +str(state))
        else:
            raise ValueError('Unknown input! See function description for more info.')
        
        
        
    
    def set_vcok_pu_shing(self,state):
        '''
        

        Parameters
        ----------
        state : str
            Enables/disables the pushing parameter for the measurement.
            Can be ['ON','OFF']

        Raises
        ------
        ValueError
            Error massage

        Returns
        -------
        None.

        '''
        
        stateLs = ['ON','OFF']
        if state in stateLs:
            self.write(':SENSe:VCO:TEST:KPUShing ' +str(state))
        else:
            raise ValueError('Unknown input! See function description for more info.')
    
    
    
    
    
    def set_vcokvco(self,state):
        '''
        

        Parameters
        ----------
        state : str
           Enables/disables the tune sensitivity parameter for the measurement
           Can be ['ON','OFF']
           
        Raises
        ------
        ValueError
            Error massage

        Returns
        -------
        None.

        '''
        
        stateLs = ['ON','OFF']
        if state in stateLs:
            self.write(':SENSe:VCO:TEST:KVCO ' +str(state))
        else:
            raise ValueError('Unknown input! See function description for more info.')
        
    
    
    
    
    def set_vcotype(self,typ):
        '''
        

        Parameters
        ----------
        typ : str
            Select the DUT type for the measurement. Distinguish between slow (VCXO) and fast
            (VCO) tuning sensitivities. Can be ['VCO','VCXO']

        Raises
        ------
        ValueError
            Error massage

        Returns
        -------
        None.

        '''
        
        typLs = ['VCO','VCXO']
        if typ in typLs:
            self.write(':SENSe:VCO:TYPE ' +str(typ))
        else:
            raise ValueError('Unknown input! See function description for more info.')
        
        
        
        
        
    def set_vco_test_p_noise(self,state):
        '''
        

        Parameters
        ----------
        state : str
            Enables/Disables the phase noise parameter for the measurement.
            Can be set to ['ON','OFF']

        Raises
        ------
        ValueError
            Error massage

        Returns
        -------
        None.

        '''
        
        stateLs = ['ON','OFF']
        if state in stateLs:
            self.write(':SENSe:VCO:TEST:PNoise ' +str(state))
        else:
            raise ValueError('Unknown input! See function description for more info.')
            
            
            
            
    def set_vco_test_pnoise_off_set(self,value1=0,value2=0,value3=0,value4=0):
        '''
        

        Parameters
        ----------
        value1 : float
            freq val 1
        value2 : float
            freq val 2
        value3 : float
            freq val 3
        value4 : float
            freq val 4


        Sets up to 4 offset frequencies at which the phase noise is measured. 
        At least 1 parameter is required. Blank parameters are set to 0 
        (disabled). The query returns the set frequency for the specified 
        offset. The offset can be specified with the <sel> parameter and can 
        be chosen from 1|2|3|4
        
        Unit HZ
        
        Returns
        -------
        None.

        '''
        
        self.write(':SENSe:VCO:TEST:Pnoise:OFFSet ' +str(value1)+','+str(value2)+','\
                   +str(value3)+','+str(value4))
        
            
            
    def set_vco_test_point(self,value):
        '''
        

        Parameters
        ----------
        value : float
            Sets the number rof voltage points to use in the measurement

        Returns
        -------
        None.

        '''
        
        self.write(':SENSe:VCO:VOLTage:POINts '+str(value))


# =============================================================================
# Get Functions
# =============================================================================
        
        
    def getIdn(self):
        '''
        

        Returns
        -------
        TYPE Str
            Queries the device serial number and name

        '''
        
        return self.query('*IDN?')
        
        
            
# =============================================================================
# Measurments Examples 
# =============================================================================
    
    def PNMeasExample(self,value):
        '''
        This is a small example how to make a phase noise measurement.
        '''
        
        self.set_sys_meas_mode('PN') # select phase noise measurement
        self.init()                # start measurement
        self.set_calc_average('ALL') # wait for the measurement to finish
        err = self.get_system_error()     # check if measurement was successful
        val = self.get_pn_spot(value) #request spot noise value at 1MHz offset
        ResultDic = {}
        ResultDic['Error Value'] = err # Write Error status if 0 no errors!
        ResultDic['Spot Phase Noise @ ' +str(value)] = val
        return ResultDic
    
    
    
    def ANMeasExample(self,value):
        '''
        This is a small example how to make a phase noise measurement.
        '''
        self.set_sys_meas_mode('AN') # select amplitude noise measurement
        self.init()                # start measurement
        err = self.get_system_error()     # check if measurement was successful
        val = self.get_an_spot(value) #request spot noise value at 1MHz offset
        ResultDic = {}
        ResultDic['Error Value'] = err #Write Error status if 0 no errors!
        ResultDic['Spot Amplitude Noise @ ' +str(value)] = val
        return ResultDic




    def FNMeasExample(self,value):
        '''
        This is a small example how to make a frequency noise measurement.
        '''
        self.set_sys_meas_mode('FN') # select amplitude noise measurement
        self.init()                # start measurement
        err = self.get_system_error()     # check if measurement was successful
        val = self.get_fn_spot(value) #request spot noise value at 1MHz offset
        ResultDic = {}
        ResultDic['Error Value'] = err #Write Error status if 0 no errors!
        ResultDic['Spot Frequency Noise @ ' +str(value)] = val
        return ResultDic
    
    
    
    def VCOMeasExample(self,NoieseOffset1,NoieseOffset2,measPoints,tunRangeMin,tunRangeMax,SupplyVoltage,delay):
        '''
        This is a small example how to make a Voltage controlled oscillator noise measurement.
        '''
        
        # Config
        self.set_sys_meas_mode('VCO') # Select VCO characterization
        self.set_vco_test_freq('ON') # Enable frequency parameter
        self.set_vco_test_i_supply('ON') # Enable supply current parameter
        self.set_vcok_pu_shing('ON') # Enable pushing parameter
        self.set_vcokvco('ON') # Enable Kvco parameter
        self.set_vco_test_p_noise('ON') # Enable spot noise parameter
        self.set_vco_test_pnoise_off_set(NoieseOffset1,NoieseOffset2) # Set two spot noise offsets: 1.2kHz, 100kHz
        self.set_vco_test_power('ON') # Enable power parameter
        
        
        # Measurement
        self.set_vcotype('VCO') # Set DUT Type (VCO or VCXO)
        self.set_vco_test_point(measPoints) # Set 11 measurement points
        self.set_vco_test_start(tunRangeMin) # Set tuning range minimum to 0.5V
        self.set_vco_test_stop(tunRangeMax) # Set tuning range maximum to 10V
        self.set_dut_port_voltage(SupplyVoltage) # Set supply voltage to 6V
        self.set_dut_port_status('ON') # Enable supply voltage
        self.init()                # Start measurement
        
        
        # Loop
        self.set_vco_wait('ALL',delay) # Wait for the measurement to finish
        err = self.get_system_error() # Check if measurement was successful
        ResultDic = {}
        
        
        # Read results
        ResultDic['control voltage'] = self.get_vco_trace_voltage() # request control voltage data array
        ResultDic['frequency data'] = self.get_vco_trace_freq() # Request frequency data array
        ResultDic['Kvco data'] = self.get_vcokvco() # Request Kvco data array
        ResultDic['pushing data'] = self.get_vcok_pu_shing() # Request pushing data array
        ResultDic['supply current data'] = self.get_vco_test_i_supply() # Request supply current data array
        ResultDic['power level'] = self.get_vco_trace_power() # Request power level data array
        ResultDic['spot noise data array @offset #1 (1.2kHz)'] = self.get_vco_test_pnoise_off_set(1) # Request spot noise data array @offset #1 (1.2kHz)
        ResultDic['Error Value'] = err # Write Error status if 0 no errors!
        
        
        
        
        

        
    # =============================================================================
    # Aliases for backward compatibility
    # =============================================================================
    Close = BaseInstrument.close
    Init = init
    Abort = abort
    ask_CalcFreq = get_calc_freq
    ask_CalcPower = get_calc_power
    ask_DUTPortVoltage = get_dut_port_voltage
    ask_DUTPortStatus = get_dut_port_status
    ask_SysMeasMode = get_sys_meas_mode
    ask_SystemError = get_system_error
    ask_PMTraceJitter = get_pm_trace_jitter
    ask_PMTraceNoise = get_pm_trace_noise
    ask_PN_IFGain = get_pn_if_gain
    ask_PN_StartFreq = get_pn_start_freq
    ask_PN_StopFreq = get_pn_stop_freq
    ask_PNSpot = get_pn_spot
    ask_ANTraceFreq = get_an_trace_freq
    ask_ANTraceNoise = get_an_trace_noise
    ask_ANTraceSpurFreq = get_an_trace_spur_freq
    ask_ANTraceSpurPower = get_an_trace_spur_power
    ask_ANSpot = get_an_spot
    ask_FNTraceFreq = get_fn_trace_freq
    ask_FNTraceNoise = get_fn_trace_noise
    ask_FNTraceSpurFreq = get_fn_trace_spur_freq
    ask_FNTraceSpurPower = get_fn_trace_spur_power
    ask_FNSpot = get_fn_spot
    ask_VCOTraceFreq = get_vco_trace_freq
    ask_VCOTracePNoise = get_vco_trace_p_noise
    ask_VCOTracePower = get_vco_trace_power
    ask_VCOTraceVoltage = get_vco_trace_voltage
    ask_VSOTestFreq = get_vso_test_freq
    ask_VSOTestNoise = get_vso_test_noise
    ask_VCOTestPower = get_vco_test_power
    ask_VCOTestStart = get_vco_test_start
    ask_VCOTestStop = get_vco_test_stop
    ask_VCOTestISupply = get_vco_test_i_supply
    ask_VCOKPuShing = get_vcok_pu_shing
    ask_VCOKVCO = get_vcokvco
    ask_VCOTYPE = get_vcotype
    ask_VCOTestPNoise = get_vco_test_p_noise
    ask_VCOTestPnoiseOFFSet = get_vco_test_pnoise_off_set
    ask_VCOTestPoint = get_vco_test_point
    set_Output = set_output
    set_SysMeasMode = set_sys_meas_mode
    set_FreqExecute = set_freq_execute
    set_PowerExecute = set_power_execute
    set_CalcAverage = set_calc_average
    set_DUTPortVoltage = set_dut_port_voltage
    set_DUTPortStatus = set_dut_port_status
    set_PNIFGain = set_pnif_gain
    set_PNStartFreq = set_pn_start_freq
    set_PNStopFreq = set_pn_stop_freq
    set_VCOWait = set_vco_wait
    set_VCOTestFreq = set_vco_test_freq
    set_VCOTestNoise = set_vco_test_noise
    set_VCOTestPower = set_vco_test_power
    set_VCOTestStart = set_vco_test_start
    set_VCOTestStop = set_vco_test_stop
    set_VCOTestISupply = set_vco_test_i_supply
    set_VCOKPuShing = set_vcok_pu_shing
    set_VCOKVCO = set_vcokvco
    set_VCOTYPE = set_vcotype
    set_VCOTestPNoise = set_vco_test_p_noise
    set_VCOTestPnoiseOFFSet = set_vco_test_pnoise_off_set
    set_VCOTestPoint = set_vco_test_point
