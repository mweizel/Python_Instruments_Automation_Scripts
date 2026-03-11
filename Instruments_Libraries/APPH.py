"""
Created on Tue Feb 15 10:57:49 2022

@author: Martin.Mihaylov
"""

from .BaseInstrument import BaseInstrument


class APPH(BaseInstrument):
    def __init__(self, resource_str: str, visa_library: str = "@py", **kwargs):
        kwargs.setdefault("query_delay", 0.5)
        kwargs.setdefault("read_termination", "\n")
        super().__init__(str(resource_str), visa_library=visa_library, **kwargs)
        print(self.get_idn())

    # =============================================================================
    # Initiate System
    # =============================================================================
    def init(self) -> None:
        """
        Initialize the measurement
        """
        self.write(":INITiate:IMMediate")

    # =============================================================================
    # Abort
    # =============================================================================

    def abort(self) -> None:
        """
        Abort measurement
        """
        self.write(":ABORt")

    # =============================================================================
    # ASK
    # =============================================================================

    def get_calc_freq(self) -> float:
        """
        Reads back the detected frequency from a frequency search.
        """
        return float(self.query(":CALCulate:FREQuency?"))

    def get_calc_power(self) -> float:
        """
        Reads back the detected power level from a frequency search.
        """
        return float(self.query(":CALCulate:POWer?"))

    def get_dut_port_voltage(self) -> float:
        """
        Sets/gets the voltage at the DUT TUNE port. Returns the configured value. If the output
        is turned off, it doesn't necessarily return 0, as an internal voltage may be configured.
        """
        return float(self.query(":SOURce:TUNE:DUT:VOLT?"))

    def get_dut_port_status(self) -> str:
        """
        Query the status of the DUT TUNE port.
        """
        stat = self.query("SOURce:TUNE:DUT:STAT?")
        if stat == "0":
            stat = "OFF"
        else:
            stat = "ON"
        return stat

    def get_sys_meas_mode(self) -> str:
        """
        Gets the active measurement mode.
        """
        return self.query("SENSe:MODE?")

    def get_system_error(self) -> str:
        """
        Return parameters: List of integer error numbers. This query is a request for all
        entries in the instrument's error queue. Error messages in the queue contain an
        integer in the range [-32768,32768] denoting an error code and associated descriptive
        text. This query clears the instrument's error queue.
        """
        return self.query(":SYSTem:ERRor:ALL?")

    # =============================================================================
    # Ask Phase Noise
    # =============================================================================

    def get_pm_trace_jitter(self) -> str:
        """
        Returns the RMS jitter of the current trace.
        """
        return self.query(":CALCulate:PN:TRACE:SPURious:JITTer?")

    def get_pm_trace_noise(self) -> str:
        """
        Returns a list of phase noise points of the most recent measurement as block data.
        """
        return self.query(":CALCulate:PN:TRACe:NOISe?")

    def get_pn_if_gain(self) -> float:
        """
        Range: 0-60
        Query the IF gain for the measurement.
        """
        return float(self.query(":SENSe:PN:IFGain?"))

    def get_pn_start_freq(self) -> float:
        """
        Query the start offset frequency
        """
        return float(self.query(":SENSe:PN:FREQuency:STARt?"))

    def get_pn_stop_freq(self) -> float:
        """
        Query the stop offset frequency
        """
        return float(self.query(":SENSe:PN:FREQuency:STOP?"))

    def get_pn_spot(self, value: float) -> str:
        """
        Returns the phase noise value of the last measurement at the offset frequency
        defined in <value>. The parameter is given as offset frequency in [Hz].

        Parameters
        ----------
        value : float
            Offset frequency. Unit: ``'Hz'``.
        """
        return self.query("CALCulate:PN:TRACE:SPOT? " + str(value))

    # =============================================================================
    # Ask Amplitude Noise
    # =============================================================================

    def get_an_trace_freq(self) -> str:
        """
        Returns a list of offset frequency values of the current measurement as block data.
        Hz
        """
        return self.query(":CALCulate:AN:TRACe:FREQuency?")

    def get_an_trace_noise(self) -> str:
        """
        Returns a list of amplitude noise spectrum values of the current measurement
        as block data. Unit dBc/Hz
        """
        return self.query("CALCulate:AN:TRACe:NOISe?")

    def get_an_trace_spur_freq(self) -> str:
        """
        Returns a list of offset frequencies of the spurs in the active trace as block data.
        Unit Hz
        """
        return self.query(":CALCulate:AN:TRACe:SPURious:FREQuency?")

    def get_an_trace_spur_power(self) -> str:
        """
        Returns a list of power values of the spurs in the active trace as block data.
        Unit dBc
        """
        return self.query(":CALCulate:AN:TRACe:SPURious:POWer?")

    def get_an_spot(self, value: float) -> str:
        """
        Returns the phase noise value of the last measurement at the offset frequency
        defined in <value>. The parameter is given as offset frequency in [Hz].

        Parameters
        ----------
        value : float
            Offset frequency. Unit: ``'Hz'``.
        """
        return self.query("CALCulate:AN:TRACE:SPOT? " + str(value))

    # =============================================================================
    # Ask Frequency Noise
    # =============================================================================

    def get_fn_trace_freq(self) -> str:
        """
        Returns a list of offset frequency values of the current measurement as block data.
        Unit Hz
        """
        return self.query(":CALCulate:FN:TRACe:FREQuency?")

    def get_fn_trace_noise(self) -> str:
        """
        Returns a list of phase noise spectrum values of the current measurement as block data.
        Units are in Hz.
        """
        return self.query(":CALCulate:FN:TRACe:NOISe?")

    def get_fn_trace_spur_freq(self) -> str:
        """
        Returns a list of offset frequencies of the spurs in the active trace as block data.
        Units are in Hz.
        """
        return self.query(":CALCulate:FN:TRACe:SPURious:FREQuency?")

    def get_fn_trace_spur_power(self) -> str:
        """
        Returns a list of power values of the spurs in the active trace as block data.
        Units are in Hz
        """
        return self.query(":CALCulate:FN:TRACe:SPURious:POWer?")

    def get_fn_spot(self, value: float) -> str:
        """
        Returns the spot noise value at the specified offset frequency.

        Parameters
        ----------
        value : float
            Spot noise offset frequency. Unit: ``'Hz'``.
        """
        return self.query("CALCulate:FN:TRACE:SPOT? " + str(value))

    # =============================================================================
    # Ask Voltage controlled Oscillator
    # =============================================================================

    def get_vco_trace_freq(self) -> str:
        """
        Returns a list of frequency values measured at each tune voltage point of the
        current measurement as block data2.
        """
        return self.query("CALCulate:VCO:TRACE:FREQuency?")

    def get_vco_trace_p_noise(self, chan: list) -> str:
        """
        Returns a list of phase noise values measured at each tune voltage point of
        the current measurement as block data. The parameter 1-4 selects the offset
        frequency from the set defined by the SENS:VCO:TEST:PN:OFFS <list> command

        Parameters
        ----------
        chan : int
            Valid options: ``1``, ``2``, ``3``, ``4``.

        Raises
        ------
        ValueError
            If an invalid channel is provided.
        """
        chan_list = [1, 2, 3, 4]
        if chan in chan_list:
            return self.query("CALCulate:VCO:TRACE:PNoise? " + str(chan))
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def get_vco_trace_power(self) -> str:
        """
        Returns a list of power values measured at each tune voltage point of the current
        measurement as block data.
        """
        return self.query("CALCulate:VCO:TRACE:POWer?")

    def get_vco_trace_voltage(self) -> str:
        """
        Returns a list of tune voltage values measured at each tune voltage point of the
        current measurement as block data.
        """
        return self.query("CALCulate:VCO:TRACE:VOLTage?")

    def get_vso_test_freq(self) -> str:
        """
        Query the frequency parameter for the measurement.
        """
        return self.query(":SENSe:VCO:TEST:FREQuency?")

    def get_vso_test_noise(self) -> str:
        """
        Query the phase noise parameter for the measurement.
        """
        return self.query(":SENSe:VCO:TEST:PNoise?")

    def get_vco_test_power(self) -> str:
        """
        Query the power parameter for the measurement.
        """
        return self.query(":SENSe:VCO:TEST:POWer?")

    def get_vco_test_start(self) -> str:
        """
        Query the start tuning voltage for the measurement.
        Units are in V.
        """
        return self.query(":SENSe:VCO:VOLTage:STARt?")

    def get_vco_test_stop(self) -> str:
        """
        Query the stop tuning voltage for the measurement.
        Units are in V
        """
        return self.query(":SENSe:VCO:VOLTage:STOP?")

    def get_vco_test_i_supply(self) -> str:
        """
        Query the supply current parameter for the measurement
        """
        return self.query(":SENSe:VCO:TEST:ISUPply?")

    def get_vcok_pu_shing(self) -> str:
        """
        Query the pushing parameter for the measurement
        """
        return self.query(":SENSe:VCO:TEST:KPUShing?")

    def get_vcokvco(self) -> str:
        """
        Query the tune sensitivity parameter for the measurement.
        """
        return self.query(":SENSe:VCO:TEST:KVCO?")

    def get_vcotype(self) -> str:
        """
        Query the DUT type for the measurement.
        """
        return self.query(":SENSe:VCO:TYPE?")

    def get_vco_test_p_noise(self) -> str:
        """
        Query the phase noise parameter for the measurement.
        """
        return self.query(":SENSe:VCO:TEST:PNoise?")

    def get_vco_test_pnoise_off_set(self, state: int) -> str:
        """
        Query the 4 offset frequencies at which the phase noise is measured

        Parameters
        ----------
        state : int
            Offset selector. Valid options: ``1``, ``2``, ``3``, ``4``.

        Raises
        ------
        ValueError
            If an invalid state is provided.
        """
        state_list = [1, 2, 3, 4]
        if state in state_list:
            return self.query(":SENSe:VCO:TEST:Pnoise:OFFSet" + str(state) + "?")
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def get_vco_test_point(self) -> str:
        """
        Query the number rof voltage points to use in the measurement
        """
        return self.query(":SENSe:VCO:VOLTage:POINts?")

    # =============================================================================
    # SET
    # =============================================================================

    def set_output(self, status: str | int | float | bool) -> None:
        """
        Parameters
        ----------
        status : str | int | float | bool
            Set Output ON and OFF.

            * ``'ON'`` / ``1`` : Activates the output.
            * ``'OFF'`` / ``0`` : Deactivates the output.

        Raises
        ------
        ValueError
            If an invalid state is provided.
        """
        valid_status = self._parse_state(status)
        self.write(":OUTput " + valid_status)

    def set_sys_meas_mode(self, state: str) -> None:
        """
        Parameters
        ----------
        state : str
            Sets/gets the active measurement mode.

            * ``'PN'`` : phase noise measurement
            * ``'AN'`` : amplitude noise measurement
            * ``'FN'`` : frequency noise measurement (results are converted to phase noise)
            * ``'BB'`` : base band measurement (not yet available)
            * ``'TRAN'`` : transient analysis (not yet available)
            * ``'VCO'`` : voltage controlled oscillator characterization

        Raises
        ------
        ValueError
            If an invalid state is provided.
        """
        valid_state = self._check_scpi_param(state, ["PN", "AN", "FN", "BB", "TRAN", "VCO"])
        self.write("SENSe:MODE " + valid_state)

    def set_freq_execute(self) -> None:
        """
        Starts the frequency search. See function calculate subsystem on how to read out the result.
        """
        self.write("SENSe:FREQuency:EXECute?")

    def set_power_execute(self) -> None:
        """
        Starts the power measurement. When performing SENS:FREQ:EXEC, this measurement
        will be automatically run at the end (if a signal is detected
        """
        self.write("SENSe:POWer:EXECute?")

    def set_calc_average(self, event: str) -> None:
        """
        Parameters
        ----------
        event : str
            Waits for the defined event.

            * ``'NEXT'``: next iteration complete
            * ``'ALL'``: measurement complete
            * ``<value>``: specified iteration complete

            Optionally, a timeout in milliseconds can be specified as a second parameter.
            This command will block further SCPI requests until the specified event or the
            specified timeout has occurred. If no timeout is specified, the timeout will be
            initiated.
        """
        self.write("CALCulate:WAIT:AVERage " + str(event))

    def set_dut_port_voltage(self, value: float) -> None:
        """
        Sets the voltage at the DUT TUNE port. Returns the configured value.
        If the output is turned off, it doesn't necessarily return 0, as an internal
        voltage may be configured

        Parameters
        ----------
        value : float
            Voltage at the DUT TUNE port.
        """
        self.write(":SOURce:TUNE:DUT:VOLT " + str(value))

    def set_dut_port_status(self, state: str | int | float | bool) -> None:
        """
        Parameters
        ----------
        state : str | int | float | bool
            Enables/disables the DUT TUNE port.

            * ``'ON'`` / ``1`` : Enables the port.
            * ``'OFF'`` / ``0`` : Disables the port.

        Raises
        ------
        ValueError
            If an invalid state is provided.
        """
        valid_state = self._parse_state(state)
        self.write(":SOURce:TUNE:DUT:STAT " + valid_state)

    # =============================================================================
    # Set Phase Noise
    # =============================================================================

    def set_pnif_gain(self, value: float) -> None:
        """
        Parameters
        ----------
        value : float
            Sets the IF gain for the measurement.

            * **Range**: ``0`` to ``60``

        Raises
        ------
        ValueError
            If the value is out of bounds.
        """
        if value > 60.0:
            raise ValueError("Unknown input! See function description for more info.")
        else:
            self.write(":SENSe:PN:IFGain " + str(value))

    def set_pn_start_freq(self, value: float) -> None:
        """
        Parameters
        ----------
        value : float
            Start offset frequency. Unit: ``'Hz'``.
        """
        self.write(":SENSe:PN:FREQuency:STARt " + str(value))

    def set_pn_stop_freq(self, value: float) -> None:
        """
        Parameters
        ----------
        value : float
            Stop offset frequency. Unit: ``'Hz'``.
        """
        self.write(":SENSe:PN:FREQuency:STOP " + str(value))

    # =============================================================================
    # Set Voltage controlled Oscillators
    # =============================================================================

    def set_vco_wait(self, state: str, value: float) -> str | None:
        """
        Parameters
        ----------
        state : str | int
            Target iteration to be saved.

            * ``'ALL'`` : Specifies the last iteration (waits for the measurement to finish)
            * ``'NEXT'`` : Specifies the next possible iteration
            * `<int>` : Specifies the specific iteration requested
        value : float
            Defines a timeout in milliseconds. If the command terminates without generating a
            preliminary result. It will produce an error. This error can be queried with
            SYST:ERR? or SYST:ERR:ALL?.
        """
        valid_state = self._check_scpi_param(state, ["ALL", "NEXT"])
        return self.query("CALCulate:VCO:WAIT " + valid_state + " " + str(value))

    def set_vco_test_freq(self, state: str | int | float | bool) -> None:
        """
        Parameters
        ----------
        state : str | int | float | bool
            Enables/Disables the frequency parameter for the measurement.

            * ``'ON'`` / ``1`` : Enables parameter.
            * ``'OFF'`` / ``0`` : Disables parameter.

        Raises
        ------
        ValueError
            If an invalid state is provided.
        """
        valid_state = self._parse_state(state)
        self.write(":SENSe:VCO:TEST:FREQuency " + valid_state)

    def set_vco_test_noise(self, state: str | int | float | bool) -> None:
        """
        Parameters
        ----------
        state : str | int | float | bool
            Enables/Disables the phase noise parameter for the measurement.

            * ``'ON'`` / ``1`` : Enables parameter.
            * ``'OFF'`` / ``0`` : Disables parameter.

        Raises
        ------
        ValueError
            If an invalid state is provided.
        """
        valid_state = self._parse_state(state)
        self.write(":SENSe:VCO:TEST:PNoise " + valid_state)

    def set_vco_test_power(self, state: str | int | float | bool) -> None:
        """
        Parameters
        ----------
        state : str | int | float | bool
            Enables/Disables the power parameter for the measurement.

            * ``'ON'`` / ``1`` : Enables parameter.
            * ``'OFF'`` / ``0`` : Disables parameter.

        Raises
        ------
        ValueError
            If an invalid state is provided.
        """
        valid_state = self._parse_state(state)
        self.write(":SENSe:VCO:TEST:POWer " + valid_state)

    def set_vco_test_start(self, value: float) -> None:
        """
        Parameters
        ----------
        value : float
            Start tuning voltage for the measurement. Unit: ``'V'``.
        """
        self.write(":SENSe:VCO:VOLTage:STARt " + str(value))

    def set_vco_test_stop(self, value: float) -> None:
        """
        Parameters
        ----------
        value : float
            Stop tuning voltage for the measurement. Unit: ``'V'``.
        """
        self.write(":SENSe:VCO:VOLTage:STOP " + str(value))

    def set_vco_test_i_supply(self, state: str | int | float | bool) -> None:
        """
        Parameters
        ----------
        state : str | int | float | bool
            Enables/disables the supply current parameter for the measurement.

            * ``'ON'`` / ``1`` : Enables parameter.
            * ``'OFF'`` / ``0`` : Disables parameter.

        Raises
        ------
        ValueError
            If an invalid state is provided.
        """
        valid_state = self._parse_state(state)
        self.write(":SENSe:VCO:TEST:ISUPply " + valid_state)

    def set_vcok_pu_shing(self, state: str | int | float | bool) -> None:
        """
        Parameters
        ----------
        state : str | int | float | bool
            Enables/disables the pushing parameter for the measurement.

            * ``'ON'`` / ``1`` : Enables parameter.
            * ``'OFF'`` / ``0`` : Disables parameter.

        Raises
        ------
        ValueError
            If an invalid state is provided.
        """
        valid_state = self._parse_state(state)
        self.write(":SENSe:VCO:TEST:KPUShing " + valid_state)

    def set_vcokvco(self, state: str | int | float | bool) -> None:
        """
        Parameters
        ----------
        state : str | int | float | bool
            Enables/disables the tune sensitivity parameter for the measurement.

            * ``'ON'`` / ``1`` : Enables parameter.
            * ``'OFF'`` / ``0`` : Disables parameter.

        Raises
        ------
        ValueError
            If an invalid state is provided.
        """
        valid_state = self._parse_state(state)
        self.write(":SENSe:VCO:TEST:KVCO " + valid_state)

    def set_vcotype(self, typ: str) -> None:
        """
        Parameters
        ----------
        typ : str
            Select the DUT type for the measurement.

            * ``'VCO'`` : Fast tuning sensitivity
            * ``'VCXO'`` : Slow tuning sensitivity

        Raises
        ------
        ValueError
            If an invalid type is provided.
        """
        valid_typ = self._check_scpi_param(typ, ["VCO", "VCXO"])
        self.write(":SENSe:VCO:TYPE " + valid_typ)

    def set_vco_test_p_noise(self, state: str | int | float | bool) -> None:
        """
        Parameters
        ----------
        state : str | int | float | bool
            Enables/Disables the phase noise parameter for the measurement.

            * ``'ON'`` / ``1`` : Enables parameter.
            * ``'OFF'`` / ``0`` : Disables parameter.

        Raises
        ------
        ValueError
            If an invalid state is provided.
        """
        valid_state = self._parse_state(state)
        self.write(":SENSe:VCO:TEST:PNoise " + valid_state)

    def set_vco_test_pnoise_off_set(
        self, value1: float = 0, value2: float = 0, value3: float = 0, value4: float = 0
    ) -> None:
        """
        Sets up to 4 offset frequencies at which the phase noise is measured.
        At least 1 parameter is required. Blank parameters are set to 0
        (disabled). The query returns the set frequency for the specified
        offset. The offset can be specified with the <sel> parameter and can
        be chosen from 1|2|3|4

        Unit HZ

        Parameters
        ----------
        value1 : float
            Offset 1 frequency. Unit: ``'Hz'``.
        value2 : float
            Offset 2 frequency. Unit: ``'Hz'``.
        value3 : float
            Offset 3 frequency. Unit: ``'Hz'``.
        value4 : float
            Offset 4 frequency. Unit: ``'Hz'``.
        """
        self.write(
            ":SENSe:VCO:TEST:Pnoise:OFFSet "
            + str(value1)
            + ","
            + str(value2)
            + ","
            + str(value3)
            + ","
            + str(value4)
        )

    def set_vco_test_point(self, value: float) -> None:
        """
        Parameters
        ----------
        value : float
            Number of voltage points to use in the measurement.
        """
        self.write(":SENSe:VCO:VOLTage:POINts " + str(value))

    # =============================================================================
    # Get Functions
    # =============================================================================

    # =============================================================================
    # Measurments Examples
    # =============================================================================

    def pn_meas_example(self, value):
        """
        This is a small example how to make a phase noise measurement.
        """

        self.set_sys_meas_mode("PN")  # select phase noise measurement
        self.init()  # start measurement
        self.set_calc_average("ALL")  # wait for the measurement to finish
        err = self.get_system_error()  # check if measurement was successful
        val = self.get_pn_spot(value)  # request spot noise value at 1MHz offset
        result_dict = {}
        result_dict["Error Value"] = err  # Write Error status if 0 no errors!
        result_dict["Spot Phase Noise @ " + str(value)] = val
        return result_dict

    def an_meas_example(self, value):
        """
        This is a small example how to make a phase noise measurement.
        """
        self.set_sys_meas_mode("AN")  # select amplitude noise measurement
        self.init()  # start measurement
        err = self.get_system_error()  # check if measurement was successful
        val = self.get_an_spot(value)  # request spot noise value at 1MHz offset
        result_dict = {}
        result_dict["Error Value"] = err  # Write Error status if 0 no errors!
        result_dict["Spot Amplitude Noise @ " + str(value)] = val
        return result_dict

    def fn_meas_example(self, value):
        """
        This is a small example how to make a frequency noise measurement.
        """
        self.set_sys_meas_mode("FN")  # select amplitude noise measurement
        self.init()  # start measurement
        err = self.get_system_error()  # check if measurement was successful
        val = self.get_fn_spot(value)  # request spot noise value at 1MHz offset
        result_dict = {}
        result_dict["Error Value"] = err  # Write Error status if 0 no errors!
        result_dict["Spot Frequency Noise @ " + str(value)] = val
        return result_dict

    def vco_meas_example(
        self,
        noise_offset_1,
        noise_offset_2,
        meas_points,
        tun_range_min,
        tun_range_max,
        supply_voltage,
        delay,
    ):
        """
        This is a small example how to make a Voltage controlled oscillator noise measurement.
        """

        # Config
        self.set_sys_meas_mode("VCO")  # Select VCO characterization
        self.set_vco_test_freq("ON")  # Enable frequency parameter
        self.set_vco_test_i_supply("ON")  # Enable supply current parameter
        self.set_vcok_pu_shing("ON")  # Enable pushing parameter
        self.set_vcokvco("ON")  # Enable Kvco parameter
        self.set_vco_test_p_noise("ON")  # Enable spot noise parameter
        self.set_vco_test_pnoise_off_set(
            noise_offset_1, noise_offset_2
        )  # Set two spot noise offsets: 1.2kHz, 100kHz
        self.set_vco_test_power("ON")  # Enable power parameter

        # Measurement
        self.set_vcotype("VCO")  # Set DUT Type (VCO or VCXO)
        self.set_vco_test_point(meas_points)  # Set 11 measurement points
        self.set_vco_test_start(tun_range_min)  # Set tuning range minimum to 0.5V
        self.set_vco_test_stop(tun_range_max)  # Set tuning range maximum to 10V
        self.set_dut_port_voltage(supply_voltage)  # Set supply voltage to 6V
        self.set_dut_port_status("ON")  # Enable supply voltage
        self.init()  # Start measurement

        # Loop
        self.set_vco_wait("ALL", delay)  # Wait for the measurement to finish
        err = self.get_system_error()  # Check if measurement was successful
        result_dict = {}

        # Read results
        result_dict["control voltage"] = (
            self.get_vco_trace_voltage()
        )  # request control voltage data array
        result_dict["frequency data"] = self.get_vco_trace_freq()  # Request frequency data array
        result_dict["Kvco data"] = self.get_vcokvco()  # Request Kvco data array
        result_dict["pushing data"] = self.get_vcok_pu_shing()  # Request pushing data array
        result_dict["supply current data"] = (
            self.get_vco_test_i_supply()
        )  # Request supply current data array
        result_dict["power level"] = self.get_vco_trace_power()  # Request power level data array
        result_dict["spot noise data array @offset #1 (1.2kHz)"] = self.get_vco_test_pnoise_off_set(
            1
        )  # Request spot noise data array @offset #1 (1.2kHz)
        result_dict["Error Value"] = err  # Write Error status if 0 no errors!
