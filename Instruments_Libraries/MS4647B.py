# -*- coding: utf-8 -*-
"""
Created on Mon Dec 13 10:40:31 2021

@author: Martin.Mihaylov
"""


import numpy as np
from .BaseInstrument import BaseInstrument


class MS4647B(BaseInstrument):
    """
    This class uses BaseInstrument to connect to an Anritsu MS4647B VNA.
    """

    def __init__(self, resource_str: str, visa_library: str = '@py', **kwargs):
        """
        Connect to Device and print the Identification Number.
        """
        # Set default read_termination to '\n' to avoid manual splitting of responses
        kwargs.setdefault('read_termination', '\n')
        super().__init__(resource_str, visa_library=visa_library, **kwargs)
        print(self.get_idn())

    # =============================================================================
    # Return to local
    # =============================================================================

    def rtl(self):
        """


        Returns
        -------
        None
        Description: Send all devices to local operation. No query

        """
        self.write("RTL")

    # =============================================================================
    # Ask
    # =============================================================================

    def get_sub_system(self):
        """


        Returns
        -------
        TYPE str
                The :SENSe:HOLD subsystem command sets the hold function for all
                channels on a per-instrument basis

        """

        return self.query(":SENSe:HOLD:FUNCtion?")

    def get_sweep_count(self, ChanNumber):
        """


        Parameters
        ----------
        ChanNumber : int
            Channel Number 1,2,3...

        Raises
        ------
        ValueError
            Error message

        Returns
        -------
        TYPE
           Description: Query only. Outputs the averaging sweep count for the
            indicated channel.

        """

        if type(ChanNumber) == int:
            return float(self.query(":SENS" + str(ChanNumber) + ":AVER:SWE?"))
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def get_test_set(self, ChanNumber):
        """


        Parameters
        ----------
        ChanNumber : int
            Channel Number 1,2,3...

        Raises
        ------
        ValueError
           Error message

        Returns
        -------
        TYPE
            Query State of TS3739.

        """

        if type(ChanNumber) == int:
            return self.query(":SENS" + str(ChanNumber) + ":TS3739:STATe?")
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def get_sys_errors(self):
        """


        Returns
        -------
        TYPE
            Description: Query only. Outputs the number of errors in the error queue.

        """

        return self.query(":SYST:ERR:COUN?")

    def get_stat_operation(self):
        """


        Returns
        -------
        TYPE
                Description: Query only. Outputs the value of the operation status
                condition reg.
                Range: 0 to 32767
                Default Value: 0

        """

        return self.query(":STAT:OPER:COND?")

    def get_stat_operation_register(self):
        """


        Returns
        -------
        TYPE    str
                Sets the value of the operation status enable register.
                Outputs the value of the operation status enable register.

        """

        return self.query(":STATus:OPERation:ENABle?")

    def get_freq_span(self, ChanNumber):
        """


        Parameters
        ----------
        ChanNumber : int
                     Channel Number 1,2,3...

        Raises
        ------
        ValueError
            Error message

        Returns
        -------
        TYPE  : float
                Optional query. Span is automatically calculated as Stop Frequency minus
                Start Frequency. The query returns the resulting span in Hertz.

        """

        if type(ChanNumber) == int:
            return float(self.query(":SENSe" + str(ChanNumber) + ":FREQuency:SPAN?"))
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def get_center_freq(self, ChanNumber):
        """


        Parameters
        ----------
        ChanNumber : int
            Channel Number 1,2,3...

        Raises
        ------
        ValueError
            Error message

        Returns
        -------
        TYPE : float
                Optional query. Center frequency is automatically calculated using Stop Frequency and Start
                Frequency as:

                    Fc = ((Fstop - Fstart)/2) + Fstart

        """

        if type(ChanNumber) == int:
            return float(
                self.query(":SENSe" + str(ChanNumber) + ":FREQuency:CENTer?")
            )
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def get_cw_freq(self, ChanNumber):
        """


        Parameters
        ----------
        ChanNumber : int
            Channel Number 1,2,3...

        Raises
        ------
        ValueError
            Error message

        Returns
        -------
        TYPE : float
            Sets the CW frequency of the indicated channel. Outputs the CW
            frequency of the indicated channel.

            The output parameter is in Hertz.

        """

        if type(ChanNumber) == int:
            return float(self.query(":SENS" + str(ChanNumber) + ":FREQ:CW?"))
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def get_data_freq(self, ChanNumber):
        """


        Parameters
        ----------
        ChanNumber : int
                     Channel Number 1,2,3...

        Raises
        ------
        ValueError
           Error message

        Returns
        -------
        TYPE : str
            Outputs the frequency list for the indicated channel

        """

        if type(ChanNumber) == int:
            return self.query(":SENSe" + str(ChanNumber) + ":FREQuency:DATA?")
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def get_sweep_channel_status(self):
        """


        Returns
        -------
        TYPE : str
            The query outputs the On/Off state of the option to sweep only the active
            channel

        """

        return self.query(":DISP:ACT:CHAN:SWE:STAT?")

    def get_assignet_data_port(self, value):
        """


        Parameters
        ----------
        value : int/float
            the N(ports number) for the .sNp data output.

        Raises
        ------
        ValueError
            Error message

        Returns
        -------
        TYPE : str
            Outputs the data port pair assigned to use when creating an sNp data
            file on the indicated channel.

        """

        value = str(value)
        if value in ["1", "2", "3", "4"]:
            return self.query("FORMat:S" + str(value) + "P:PORT?")
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def get_param_form_in_file(self):
        """
        Outputs the parameter format displayed in an SNP data file.
        """
        return self.query(":FORMat:SNP:PARameter?")

    def get_rf_state(self):
        """


        Returns
        -------
        TYPE : str
            Outputs the RF on/off state in Hold

        """

        return self.query(":SYST:HOLD:RF?")

    def get_set_average_state(self, ChanNumber):
        """


        Parameters
        ----------
        ChanNumber : int
                     Channel Number 1,2,3...

        Raises
        ------
        ValueError
            Error message

        Returns
        -------
        TYPE : str
            Outputs the averaging function on/off status on the indicated channel.

        """

        if type(ChanNumber) == int:
            return self.query(":SENS" + str(ChanNumber) + ":AVER?")
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def get_average_function_type(self, ChanNumber):
        """


        Parameters
        ----------
        ChanNumber : int
            Channel Number 1,2,3...

        Raises
        ------
        ValueError
            Error message

        Returns
        -------
        TYPE : str
            Outputs the averaging function type of point-by-point or sweep-by-sweep.

        """

        if type(ChanNumber) == int:
            return self.query(":SENS" + str(ChanNumber) + ":AVER:TYP?")
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def get_average_count(self, ChanNumber):
        """


        Parameters
        ----------
        ChanNumber : int
                     Channel Number 1,2,3...

        Raises
        ------
        ValueError
            Error message

        Returns
        -------
        TYPE : float
            Outputs the averaging count for the indicated channel.

        """

        if type(ChanNumber) == int:
            return float(self.query(":SENS" + str(ChanNumber) + ":AVER:COUN?"))
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def get_transfer_data(self, name, portNumb):
        """


        Parameters
        ----------
        name : str
            File Name
        portNumb : int
            the N(ports number) for the .sNp data output.

        Returns
        -------
        TYPE : str
            The query outputs the disk file data to the
            GPIB. The file must exist



            Hard coded path on the VNA = 'C:/tmp/'

        """

        path = "C:/tmp/"
        path = str(path) + str(name) + "_.s" + str(portNumb) + "p"
        return self.query(":MMEM:TRAN? " + '"' + path + '"')

    def get_transfer_data_csv(self, name):
        """


        Parameters
        ----------
        name : str
            File Name

        Returns
        -------
        TYPE : str
            The query outputs the disk file data to the
            GPIB. The file must exist



            Hard coded path on the VNA = 'C:/tmp/'

        """

        path = "C:/tmp/"
        path = str(path) + str(name) + "_.csv"
        return self.query(":MMEM:TRAN? " + '"' + path + '"')

    def get_resolution_bw(self, ChanNumber):
        """


        Parameters
        ----------
        ChanNumber : int
            Channel Number 1,2,3...

        Returns
        -------
        TYPE : float
           The command sets the IF bandwidth for the indicated channel. The query outputs the IF
           bandwidth for the indicated channel.

        """

        return float(self.query(":SENS" + str(ChanNumber) + ":BAND?"))

    def get_power_on_port(self, segment, ChanNumber):
        """


        Parameters
        ----------
        segment : int
            Selected Source. Can be from 1-16
        ChanNumber : int
            Channel Number 1,2,3...

        Returns
        -------
        Value: float
            Outputs the power level of the indicated port on the indicated channel.

        """

        stSegment = np.arange(1, 17, 1)
        stChanNumber = np.arange(1, 5, 1)
        if segment in stSegment and ChanNumber in stChanNumber:
            return float(
                self.query(":SOUR" + str(segment) + ":POW:PORT" + str(ChanNumber) + "?")
            )
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def get_smoothing_state(self, ChanNumber):
        """


        Parameters
        ----------
        ChanNumber : int
            Channel Number 1,2,3...

        Returns
        -------
        TYPE
            Query outputs the smoothing on/off status for the indicated channel and active trace.
            1 = ON
            2 = OFF

        """
        return float(self.query(":CALC" + str(ChanNumber) + ":SMO?"))

    def get_display_trace(self):
        """


        Returns
        -------
        TYPE
            Query only. Outputs the Active Channel number.

        """
        return self.query(":DISPlay:WINDow:ACTivate?")

    def get_display_count(self):
        """


        Returns
        -------
        TYPE
            Query the number of displayed channels.

        """
        return float(self.query(":DISP:COUN?"))

    def get_display_title(self):
        """


        Returns
        -------
        TYPE
            Outputs the user title for the channel
            indicated

        """
        return self.query(":DISP:WIND1:TITL?")

    def get_select_parameter(self):
        """


        Returns
        -------
           The query outputs only the selected parameter.

        """

        return self.query(":CALC1:PAR1:DEF?")

    def get_sweep_delay(self):
        """


        Returns
        -------
            Outputs the sweep delay time of the indicated channel.

        """

        return self.query(":SENS1:SWE:DEL?")

    def get_sweep_time(self):
        """


        Returns
        -------
            Outputs the Sweep Time of the indicated  channel.

        """
        return float(self.query(":SENS1:SWE:TIM?"))

    # =============================================================================
    # Set
    # =============================================================================

    def set_clear_average(self, ChanNumber):
        """


        Parameters
        ----------
        ChanNumber : int
            Channel Number 1,2,3...
            Description: Clears and restarts the averaging sweep count of the
            indicated channel.
        Raises
        ------
        ValueError
            Error message

        Returns
        -------
        None

        """

        if type(ChanNumber) == int:
            self.write(":SENS" + str(ChanNumber) + ":AVER:CLE")
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_sub_system_hold(self):
        """


        Returns
        -------
        None
            Sets the hold function for all channels on a per-instrument basis.
            The sweep is stopped.

        """

        self.write(":SENS:HOLD:FUNC HOLD")

    def set_sub_system_sing(self):
        """


        Returns
        -------
        None
            The sweep restarts and sweeps until the end of the
            sweep, at which point it sets the end of sweep status bit and
            stops.

        """

        self.write(":SENS:HOLD:FUNC SING")

    def set_sub_system_cont(self):
        """


        Returns
        -------
        None
            The sweep is sweeping continuously

        """

        self.write(":SENS:HOLD:FUNC CONT")

    def set_display_scale(self):
        """


        Returns
        -------
        None
            Description: Auto scales all traces on all channels.
        """

        self.write(":DISPlay:Y:AUTO")

    def set_ts3739(self, ChanNumber, state):
        """


        Parameters
        ----------
        ChanNumber : int
            Channel Number 1,2,3...
        state : str/int
            The :SENSe{1-16}:TS3739 subsystem commands are used to configure and
            control the VectorStar ME7838x  Broadband/Millimeter-Wave 3738A Test Set.

        Raises
        ------
        ValueError
            Error message

        Returns
        -------
        None

        """

        if type(ChanNumber) == int:
            if state in ["ON", "OFF", 1, 0]:
                self.write(":SENS" + str(ChanNumber) + ":TS3739 " + str(state))
            else:
                raise ValueError("Unknown input! See function description for more info.")
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_clear_error(self):
        """


        Returns
        -------
        None
        Description: Clears the contents of the error queue.

        """

        self.write(":SYST:ERR:CLE")

    def set_display_color_reset(self):
        """


        Returns
        -------
        None
        Resets all colors and inverted colors to their normal default values.

        """

        self.write(":DISP:COL:RES")

    def set_stat_operation_register(self, value):
        """


        Parameters
        ----------
        value : TYPE
            Sets the value of the operation status enable register.
            Outputs the value of the operation status enable register.
            The input parameter is a unitless number.

            Range: 0 to 65535

        Returns
        -------
        None

        """

        value = int(value)
        self.write(":STAT:OPER:ENAB " + str(value))

    def set_start_freq(self, ChanNumber, value):
        """


        Parameters
        ----------
        ChanNumber : int
                     Channel Number 1,2,3...
        value : int/str in form - 10E+9
                Sets the start value of the sweep range of the indicated channel.
                The input parameter is in Hertz, Meters, or Seconds.

        Raises
        ------
        ValueError
            Error message

        Returns
        -------
        None

        """

        if type(ChanNumber) == int:
            self.write(":SENSe" + str(ChanNumber) + ":FREQuency:STARt " + str(value))
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_stop_freq(self, ChanNumber, value):
        """


        Parameters
        ----------
        ChanNumber : int
                     Channel Number 1,2,3...
        value : int/str in form - 10E+9
                Sets the stop value of the sweep range of the indicated channel.
                The input parameter is in Hertz, Meters, or Seconds.

        Raises
        ------
        ValueError
            Error message

        Returns
        -------
        None

        """

        if type(ChanNumber) == int:
            self.write(":SENSe" + str(ChanNumber) + ":FREQuency:STOP " + str(value))
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_center_freq(self, ChanNumber, value):
        """


        Parameters
        ----------
        ChanNumber : int
                     Channel Number 1,2,3...
        value : int/str in form - 10E+9
                Sets the center value of the sweep range of the indicated channel.
                Outputs the center value of the sweep range of the indicated channel

        Raises
        ------
        ValueError
            Error message

        Returns
        -------
        None

        """

        if type(ChanNumber) == int:
            self.write(":SENS" + str(ChanNumber) + ":FREQ:CENT " + str(value))
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_cw_freq(self, ChanNumber, value):
        """


        Parameters
        ----------
        ChanNumber : int
                     Channel Number 1,2,3...
        value : int/str in form - 10E+9
               Sets the CW frequency of the indicated channel. Outputs the CW
               frequency of the indicated channel.

        Raises
        ------
        ValueError
            Error message

        Returns
        -------
        None

        """

        if type(ChanNumber) == int:
            self.write(":SENS" + str(ChanNumber) + ":FREQ:CW " + str(value))
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_sweep_channel_status(self, state):
        """


        Parameters
        ----------
        state : str/int
                The command turns On/Off the option to sweep only the active channel

        Raises
        ------
        ValueError
            Error message

        Returns
        -------
        None

        """

        if state in ["ON", "OFF", 1, 0]:
            self.write(":DISP:ACT:CHAN:SWE:STAT  " + str(state))
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_assignet_data_port(self, ChanNumber, value1, value2):
        """


        Parameters
        ----------
        ChanNumber : int
                     Channel Number 1,2,3...
        value1 : int

        value2 : int

            The command assigns the data port pair to use when creating an sNp
            data file on the indicated channel. The use of Port 3 and/or Port 4
            requires a 4-port VNA instrument

            PORT12 | PORT13 | PORT14 | PORT23 | PORT24 | PORT34

        Raises
        ------
        ValueError
            Error message

        Returns
        -------
        None

        """

        value1 = str(value1)
        value2 = str(value2)
        if type(ChanNumber) == int:
            if value1 in ["1", "2", "3", "4"]:
                self.write(
                    ":CALC"
                    + str(ChanNumber)
                    + ":FORM:S"
                    + str(value1)
                    + "P:PORT PORT"
                    + str(value1)
                    + str(value2)
                )
            else:
                raise ValueError("Unknown input! See function description for more info.")
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_param_form_in_file(self, unit):
        """

        Parameters
        ----------
        unit : str
            Sets the parameter format displayed in an SNP data file.
            Where:
            - LINPH = Linear and Phase
            - LOGPH = Log and Phase
            - REIM = Real and Imaginary Numbers

        Raises
        ------
        ValueError
            Error message

        Returns
        -------
        None

        """

        if unit in ["LINPH", "LOGPH", "REIM"]:
            self.write(":FORM:SNP:PAR " + str(unit))
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_rf_state(self, state):
        """


        Parameters
        ----------
        state : str/int
                Sets the RF on/off state in Hold.

        Raises
        ------
        ValueError
            Error message

        Returns
        -------
        None

        """

        if state in ["ON", "OFF", 1, 0]:
            self.write(":SYST:HOLD:RF " + str(state))
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_set_average_state(self, ChanNumber, state):
        """


        Parameters
        ----------
        ChanNumber : int
                     Channel Number 1,2,3...
        state : int/str
             Turns averaging on/off for the indicated channel (Turns on and Off the averaging for all channels).

        Raises
        ------
        ValueError
            Error message

        Returns
        -------
        None

        """

        if type(ChanNumber) == int:
            if state in ["ON", "OFF", 1, 0]:
                self.write(":SENS" + str(ChanNumber) + ":AVER " + str(state))
            else:
                raise ValueError("Unknown input! See function description for more info.")
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_average_function_type(self, ChanNumber, state):
        """


        Parameters
        ----------
        ChanNumber : int
                     Channel Number 1,2,3...
        state : str
            Sets the averaging function type to point-by-point or sweep-by-sweep.
            POIN | SWE
            Default Value: POIN

        Raises
        ------
        ValueError
            Error message

        Returns
        -------
        None

        """

        if type(ChanNumber) == int:
            if state in ["SWE", "POIN"]:
                self.write(":SENS" + str(ChanNumber) + ":AVER:TYP " + str(state))
            else:
                raise ValueError("Unknown input! See function description for more info.")
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_average_count(self, ChanNumber, value):
        """


        Parameters
        ----------
        ChanNumber : int
                     Channel Number 1,2,3...
        value : int
            Sets the averaging count for the indicated channel. The channel must
            be turned on.
            The input parameter is a unitless number.
            Range: 1 to 1024
            Default Value: 1

        Raises
        ------
        ValueError
            Error message

        Returns
        -------
        None

        """

        value = str(value)
        if type(ChanNumber) == int:
            self.write(":SENS" + str(ChanNumber) + ":AVER:COUN " + str(value))
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_resolution_bw(self, ChanNumber, value):
        """


        Parameters
        ----------
        ChanNumber : int
                     Channel Number 1,2,3...
        value : int/floa/str
           The command sets the IF bandwidth for the indicated channel. The query outputs the IF
           bandwidth for the indicated channel.

        Raises
        ------
        ValueError
            Error message

        Returns
        -------
        None

        """

        value = str(value)
        if type(ChanNumber) == int:
            self.write(":SENS" + str(ChanNumber) + ":BAND " + str(value))
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_power_on_port(self, segment, ChanNumber, value):
        """


        Parameters
        ----------
        segment : int
            Selected Source. Can be from 1-16
        ChanNumber : int
            Channel Number 1,2,3...
        value : int/floa/str
            Sets the power level of the indicated port on the indicated channel.

        Raises
        ------
        ValueError
            Error message

        Returns
        -------
        None

        """

        stSegment = np.arange(1, 17, 1)
        stChanNumber = np.arange(1, 5, 1)
        if segment in stSegment and ChanNumber in stChanNumber:
            self.write(":SOUR" + str(segment) + ":POW:PORT" + str(ChanNumber) + " " + str(value))
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_smoothing_state(self, ChanNumber, state):
        """


        Parameters
        ----------
        ChanNumber : int
            Channel Number 1,2,3...
        state : str/int
            can be int or str form the list ['ON','OFF',1,0]

        Raises
        ------
        ValueError
             Error message

        Returns
        -------
        The command sets the smoothing aperture for the indicated channel and active trace.

        """
        if type(ChanNumber) == int:
            if state in ["ON", "OFF", 1, 0]:
                self.write(":CALC" + str(ChanNumber) + ":SMO " + str(state))
            else:
                raise ValueError("Unknown input! See function description for more info.")
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_smoothing_ape_rture(self, ChanNumber, value):
        """


        Parameters
        ----------
        ChanNumber : int
            Channel Number 1,2,3...
        value : int
            Percentage smoothing between 0 to 100
        Raises
        ------
        ValueError
            Error message

        Returns
        -------
        The command sets the smoothing aperture for the indicated channel and active trace.

        """
        if type(ChanNumber) == int:

            self.write(":CALC" + str(ChanNumber) + "SMO:APER " + str(float(value)))
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_display_trace(self, ChanNumber):
        """


        Parameters
        ----------
        ChanNumber : int
            Channel Number 1,2,3...

        Raises
        ------
        ValueError
            Error message

        Returns
        -------
        The command sets the active channel to the indicated number. When the VNA is set to
        100,000 point mode, the number of channels is

        """
        if type(ChanNumber) == int:

            self.write(":DISP:WIND" + str(ChanNumber) + ":ACT")
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_display_count(self, ChannelNumber):
        """


        Parameters
        ----------
        ChanNumber : int
            Channel Number 1,2,3...

        Raises
        ------
        ValueError
            Error message

        Returns
        -------
        None: Sets the number of displayed channels. When the VNA is in 25,000 point mode, the
        number of channels can only be 1 (one), 2, 3, 4, 6, 8, 9, 10, 12, or 16 channels. If the
        channel display is set to a non-listed number (5, 7, 11, 13, 14, 15), the instrument is set to
        the next higher channel number. If a number of greater than 16 is entered, the
        instrument is set to 16 channels. If the instrument is set to 100,000 points, any input
        results in 1 (one) channel. Outputs the number of displayed channels.

        """
        if type(ChannelNumber) == int:

            self.write(":DISP:COUN " + str(ChannelNumber))
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_display_title(self, ChannelName):
        """


        Parameters
        ----------
        ChanNumber : int
            Channel Number 1,2,3...

        Raises
        ------
        ValueError
            Error message

        Returns
        -------
        None: Sets the user title for the channel indicated.

        """

        if type(ChannelName) == str:
            self.write(":DISP:WIND1:TITL " + ChannelName)
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_select_parameter(self, S_Param):
        """


        Parameters
        ----------
        S_Param : str
            S-Parameter selected.

        Raises
        ------
        ValueError
            Error message

        Returns
        -------
        None: Select an S-Parameter. 16 S-Parameters for 4 Ports config can be selected.

        """
        S_Paramls = [
            "S11",
            "S12",
            "S13",
            "S14",
            "S21",
            "S22",
            "S23",
            "S24",
            "S31",
            "S32",
            "S33",
            "S34",
            "S41",
            "S42",
            "S43",
            "S44",
        ]
        if type(S_Param) == str:
            if S_Param in S_Paramls:
                self.write(":CALC1:PAR1:DEF " + S_Param)
            else:
                raise ValueError("Unknown input! See function description for more info.")
        else:
            raise ValueError("Unknown input! See function description for more info.")

    def set_sweep_delay(self, time):
        """

        Parameters
        ----------
        time : float
            Sets the sweep delay time of the indicated channel.

        Returns
        -------
        None

        """
        self.write(":SENS1:SWE:DEL " + str(time))

    def set_sweep_time(self, time):
        """


        Parameters
        ----------
        time : float
            Sets the Sweep Time of the indicated channel.

        Returns
        -------
        None

        """

        self.write(":SENS1:SWE:TIM " + str(time))

    # =============================================================================
    # Save
    # =============================================================================

    def save_data(self, name, portNumb):
        """


        Parameters
        ----------
        name : str
            File Name
        portNumb : TYPE
                The N(ports number) for the .sNp data output.
                Description: Stores a data file of the type specified by the filename
                extension.No query.


                Hard coded path on the VNA = 'C:/tmp/'

        Returns
        -------
        None

        """

        path = "C:/tmp/"
        path = str(path) + str(name) + "_.s" + str(portNumb) + "p"
        self.write(":MMEM:STOR " + '"' + path + '"')

    def save_data_csv(self, name):
        """


        Parameters
        ----------
        name : str
            File Name
        portNumb : TYPE
                The N(ports number) for the .sNp data output.
                Description: Stores a data file of the type specified by the filename
                extension.No query.


                Hard coded path on the VNA = 'C:/tmp/'

        Returns
        -------
        None

        """

        path = "C:/tmp/"
        path = str(path) + str(name) + "_.csv"
        self.write(":MMEM:STOR " + '"' + path + '"')

    def save_image(self, name):
        """


        Parameters
        ----------
        name : str
            File Name
        portNumb : TYPE
                The N(ports number) for the .sNp data output.
                Description: Stores a data file of the type specified by the filename
                extension.No query.


                Hard coded path on the VNA = 'C:/tmp/'

        Returns
        -------
        None

        """

        path = "C:/tmp/Image/"
        path = str(path) + str(name) + "_.png"
        self.write(":MMEMory:STORe:IMAGe " + '"' + path + '"')

    def delete_data(self, name, portNumb):
        """


        Parameters
        ----------
        name : str
            File Name
        portNumb : TYPE
                The N(ports number) for the .sNp data output.
                Delete a disk, file, or directory. Use caution with this command as there is no recovery
                operation in case of a user mistake or error. No query


                Hard coded path on the VNA = 'C:/tmp/'

        Returns
        -------
        None

        """
        path = "C:/tmp/"
        path = str(path) + str(name) + "_.s" + str(portNumb) + "p"
        self.write(":MMEMory:DEL " + '"' + path + '"')

    def delete_data_csv(self, name):
        """


        Parameters
        ----------
        name : str
            File Name
        portNumb : TYPE
                The N(ports number) for the .sNp data output.
                Delete a disk, file, or directory. Use caution with this command as there is no recovery
                operation in case of a user mistake or error. No query


                Hard coded path on the VNA = 'C:/tmp/'

        Returns
        -------
        None

        """
        path = "C:/tmp/"
        path = str(path) + str(name) + "_.csv"
        self.write(":MMEMory:DEL " + '"' + path + '"')

    def save_transfer_data(self, file, path, name, portNumb):
        """


        Parameters
        ----------
        file : str
                File data extracted from function ask_TransferData
        path : str
            Where on the PC to save the data
        name : str
            Name of the File
        portNumb : int/str
            The N(ports number) for the .sNp data output.

            Write a text File with the transferred data

        Returns
        -------
        None

        """

        readinglines = file.splitlines()
        with open(str(path) + "/" + str(name) + ".s" + str(portNumb) + "p", "w") as f:
            for line in readinglines:
                f.write(line)
                f.write("\n")

    def save_transfer_data_csv(self, file, path, name):
        """


        Parameters
        ----------
        file : str
                File data extracted from function ask_TransferData
        path : str
            Where on the PC to save the data
        name : str
            Name of the File
        portNumb : int/str
            The N(ports number) for the .sNp data output.

            Write a text File with the transferred data

        Returns
        -------
        None

        """

        readinglines = file.splitlines()
        with open(str(path) + "/" + str(name) + ".csv", "w") as f:
            for line in readinglines:
                f.write(line)
                f.write("\n")

    # =============================================================================
    # Aliases
    # =============================================================================
    
    getIdn = BaseInstrument.get_idn
    ask_SubSystem = get_sub_system
    ask_SweepCount = get_sweep_count
    ask_TestSet = get_test_set
    ask_SysErrors = get_sys_errors
    ask_StatOperation = get_stat_operation
    ask_StatOperationRegister = get_stat_operation_register
    ask_FreqSpan = get_freq_span
    ask_CenterFreq = get_center_freq
    ask_CWFreq = get_cw_freq
    ask_DataFreq = get_data_freq
    ask_SweepChannelStatus = get_sweep_channel_status
    ask_AssignetDataPort = get_assignet_data_port
    ask_ParamFormInFile = get_param_form_in_file
    ask_RFState = get_rf_state
    ask_SetAverageState = get_set_average_state
    ask_AverageFunctionType = get_average_function_type
    ask_AverageCount = get_average_count
    ask_TransferData = get_transfer_data
    ask_TransferDataCSV = get_transfer_data_csv
    ask_ResolutionBW = get_resolution_bw
    ask_PowerOnPort = get_power_on_port
    ask_SmoothingState = get_smoothing_state
    ask_DisplayTrace = get_display_trace
    ask_DisplayCount = get_display_count
    ask_DisplayTitle = get_display_title
    ask_SelectParameter = get_select_parameter
    ask_SweepDelay = get_sweep_delay
    ask_SweepTime = get_sweep_time
    

    # =============================================================================
    # Aliases for backward compatibility
    # =============================================================================
    Close = BaseInstrument.close
    SaveDataCSV = save_data_csv
    SaveImage = save_image
    RTL = rtl
    get_ResolutionBW = get_resolution_bw
    SaveData = save_data
    get_SweepDelay = get_sweep_delay
    set_SetAverageState = set_set_average_state
    get_CWFreq = get_cw_freq
    set_ParamFormInFile = set_param_form_in_file
    get_CenterFreq = get_center_freq
    get_RFState = get_rf_state
    set_SweepDelay = set_sweep_delay
    get_TransferDataCSV = get_transfer_data_csv
    get_AverageCount = get_average_count
    set_SmoothingAPERture = set_smoothing_ape_rture
    DeleteDataCSV = delete_data_csv
    set_CenterFreq = set_center_freq
    set_PowerOnPort = set_power_on_port
    get_DisplayTrace = get_display_trace
    SaveTransferData = save_transfer_data
    get_AssignetDataPort = get_assignet_data_port
    set_StopFreq = set_stop_freq
    set_DisplayScale = set_display_scale
    get_SubSystem = get_sub_system
    set_RFState = set_rf_state
    set_ClearError = set_clear_error
    set_SmoothingState = set_smoothing_state
    set_AverageCount = set_average_count
    get_StatOperation = get_stat_operation
    set_DisplayTrace = set_display_trace
    set_AssignetDataPort = set_assignet_data_port
    get_AverageFunctionType = get_average_function_type
    set_CWFreq = set_cw_freq
    set_AverageFunctionType = set_average_function_type
    set_ResolutionBW = set_resolution_bw
    get_PowerOnPort = get_power_on_port
    SaveTransferDataCSV = save_transfer_data_csv
    set_SweepChannelStatus = set_sweep_channel_status
    get_SweepTime = get_sweep_time
    get_StatOperationRegister = get_stat_operation_register
    DeleteData = delete_data
    set_SubSystemSing = set_sub_system_sing
    set_SelectParameter = set_select_parameter
    set_TS3739 = set_ts3739
    get_TransferData = get_transfer_data
    get_DataFreq = get_data_freq
    get_SweepChannelStatus = get_sweep_channel_status
    get_SetAverageState = get_set_average_state
    get_FreqSpan = get_freq_span
    set_SweepTime = set_sweep_time
    set_DisplayTitle = set_display_title
    set_SubSystemCont = set_sub_system_cont
    set_SubSystemHold = set_sub_system_hold
    set_DisplayCount = set_display_count
    get_ParamFormInFile = get_param_form_in_file
    get_SysErrors = get_sys_errors
    get_SelectParameter = get_select_parameter
    set_StartFreq = set_start_freq
    get_SweepCount = get_sweep_count
    set_StatOperationRegister = set_stat_operation_register
    get_DisplayCount = get_display_count
    get_SmoothingState = get_smoothing_state
    set_DisplayColorReset = set_display_color_reset
    get_DisplayTitle = get_display_title
    get_TestSet = get_test_set
    set_ClearAverage = set_clear_average
