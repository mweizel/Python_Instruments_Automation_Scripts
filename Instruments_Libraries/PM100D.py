# -*- coding: utf-8 -*-
"""
Created on Thu Dec  2 08:27:01 2021

@author: MartinMihaylov
"""


import time
import numpy as np
from typing import Optional, Union, Dict, List
from .BaseInstrument import BaseInstrument


class PM100D(BaseInstrument):
    """
    Thorlabs PM100-series power meter wrapper using PyVISA.

    You can construct either with:
      - resource_str="P00XXXXX"       # serial only (legacy behavior)
      - resource_str="USB0::...::INSTR"  # full VISA resource (also works)

    Parameters
    ----------
    resource_str : str | None
        Either the device serial (e.g., 'P00XXXXX') or a full VISA string. Kept
        for backward compatibility.
    visa_library : str
        Optional PyVISA backend string, e.g., '@py' for pyvisa-py.
    """

    def __init__(
        self,
        resource_str: str,
        visa_library: str = '@py',
        **kwargs
    ):

        # Choose the effective VISA resource name
        s = str(resource_str)
        if "::" in s or s.startswith("USB"):
            # Caller passed a full VISA string in resource_str
            rn = s
        else:
            # Caller passed a bare serial; build a PM100D VISA address
            # Vendor ID 0x1313 = Thorlabs; Product ID 0x8078 = PM100D USBTMC
            rn = f"USB0::0x1313::0x8078::{s}::INSTR"

        kwargs.setdefault('timeout', 1000)
        kwargs.setdefault('read_termination', '\n')
        super().__init__(rn, visa_library=visa_library, **kwargs)

        # Query *IDN? to verify connectivity (Thorlabs PM100* expected)
        print(self.get_idn())

    # =============================================================================
    #     Self Test
    # =============================================================================

    def self_test(self):
        """


        Returns
        -------
        TYPE
             Use this query command to perform the instrument self-test routine. The command
             places the coded result in the Output Queue. A returned value of zero (0) indicates
             that the test passed, other values indicate that the test failed.

        """
        print(
            "A returned value of zero (0) indicates that the test passed, other \
              values indicate that the test failed."
        )

        return self.query("*TST?")

    # =============================================================================
    # Configuration
    # =============================================================================
    def read_config(self) -> str:
        """


        Returns
        -------
        str
            Query the current measurement configuration

        """

        return self.query("CONFigure?")

    # =============================================================================
    # Fetch last meassure Data
    # =============================================================================

    def fetch_data(self, allow_NaN: bool = False, delay: float | None = None) -> float:
        """Reads last measurement data. WILL NOT START THE MEASUREMENT!
        Use readData() instead. Returns 'nan' if no data is available.


        Returns
        -------
        float
            last measurement data or 'nan' if no data is available.
        """
        val = float(self.query(":FETCh?"))
        if abs(val) >= 9.0e37:
            delay = 1 if delay is None else delay
            val = self.read_data(delay=delay, allow_NaN=allow_NaN)
        return val

    def read_data(self, allow_NaN: bool = False, delay: float | None = 1) -> float:
        """Starts a measurement and reads last measurement data.

        Returns
        -------
        float
            last measurement data or 'nan' if no data is available.
        """
        s = self._resource.query(":READ?", delay=delay)  # triggers, waits, returns result
        val = float(s)
        if abs(val) >= 9.0e37:
            if allow_NaN:
                return float("nan")
            else:
                raise OverflowError(f"READ? returned sentinel {val}")
        return val



    # =============================================================================
    # Initialize Commando
    # =============================================================================

    def init(self) -> None:
        """Start measurement.


        Returns
        -------
        None.

        """
        self.write(":INITiate:IMMediate")

    # =============================================================================
    # Abort Measurement
    # =============================================================================

    def abort(self) -> None:
        """


        Returns
        -------
        None.
            Abort measurement

        """

        self.write("ABORt")

    # =============================================================================
    # Adapter Settings
    # =============================================================================

    def get_adapter_type(self) -> str:
        """


        Returns
        -------
        str
            Queries default sensor adapter type

        """
        return self.query("INPut:ADAPter:TYPE?")

    def set_adapter_type(self, state: str) -> None:
        """


        Parameters
        ----------
        state : str
            Sets default sensor adapter type:
                Allow senor types are: ['PHOTodiode','THERmal','PYRo']
        Raises
        ------
        ValueError
            Error message.

        Returns
        -------
        None.

        """

        stState = ["PHOTodiode", "THERmal", "PYRo"]
        if state in stState:
            self.write("INPut:ADAPter:TYPE " + state)
        else:
            raise ValueError("Unknown input! See function description for more info.")

    # =============================================================================
    # Photodiode parameters
    # =============================================================================
    def set_pd(self, state: str | int) -> None:
        """


        Parameters
        ----------
        state : str/int
            Sets the bandwidth of the photodiode input stage.
                Can be ['ON','OFF',1,0]
        Raises
        ------
        ValueError
            Error message.

        """
        state = self._parse_state(state)
        self.write(f"INPut:PDIode:FILTer:LPASs:STATe {state}")

    # =============================================================================
    # Ask Instrument
    # =============================================================================

    def get_beeper(self) -> int:
        """


        Returns
        -------
        int
            Return the state of the beeper.

        """
        return int(self.query("SYSTem:BEEPer:STATe?"))

    def get_calibration(self) -> str:
        """


        Returns
        -------
        str
            Returns a human readable calibration string.

        """

        return self.query("CALibration:STRing?")

    def get_pd_power(self) -> str:
        """


        Returns
        -------
        str
            Queries the photodiode response value.

        """

        return self.query("CORRection:POWer:PDIOde:RESPonse?")

    def get_thermopile(self) -> str:
        """


        Returns
        -------
        str
            Queries the thermopile response value.

        """

        return self.query("POWer:THERmopile:RESPonse?")

    def get_pyro(self) -> str:
        """


        Returns
        -------
        str
            Queries the pyro-detectr response value.

        """

        return self.query("ENERgy:PYRO:RESPonse?")

    def get_energy_range(self) -> str:
        """


        Returns
        -------
        str
            Queries the energy range.

        """
        return self.query("ENERgy:RANGe:UPPer?")

    def get_current_range(self) -> str:
        """


        Returns
        -------
        str
            Queries the actual current range.

        """
        return self.query("CURRent:DC:UPPer?")

    def get_auto_current_range(self) -> str:
        """


        Returns
        -------
        str
            Queries the auto-ranging function state.

        """
        return self.query("CURRent:DC:AUTO?")

    def get_freq_range(self, state: str) -> str:
        """Queries the frequency range.


        Parameters
        ----------
        state : str
            Can be  ['MAX','MIN']

        Raises
        ------
        ValueError
            Error message.

        Returns
        -------
        str
            Queries the frequency range.

        """
        stState = ["MAX", "MIN"]
        if state in stState:
            if state == "MAX":
                state = "UPPer?"
                return self.query("SENSe:FREQuency:Range:" + state)
            else:
                state = "LOWer?"
                return self.query("SENSe:FREQuency:Range:" + state)
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def get_power_units(self) -> str:
        """


        Returns
        -------
        str
            Queries the power unit.

        """

        return self.query("SENSe:POWer:DC:UNIT?")

    def get_auto_power_range(self) -> str:
        """


        Returns
        -------
        str
            Queries the auto-ranging function state.

        """

        return self.query("POWer:DC:RANGe:AUTO?")

    def get_power_range(self):
        """


        Returns
        -------
        str
            Queries the power range.

        """

        return self.query("POWer:DC:RANGe:UPPer?")

    def get_volt_range(self):
        """


        Returns
        -------
        str
            Queries the current voltage range.

        """

        return self.query("VOLTage:DC:UPPer?")

    def get_auto_voltage_range(self):
        """


        Returns
        -------
        str
           Queries the auto-ranging function state.

        """

        return self.query("VOLTage:DC:AUTO?")

    def get_wavelength(self):
        """


        Returns
        -------
        str
            Queries the operation wavelength.

        """

        return self.query("CORRection:WAVelength?")

    def get_beam_diameter(self):
        """


        Returns
        -------
        str
            Queries the beam diameter.

        """

        return self.query("CORRection:BEAMdiameter?")

    def get_average(self):
        """


        Returns
        -------
        str
            Queries the averaging rate.

        """

        return self.query("SENSe:AVERage:COUNt?")

    # =============================================================================
    # Set Power,Energy,Current,Voltage Measurment Values aand Wavelength
    # =============================================================================

    def set_power_units(self, state: str) -> None:
        """


        Parameters
        ----------
        state : str
            Sets the power unit W or dBm. Can be ['W','dBm'].

        Raises
        ------
        ValueError
            Error message.

        """

        stState = ["W", "dBm"]
        if state in stState:
            self.write("POWer:DC:UNIT " + str(state))
        else:
            raise ValueError(f"Unknown input! You selected {state}. Allowed inputs are {stState}")

    def set_auto_power_range(self, state: str | int) -> None:
        """Switches the auto-ranging function on and off.


        Parameters
        ----------
        state : str/int
             Can be set to ['ON','OFF',1,0].


        Raises
        ------
        ValueError
            Error message.

        """
        state = self._parse_state(state)
        self.write(f"POWer:DC:RANGe:AUTO {state}")

    def set_power_range(self, value: float | int) -> None:
        """


        Parameters
        ----------
        value : float/int
             Sets the current range in W

        Raises
        ------
        ValueError
            Error message.

        """

        if type(value) == int or type(value) == float:
            self.write("POWer:DC:RANGe:UPPer " + str(value) + " W")
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_auto_current_range(self, state: str | int) -> None:
        """Switches the auto-ranging function on and off.


        Parameters
        ----------
        state : str/int
            Can be set to ['ON','OFF',1,0].

        Raises
        ------
        ValueError
            Error message.

        """

        state = self._parse_state(state)
        self.write(f"SENSe:CURRent:DC:RANGe:AUTO {state}")

    def set_current_range(self, value: float | int) -> None:
        """


        Parameters
        ----------
        value : float/int
           Sets the current range in A.


        Raises
        ------
        ValueError
            Error message.

        """

        if type(value) == int or type(value) == float:
            self.write("SENSe:CURRent:DC:RANGe:UPPer " + str(value) + " A")
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_auto_voltage_range(self, state: str | int) -> None:
        """Switches the auto-ranging function on and off.


        Parameters
        ----------
        state : str/int
            Can be ['ON','OFF',1,0]


        Raises
        ------
        ValueError
            Error message.

        """

        state = self._parse_state(state)
        self.write(f"SENSe:VOLTage:DC:RANGe:AUTO {state}")

    def set_voltage_range(self, value: float) -> None:
        """


        Parameters
        ----------
        value : float
            Sets the voltage range in V

        Raises
        ------
        ValueError
            Error message.

        """

        if type(value) == int or type(value) == float:
            self.write("SENSe:VOLTage:DC:RANGe:UPPer " + str(value) + " V")
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_energy_range(self, value: float | int) -> None:
        """


        Parameters
        ----------
        value : float
             Sets the energy range in J

        Raises
        ------
        ValueError
            Error message.

        """

        if type(value) == int or type(value) == float:
            self.write("SENSe:ENERgy:DC:RANGe:UPPer " + str(value) + " J")
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_wavelength(self, value: float | int) -> None:
        """


        Parameters
        ----------
        value : float/int
            Sets the operation wavelength in nm.

        """

        self.write(f"SENSe:CORRection:WAVelength {value} nm")

    def set_average(self, value: float | int) -> None:
        """


        Parameters
        ----------
        value : float/int
            Sets the averaging rate (1 sample takes approx. 3ms)

        """
        self.write(f"SENSe:AVERage:COUNt {value}")

    # =============================================================================
    # Configure
    # =============================================================================

    def config_power(self) -> None:
        """
        Configure for power measurement.

        """
        self.write(":CONFigure:POWer")

    def config_current(self) -> None:
        """
        Configure for current measurement.

        """
        self.write(":CONFigure:CURRent:DC")

    def config_voltage(self) -> None:
        """
        Configure for voltage measurement.

        """
        self.write(":CONFigure::VOLTage:DC")

    def config_energy(self) -> None:
        """
        Configure for energy measurement.

        """
        self.write(":CONFigure:ENERgy")

    def config_freq(self) -> None:
        """
        Configure for frequency measurement.
        """
        self.write(":CONFigure:FREQuency")

    def config_power_density(self) -> None:
        """
        Configure for power density measurement.

        """
        self.write(":CONFigure:PDENsity")

    def config_energy_density(self) -> None:
        """
        Configure for energy density measurement.

        """
        self.write(":CONFigure:EDENsity")

    def config_resistance(self) -> None:
        """
        Configure for sensor presence resistance measurement.

        """
        self.write(":CONFigure:RESistance")

    def config_temp(self) -> None:
        """
        Configure for sensor temperature measurement.

        """
        self.write(":CONFigure:TEMPerature")

    # =============================================================================
    # Perform Measurment
    # =============================================================================

    def meas_power(self) -> None:
        """
        Performs a Power measurement.
        Maxim: Does nothing? Measure with Init() or readData() instead!
        """
        self.write("MEASure:POWer")

    def meas_current(self) -> None:
        """
        Performs a current measurement.
        Maxim: Does nothing? Measure with Init() or readData() instead!
        """
        self.write("MEASure:CURRent:DC ")

    def meas_voltage(self) -> None:
        """
        Performs a voltage measurement.
        Maxim: Does nothing? Measure with Init() or readData() instead!
        """
        self.write("MEASure:VOLTage:DC")

    def meas_energy(self) -> None:
        """
        Maxim: Does nothing? Measure with Init() or readData() instead!
        """
        self.write("MEASure:ENERgy")

    def meas_power_density(self) -> None:
        """
        Performs a power density measurement.
        Maxim: Does nothing? Measure with Init() or readData() instead!
        """
        self.write("MEASure:PDENsity")

    def meas_energy_density(self) -> None:
        """
        Performs an energy density measurement.
        Maxim: Does nothing? Measure with Init() or readData() instead!
        """
        self.write("MEASure:EDENsity")

    def meas_resistance(self) -> None:
        """
        Performs a sensor presence resistance measurement.
        Maxim: Does nothing? Measure with Init() or readData() instead!
        """
        self.write("MEASure:RESistance")

    def meas_temp(self) -> None:
        """
        Performs a sensor temperature measurement.
        Maxim: Does nothing? Measure with Init() or readData() instead!
        """
        self.write("MEASure:TEMPerature")

    def meas_freq(self) -> None:
        """
        Performs a frequency measurement.
        Maxim: Does nothing? Measure with Init() or readData() instead!
        """
        self.write("MEASure:FREQuency")

    # =============================================================================
    # Measurment Test
    # =============================================================================

    def adjust_power_meas(self) -> None:
        """Legacy function. Do not use.
        Adjust the power measurement interactively.

        """
        un = input("Set Power unit 'W' or 'dBm': ")
        self.set_power_units(un)
        dis = input("Set Power Measurement Range 'auto' or 'manual': ")
        disList = ["auto", "manual"]
        if dis in disList:
            if dis == "auto":
                self.set_auto_power_range("ON")
            else:
                self.set_auto_power_range("OFF")
                val = float(input("Sets the upper Power range in W to: "))
                self.set_power_range(val)
        else:
            print("Invalid input! adjustPowerMeas() is stopped!")

    def adjust_energy_meas(self):
        """Legacy function. Do not use.
        Adjust the Energy Measurement interactively.

        """
        print("Energy is measured in J")
        value = float(input("Set Energy range in J: "))
        self.set_energy_range(value)

    def adjust_voltage_range(self):
        """Legacy function. Do not use.
        Adjust the Voltage Measurement interactively.

        """
        dis = input("Set Voltage Measurement Range 'auto' or 'manual': ")
        disList = ["auto", "manual"]
        if dis in disList:
            if dis == "auto":
                self.set_auto_voltage_range("ON")
            else:
                self.set_auto_voltage_range("OFF")
                value = float(input("Sets the upper range to: "))
                self.set_voltage_range(value)
        else:
            print("Invalid input! adjustVoltageRange() is stopped!")

    def adjust_current_range(self):
        """Legacy function. Do not use.
        Adjust the Current Measurement interactively.

        """
        dis = input("Set Current Measurement Range 'auto' or 'manual': ")
        disList = ["auto", "manual"]
        if dis in disList:
            if dis == "auto":
                self.set_auto_current_range("ON")
            else:
                self.set_auto_voltage_range("OFF")
                value = float(input("Sets the upper range to: "))
                self.set_current_range(value)
        else:
            print("Invalid input! adjustVoltageRange() is stopped!")

    def set_parameters(self, Type: str) -> None:
        """Legacy function. Do not use.
        This function will set the measurement parameters interactively.


        Parameters
        ----------
        Type : str
            Can be set to Type = ['Power','Energy','Current','Voltage']

        """

        diss = Type
        dissList = ["Power", "Energy", "Current", "Voltage"]
        if diss in dissList:
            if diss == "Power":
                self.adjust_power_meas()
            elif diss == "Energy":
                self.adjust_energy_meas()
            elif diss == "Voltage":
                self.adjust_voltage_range()
            else:
                self.adjust_current_range()
        else:
            print("Invalid input! Function will be stopped!")

    def display_param(self, Type: str) -> None:
        """Legacy function. Do not use.
        This function will print all the adjusted parameters.


        Parameters
        ----------
        Type : str
            Can be set to Type = ['Power','Energy','Current','Voltage']


        """

        print("Adapter Type: ", self.get_adapter_type())
        print("Max Frequency range: ", self.get_freq_range("MAX"))
        print("Min Frequency range: ", self.get_freq_range("MIN"))
        print("Wavelength: ", self.get_wavelength())

        meas = Type
        measList = ["Power", "Energy", "Current", "Voltage"]
        if meas in measList:
            if meas == "Power":
                print("Power Unit set: ", self.get_power_units())
                print("Power range auto: ", self.get_auto_power_range())
                print("Power Range set: ", self.get_power_range())

            elif meas == "Energy":
                print("Energy range auto: ", self.get_energy_range())
            elif meas == "Voltage":
                print("Voltage range auto: ", self.get_auto_voltage_range())
                print("Voltage range: ", self.get_volt_range())
            elif meas == "Current":
                print("Current range auto: ", self.get_auto_current_range())
                print("Current range: ", self.get_current_range())
        else:
            print("Invalid Value! Function will be terminated.")

    def display_param_dict(self, Type: str) -> tuple[list, list, list]:
        """This function will print all the adjusted parameters.


        Parameters
        ----------
        Type : str
            Can be set to Type = ['Power','Energy','Current','Voltage']

        Returns
        -------
        Headers : str
            String with ['Power','Energy','Current','Voltage']
        Data : list
            Data from the instrument.
        Params : list
            List with str for different data that are extracted from the instrument.

        """

        Headers = ["Power", "Energy", "Current", "Voltage"]
        Params = ["Adapter Type", "Max Frequency range", "Min Frequency range", "Wavelength"]
        Data = [
            self.get_adapter_type(),
            self.get_freq_range("MAX"),
            self.get_freq_range("MIN"),
            self.get_wavelength(),
        ]

        meas = Type
        measList = ["Power", "Energy", "Current", "Voltage"]
        if meas in measList:
            if meas == "Power":
                Params.append("Power Unit set")
                Data.append(self.get_power_units())
                Params.append("Power range auto")
                Data.append(self.get_auto_power_range())
                Params.append("Power Range set")
                Data.append(self.get_power_range())

            elif meas == "Energy":
                Params.append("Energy range auto")
                Data.append(self.get_energy_range())

            elif meas == "Voltage":
                Params.append("Voltage range auto")
                Data.append(self.get_auto_voltage_range())
                Params.append("Voltage range")
                Data.append(self.get_volt_range())
            elif meas == "Current":
                Params.append("Current range auto")
                Data.append(self.get_auto_current_range())
                Params.append("Current range")
                Data.append(self.get_current_range())

        else:
            print("Invalid Value! Function will be terminated.")

        return Headers, Data, Params

    def power_meas(self) -> float:
        """Legacy function. Do not use! Use get_Power instead.
        Performs a power measurement interactively.


        Returns
        -------
        float
            Data from the power measurement.

        """

        print("This Function performs Power measurements.")
        # print('To go on whit the measurments please check again the parameters set!')
        self.set_parameters("Power")
        print("#####################################")
        self.display_param("Power")
        print("#####################################")

        com = input("Should the measurement proceed yes/no: ")
        if com == "yes":
            self.init()
            complete = "0"
            while complete != "1":
                complete = self.OPC()
                time.sleep(0.1)
            self.config_power()
            self.meas_power()
            return self.fetch_data()
        else:
            print("Measurement is canceled!")
            return float("nan")

    def default_power_meas(self, WaveLength: float | int) -> float:
        """Legacy function. Do not use! Use get_Power instead.
        Performs a power measurement with hard coded parameters!
        PowerRange is set to auto.

        Parameters
        ----------
        WaveLength : float
            Wavelength in nm.

        Returns
        -------
        float
            Power in dBm.

        """

        self.set_power_units("dBm")
        self.set_wavelength(WaveLength)
        self.set_auto_power_range("ON")

        self.config_power()
        self.meas_power()
        self.init()
        complete = "0"
        while complete != "1":
            complete = self.OPC()
            time.sleep(0.1)

        return self.fetch_data()

    def default_power_meas_w(self, WaveLength: float | int) -> float:
        """Legacy function. Do not use! Use get_Power instead.
        Performs a power measurement with hard coded parameters!
        PowerRange is set to auto.

        Parameters
        ----------
        WaveLength : float
            Wavelength in nm.

        Returns
        -------
        float
            Power in W.

        """

        self.set_power_units("W")
        self.set_wavelength(WaveLength)
        self.set_auto_power_range("ON")

        self.config_power()
        self.meas_power()
        self.init()
        complete = "0"
        while complete != "1":
            complete = self.OPC()
            time.sleep(0.1)
        return self.fetch_data()

    def power_specifications(self) -> None:
        """Legacy function. Do not use.
        This function will print all the adjusted parameters for the power measurement.

        """

        self.display_param("Power")

    def get_power(
        self,
        unit: str | None = None,
        waveLength: float | None = None,
        *,
        allow_NaN: bool = False,
        delay: float | None = None,
    ) -> float:
        """Performs a Power measurement.

        Parameters
        ----------
        unit : str, optional
            Power unit ['W','dBm']. The default is (keep unchanged).
        waveLength : float, optional
            Wavelength in nm. The default is (keep unchanged).
        allow_NaN : bool, optional
            If True, returns 'nan' if no data is available. The default is False.
        delay : float, optional
            Delay in seconds between query and read. The default is (standard delay).

        Returns
        -------
        float
            Power in dBm or W.

        """

        if unit != None:
            self.set_power_units(unit)
        if waveLength != None:
            self.set_wavelength(waveLength)
        if self.read_config() == "POW":
            pass
        else:
            self.config_power()

        self.init()
        complete = "0"
        while complete != "1":  # From Maxim: This does not work.
            complete = self.OPC()
            time.sleep(0.1)
        return self.fetch_data(allow_NaN=allow_NaN, delay=delay)

    def get_power(
        self,
        unit: str | None = None,
        waveLength: float | None = None,
        *,
        allow_NaN: bool = False,
        delay: float | None = None,
    ) -> float:
        """Calls get_Power()."""
        return self.get_power(unit=unit, waveLength=waveLength, allow_NaN=allow_NaN, delay=delay)

    # =============================================================================
    # Aliases for backward compatibility
    # =============================================================================
    ReadConfig = read_config
    fetchData = fetch_data
    readData = read_data
    Init = init
    Abort = abort
    ask_AdapterType = get_adapter_type
    set_AdapterType = set_adapter_type
    set_PD = set_pd
    ask_beeper = get_beeper
    ask_calibration = get_calibration
    ask_PDPower = get_pd_power
    ask_Thermopile = get_thermopile
    ask_Pyro = get_pyro
    ask_energyRange = get_energy_range
    ask_currentRange = get_current_range
    ask_AutoCurrentRange = get_auto_current_range
    ask_freqRange = get_freq_range
    ask_PowerUnits = get_power_units
    ask_AutoPowerRange = get_auto_power_range
    ask_PowerRange = get_power_range
    ask_voltRange = get_volt_range
    ask_AutoVoltageRange = get_auto_voltage_range
    ask_Wavelength = get_wavelength
    ask_BeamDiameter = get_beam_diameter
    ask_Average = get_average
    set_PowerUnits = set_power_units
    set_AutoPowerRange = set_auto_power_range
    set_PowerRange = set_power_range
    set_AutoCurrentRange = set_auto_current_range
    set_currentRange = set_current_range
    set_AutoVoltageRange = set_auto_voltage_range
    set_voltageRange = set_voltage_range
    set_energyRange = set_energy_range
    set_WaveLength = set_wavelength
    set_Average = set_average
    ConfigPower = config_power
    ConfigCurrent = config_current
    ConfigVoltage = config_voltage
    ConfigEnergy = config_energy
    ConfigFreq = config_freq
    ConfigPowerDensity = config_power_density
    ConfigEnergyDensity = config_energy_density
    ConfigResistance = config_resistance
    ConfigTemp = config_temp
    MeasPower = meas_power
    MeasCurrent = meas_current
    MeasVoltage = meas_voltage
    MeasEnergy = meas_energy
    MeasPowerDensity = meas_power_density
    MeasEnergyDensity = meas_energy_density
    MeasResistance = meas_resistance
    MeasTemp = meas_temp
    MeasFreq = meas_freq
    adjustPowerMeas = adjust_power_meas
    adjustEnergyMeas = adjust_energy_meas
    adjustVoltageRange = adjust_voltage_range
    adjustCurrentRange = adjust_current_range
    set_Parameters = set_parameters
    DisplayParam = display_param
    DisplayParamDict = display_param_dict
    PowerMeas = power_meas
    DefaultPowerMeas = default_power_meas
    DefaultPowerMeas_W = default_power_meas_w
    PowerSpecifications = power_specifications
    get_Power = get_power
    ask_Power = get_power
