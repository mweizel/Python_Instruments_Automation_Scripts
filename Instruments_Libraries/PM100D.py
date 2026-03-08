"""
Created on Thu Dec  2 08:27:01 2021

@author: MartinMihaylov
"""

import time

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

    def __init__(self, resource_str: str, visa_library: str = "@py", **kwargs):

        # Choose the effective VISA resource name
        s = str(resource_str)
        if "::" in s or s.startswith("USB"):
            # Caller passed a full VISA string in resource_str
            rn = s
        else:
            # Caller passed a bare serial; build a PM100D VISA address
            # Vendor ID 0x1313 = Thorlabs; Product ID 0x8078 = PM100D USBTMC
            rn = f"USB0::0x1313::0x8078::{s}::INSTR"

        kwargs.setdefault("timeout", 1000)
        kwargs.setdefault("read_termination", "\n")
        super().__init__(rn, visa_library=visa_library, **kwargs)

        # Query *IDN? to verify connectivity (Thorlabs PM100* expected)
        print(self.get_idn())

    # =============================================================================
    #     Self Test
    # =============================================================================

    def self_test(self):
        """
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
        Query the current measurement configuration.
        """

        return self.query("CONFigure?")

    # =============================================================================
    # Fetch last meassure Data
    # =============================================================================

    def fetch_data(self, allow_NaN: bool = False, delay: float | None = None) -> float:  # noqa: N803
        """
        Reads last measurement data. WILL NOT START THE MEASUREMENT!
        Use readData() instead. Returns 'nan' if no data is available.
        """
        val = float(self.query(":FETCh?"))
        if abs(val) >= 9.0e37:
            delay = 1 if delay is None else delay
            val = self.read_data(delay=delay, allow_NaN=allow_NaN)
        return val

    def read_data(self, allow_NaN: bool = False, delay: float | None = 1) -> float:  # noqa: N803
        """
        Starts a measurement and reads last measurement data.
        Returns last measurement data or 'nan' if no data is available.
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
        """
        Start measurement.
        """
        self.write(":INITiate:IMMediate")

    # =============================================================================
    # Abort Measurement
    # =============================================================================

    def abort(self) -> None:
        """
        Abort measurement.
        """

        self.write("ABORt")

    # =============================================================================
    # Adapter Settings
    # =============================================================================

    def get_adapter_type(self) -> str:
        """
        Queries default sensor adapter type.
        """
        return self.query("INPut:ADAPter:TYPE?")

    def set_adapter_type(self, state: str) -> None:
        """


        Parameters
        ----------
        state : str
            Sets default sensor adapter type:
                Allow senor types are: ['PHOTodiode','THERmal','PYRo']
        """

        valid_state = self._check_scpi_param(state, ["PHOTodiode", "THERmal", "PYRo"])
        self.write("INPut:ADAPter:TYPE " + valid_state)

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
        """
        state = self._parse_state(state)
        self.write(f"INPut:PDIode:FILTer:LPASs:STATe {state}")

    # =============================================================================
    # Ask Instrument
    # =============================================================================

    def get_beeper(self) -> int:
        """
        Return the state of the beeper.
        """
        return int(self.query("SYSTem:BEEPer:STATe?"))

    def get_calibration(self) -> str:
        """
        Returns a human readable calibration string.
        """

        return self.query("CALibration:STRing?")

    def get_pd_power(self) -> str:
        """
        Queries the photodiode response value.
        """

        return self.query("CORRection:POWer:PDIOde:RESPonse?")

    def get_thermopile(self) -> str:
        """
        Queries the thermopile response value.
        """

        return self.query("POWer:THERmopile:RESPonse?")

    def get_pyro(self) -> str:
        """
        Queries the pyro-detectr response value.
        """

        return self.query("ENERgy:PYRO:RESPonse?")

    def get_energy_range(self) -> str:
        """
        Queries the energy range.
        """
        return self.query("ENERgy:RANGe:UPPer?")

    def get_current_range(self) -> str:
        """
        Queries the actual current range.
        """
        return self.query("CURRent:DC:UPPer?")

    def get_auto_current_range(self) -> str:
        """
        Queries the auto-ranging function state.
        """
        return self.query("CURRent:DC:AUTO?")

    def get_freq_range(self, state: str) -> str | None:
        """Queries the frequency range.


        Parameters
        ----------
        state : str
            Can be  ['MAX','MIN']
        """
        valid_state = self._check_scpi_param(state, ["MAXimum", "MINimum"])
        if valid_state == "MAXimum":
            return self.query("SENSe:FREQuency:Range:UPPer?")
        elif valid_state == "MINimum":
            return self.query("SENSe:FREQuency:Range:LOWer?")


    def get_power_units(self) -> str:
        """
        Queries the power unit.
        """

        return self.query("SENSe:POWer:DC:UNIT?")

    def get_auto_power_range(self) -> str:
        """
        Queries the auto-ranging function state.
        """

        return self.query("POWer:DC:RANGe:AUTO?")

    def get_power_range(self):
        """
        Queries the power range.
        """

        return self.query("POWer:DC:RANGe:UPPer?")

    def get_volt_range(self):
        """
        Queries the current voltage range.
        """

        return self.query("VOLTage:DC:UPPer?")

    def get_auto_voltage_range(self):
        """
        Queries the auto-ranging function state.
        """

        return self.query("VOLTage:DC:AUTO?")

    def get_wavelength(self):
        """
        Queries the operation wavelength.
        """

        return self.query("CORRection:WAVelength?")

    def get_beam_diameter(self):
        """
        Queries the beam diameter.
        """

        return self.query("CORRection:BEAMdiameter?")

    def get_average(self):
        """
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
        """

        valid_state = self._check_scpi_param(state, ["W", "DBM"])
        self.write("POWer:DC:UNIT " + valid_state)

    def set_auto_power_range(self, state: str | int) -> None:
        """Switches the auto-ranging function on and off.


        Parameters
        ----------
        state : str/int
             Can be set to ['ON','OFF',1,0].
        """
        state = self._parse_state(state)
        self.write(f"POWer:DC:RANGe:AUTO {state}")

    def set_power_range(self, value: float | int) -> None:
        """


        Parameters
        ----------
        value : float/int
             Sets the current range in W
        """

        if isinstance(value, (int, float)):
            self.write("POWer:DC:RANGe:UPPer " + str(value) + " W")
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_auto_current_range(self, state: str | int) -> None:
        """Switches the auto-ranging function on and off.


        Parameters
        ----------
        state : str/int
            Can be set to ['ON','OFF',1,0].
        """

        state = self._parse_state(state)
        self.write(f"SENSe:CURRent:DC:RANGe:AUTO {state}")

    def set_current_range(self, value: float | int) -> None:
        """


        Parameters
        ----------
        value : float/int
           Sets the current range in A.
        """

        if isinstance(value, (int, float)):
            self.write("SENSe:CURRent:DC:RANGe:UPPer " + str(value) + " A")
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_auto_voltage_range(self, state: str | int) -> None:
        """Switches the auto-ranging function on and off.


        Parameters
        ----------
        state : str/int
            Can be ['ON','OFF',1,0]
        """

        state = self._parse_state(state)
        self.write(f"SENSe:VOLTage:DC:RANGe:AUTO {state}")

    def set_voltage_range(self, value: float) -> None:
        """


        Parameters
        ----------
        value : float
            Sets the voltage range in V
        """

        if isinstance(value, (int, float)):
            self.write("SENSe:VOLTage:DC:RANGe:UPPer " + str(value) + " V")
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_energy_range(self, value: float | int) -> None:
        """


        Parameters
        ----------
        value : float
             Sets the energy range in J
        """

        if isinstance(value, (int, float)):
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
        dis_list = ["auto", "manual"]
        if dis in dis_list:
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
        dis_list = ["auto", "manual"]
        if dis in dis_list:
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
        dis_list = ["auto", "manual"]
        if dis in dis_list:
            if dis == "auto":
                self.set_auto_current_range("ON")
            else:
                self.set_auto_voltage_range("OFF")
                value = float(input("Sets the upper range to: "))
                self.set_current_range(value)
        else:
            print("Invalid input! adjustVoltageRange() is stopped!")

    def set_parameters(self, type: str) -> None:
        """Legacy function. Do not use.
        This function will set the measurement parameters interactively.


        Parameters
        ----------
        type : str
            Can be set to Type = ['Power','Energy','Current','Voltage']

        """

        diss = type
        diss_list = ["Power", "Energy", "Current", "Voltage"]
        if diss in diss_list:
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

    def display_param(self, type: str) -> None:
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

        meas = type
        meas_list = ["Power", "Energy", "Current", "Voltage"]
        if meas in meas_list:
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

    def display_param_dict(self, type: str) -> tuple[list, list, list]:
        """This function will print all the adjusted parameters.


        Parameters
        ----------
        type : str
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

        headers = ["Power", "Energy", "Current", "Voltage"]
        params = ["Adapter Type", "Max Frequency range", "Min Frequency range", "Wavelength"]
        data = [
            self.get_adapter_type(),
            self.get_freq_range("MAX"),
            self.get_freq_range("MIN"),
            self.get_wavelength(),
        ]

        meas = type
        meas_list = ["Power", "Energy", "Current", "Voltage"]
        if meas in meas_list:
            if meas == "Power":
                params.append("Power Unit set")
                data.append(self.get_power_units())
                params.append("Power range auto")
                data.append(self.get_auto_power_range())
                params.append("Power Range set")
                data.append(self.get_power_range())

            elif meas == "Energy":
                params.append("Energy range auto")
                data.append(self.get_energy_range())

            elif meas == "Voltage":
                params.append("Voltage range auto")
                data.append(self.get_auto_voltage_range())
                params.append("Voltage range")
                data.append(self.get_volt_range())
            elif meas == "Current":
                params.append("Current range auto")
                data.append(self.get_auto_current_range())
                params.append("Current range")
                data.append(self.get_current_range())

        else:
            print("Invalid Value! Function will be terminated.")

        return headers, data, params

    def power_meas(self) -> float:
        """
        Legacy function. Do not use! Use get_Power instead.
        Performs a power measurement interactively, returning data from the measurement.
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

    def default_power_meas(self, wavelength: float | int) -> float:
        """Legacy function. Do not use! Use get_Power instead.
        Performs a power measurement with hard coded parameters!
        PowerRange is set to auto.

        Parameters
        ----------
        wavelength : float
            Wavelength in nm.

        Returns
        -------
        float
            Power in dBm.

        """

        self.set_power_units("dBm")
        self.set_wavelength(wavelength)
        self.set_auto_power_range("ON")

        self.config_power()
        self.meas_power()
        self.init()
        complete = "0"
        while complete != "1":
            complete = self.OPC()
            time.sleep(0.1)

        return self.fetch_data()

    def default_power_meas_w(self, wavelength: float | int) -> float:
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
        self.set_wavelength(wavelength)
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
        wavelength: float | None = None,
        *,
        allow_NaN: bool = False,  # noqa: N803
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

        if unit is not None:
            self.set_power_units(unit)
        if wavelength is not None:
            self.set_wavelength(wavelength)
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

