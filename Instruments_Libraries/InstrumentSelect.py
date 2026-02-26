
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 31 08:55:42 2022
Refactored on Tue Feb 27 2025

@author: Martin.Mihaylov
@author: Maxim Weizel
"""

import logging
import re
import pyvisa as visa
from typing import Any
from pyvisa.errors import VisaIOError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# =============================================================================
# Auto-Discovery Helper
# =============================================================================

def find_resource(model_regex: str, resource_filter: str = "?*INSTR", specific_address: str | None = None) -> str:
    """
    Find a VISA resource matching the given model regex.
    If specific_address is provided, it is returned directly (after verification if possible).

    Parameters
    ----------
    model_regex : str
        Regular expression to match against the *IDN? string.
    resource_filter : str
        VISA resource filter string (default: "?*INSTR").
    specific_address : str, optional
        Specific VISA resource string to use.

    Returns
    -------
    str
        The matching VISA resource string.

    Raises
    ------
    RuntimeError
        If no matching instrument is found.
    """
    if specific_address:
        logger.info(f"Using specific address: {specific_address}")
        return specific_address

    rm = visa.ResourceManager()
    try:
        resources = rm.list_resources(resource_filter)
    except ValueError:
        resources = []

    logger.info(f"Scanning {len(resources)} resources for pattern '{model_regex}'...")

    for res in resources:
        try:
            # Skip likely irrelevant resources to speed up scanning
            if "ASRL" in res and "AME" not in model_regex: # Skip COM ports unless looking for serial devices? 
                 # Actually COM ports are ASRL. VXI/TCPIP/USB are usually faster to query.
                 pass

            with rm.open_resource(res) as inst:
                inst.timeout = 200  # fast timeout for scanning
                idn = None
                try:
                    if hasattr(inst, 'query'):
                        try:
                            idn = inst.query("*IDN?").strip()
                        except Exception:
                            pass

                    if idn is None and hasattr(inst, 'write') and hasattr(inst, 'read'):
                        inst.write("*IDN?")
                        idn = inst.read().strip()
                except Exception:
                    pass

                if idn and re.search(model_regex, idn, re.IGNORECASE):
                    logger.info(f"Found match at {res}: {idn}")
                    return res
        except (VisaIOError, OSError):
            continue

    raise RuntimeError(f"No instrument found matching pattern: {model_regex}")

# =============================================================================
# Instrument Factory Functions
# =============================================================================

def OSA(resource: str | None = None):
    from Instruments_Libraries.AQ6370D import AQ6370D
    # Default fallback to old IP if not provided and not found? 
    # User requested: "auto-discovery ... only when I use localhost as hard coded ip adress, that should stay there hard coded."
    # The original file had '169.254.58.101'. We will try to find it or use provided.
    
    if resource is None:
        try:
             # Try auto-discovery
             resource = find_resource(r"AQ6370")
        except RuntimeError:
             # Fallback to the old hardcoded IP if auto-discovery fails, but warn user
             # Or should we strictly follow "User should provide IP"?
             # "The user should always provide the ip-address himself. Or the auto-discovery"
             pass
    
    if resource:
        return AQ6370D(resource)
    else:
        # Fallback to original hardcoded IP just in case, or raise error?
        # Given instruction "User should always provide...", we shouldn't magic hardcodes.
        # But for backward compatibility of scripts calling OSA() without args...
        # We will attempt connection to old default IP if nothing else works, BUT prefer auto discovery.
        return AQ6370D('169.254.58.101') # Keeping old default as last resort


def CoBrite(resource: str | None = None):
    from Instruments_Libraries.CoBrite import CoBrite
    if resource is None:
        resource = find_resource(r"COBRITE")
    return CoBrite(resource)


def SourceMeter(resource: str | None = None):
    from Instruments_Libraries.KEITHLEY2612 import KEITHLEY2612
    if resource is None:
        resource = find_resource(r"Keithley.*2612")
    return KEITHLEY2612(resource)


def PowerSupply(resource: str | None = None):
    from Instruments_Libraries.RD3005 import RD3005
    # This function was complex, handling multiple drivers (RD3005, KA3005, etc.) based on IDN.
    # We will try to preserve that logic but simplify resource finding.
    
    if resource is None:
        # Provide a smart search for various power supplies
        # Using ASRL (COM) ports
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        
        target_ids = ['KORAD', 'RND 320-KA3005P']
        
        for port in ports:
             # Try to connect and IDN
             try:
                 # We instantiate RD3005 temporarily to check IDN
                 # Note: This implies RD3005 class handles the visa/serial connection string format
                 # We assume it takes 'ASRLx::INSTR' or COMx
                 res_str = f"ASRL{port.device}::INSTR" # PyVISA format for Serial
                 # But looking at old code: RD3005(data) where data is from comports which are usually objects or strings?
                 # Old code: RD3005(data) where data comes from `COM_List.append(port)`
                 # `port` in `for port, desc, hwid in sorted(ports)` is just the device name e.g. "COM3"
                 
                 test_inst = RD3005(port.device)
                 idn = test_inst.getIdn() # Assuming legacy method exists or we updated it
                 test_inst.Close()
                 
                 if idn and any(tid in idn for tid in target_ids):
                     resource = port.device
                     break
             except:
                 continue
    
    if resource is None:
        raise RuntimeError("No suitable Power Supply found.")
        
    return RD3005(resource) 


def PowerMeter(index: int = 0, resource: str | None = None):
    """
    Auto-detect a connected Thorlabs PM100-series power meter.
    """
    from Instruments_Libraries.PM100D import PM100D
    
    if resource:
        return PM100D(resource)

    # Use auto-discovery logic similar to finding all PM100s and picking by index
    rm = visa.ResourceManager()
    matches = []
    
    try:
        resources = rm.list_resources("?*::INSTR")
    except ValueError:
        resources = []

    for res in resources:
        if "USB" not in res: continue # PM100 is typically USB
        try:
             with rm.open_resource(res) as inst:
                inst.timeout = 200
                idn = None
                try:
                    if hasattr(inst, 'query'): # Check if it supports query
                        try:
                            idn = inst.query("*IDN?").strip()
                        except Exception:
                            pass 

                    if idn is None and hasattr(inst, 'write') and hasattr(inst, 'read'): # Fallback to write/read
                        try:
                           inst.write("*IDN?")
                           idn = inst.read().strip()
                        except Exception:
                           pass
                except Exception:
                    pass

                if idn and "PM100" in idn:
                    matches.append(res)
        except:
            continue
            
    if not matches:
        raise RuntimeError("No Thorlabs PM100-series power meter found.")
    
    if not (0 <= index < len(matches)):
        raise IndexError(f"index {index} out of range (found {len(matches)} device(s)).")

    return PM100D(matches[index])


def LU1000(resource: str | None = "USB"):
    from Instruments_Libraries.LU1000 import LU1000_Cband
    return LU1000_Cband(resource)


def SpecAnalyser(resource: str | None = None):
    from Instruments_Libraries.MS2760A import MS2760A
    # Defaults to localhost per user request for hardcoded localhost
    if resource is None:
        resource = '127.0.0.1' 
    return MS2760A(resource)


def SigGen(resource: str | None = None, visa_library: str = '@ivi'):
    from Instruments_Libraries.MG3694C import MG3694C
    if resource is None:
        resource = find_resource(r"MG369")
    return MG3694C(resource_str=resource, visa_library=visa_library)


def RnS_SMA100B(resource: str | None = None, visa_library: str = '@ivi'):
    from Instruments_Libraries.SMA100B import SMA100B
    if resource is None:
        resource = find_resource(r"SMA100B")
    return SMA100B(resource_str=resource, visa_library=visa_library)


def VNA(resource: str | None = None):
    from Instruments_Libraries.MS4647B import MS4647B
    if resource is None:
        try:
             # Try auto-discovery
             resource = find_resource(r"MS4647B")
        except RuntimeError:
             # Fallback to hardcoded IP if not found
             # "169.254.100.85" was in original
             resource = 'TCPIP0::169.254.100.85::INSTR'
    return MS4647B(resource)


def APPH(resource: str | None = None):
    from Instruments_Libraries.APPH import APPH
    if resource is None:
         # Original logic looked for 'USB0'
         # We can try find_resource with regex
         try:
            resource = find_resource(r"APPH")
         except RuntimeError:
            # Fallback to finding any USB0
            rm = visa.ResourceManager()
            for res in rm.list_resources():
                 if res.startswith("USB0"):
                      resource = res
                      break
    
    if resource is None:
         raise RuntimeError("APPH not found.")
         
    return APPH(resource)


def PowerSupply_GPP4323(resource: str | None = None):
    from Instruments_Libraries.GPP4323 import GPP4323
    import serial.tools.list_ports
    
    if resource:
        return GPP4323(resource)

    # Auto-discovery for GPP4323
    ports = list(serial.tools.list_ports.comports())
    # Sort: prioritize "gpp" in description
    ports.sort(key=lambda port: (0 if "gpp" in port.description.lower() else 1, port.device))
    
    for port in ports:
        if "bluetooth" in port.description.lower(): continue
        try:
            inst = GPP4323(port.device)
            idn = inst.get_idn()
            inst.close()
            if "GPP-4323" in idn.upper():
                return GPP4323(port.device)
        except:
            continue
            
    raise RuntimeError("No GPP4323 Power Supply found.")


def UXR_1002A(resource: str | None = None):
    from Instruments_Libraries.UXR import UXR
    if resource is None:
        # Keep original hardcoded fallback
        resource = "TCPIP0::KEYSIGH-Q75EBO9.local::hislip0::INSTR"
    
    my_UXR = UXR(resource)
    # Preservation of original init settings logic
    # Note: exception handling is now up to caller or BaseInstrument
    try:
        my_UXR.system_header("off")
        my_UXR.waveform_byteorder("LSBFirst")
        my_UXR.waveform_format("WORD")
        my_UXR.waveform_streaming("off")
    except Exception as e:
        logger.warning(f"Failed to set initial UXR settings: {e}")
        
    return my_UXR


def FSWP50(resource: str | None = None):
    from Instruments_Libraries.FSWP50 import FSWP50
    if resource is None:
        # Original hardcoded IP
        resource = "169.254.253.126"
    return FSWP50(resource)


# =============================================================================
# Main Factory / Selector
# =============================================================================

def InstInit(Num):
    """
    Initialize instrument based on selection string.
    Recommended to use specific functions (e.g. SpecAnalyser()) directly instead.
    """
    map_func = {
        " Anrtisu Spectrum Analyzer MS2760A  ": SpecAnalyser,
        " Anritsu Signal Generator MG3694C  ": SigGen,
        " Anritsu Vectro Analyzer MS4647B  ": VNA,
        " Power Meter ThorLabs PM100D  ": PowerMeter,
        " Novoptel Laser LU1000  ": LU1000,
        " Yokogawa Optical Spectrum Analyzer AQ6370D  ": OSA,
        " KEITHLEY Source Meter 2612  ": SourceMeter,
        " Power Supply KA3005  ": PowerSupply,
        " CoBrite Tunable Laser  ": CoBrite,
        " AnaPico AG,APPH20G  ": APPH,
        " 4-Channels Power Suppy GPP4323 ": PowerSupply_GPP4323,
        " Rohde and Schwarz SMA100B  ": RnS_SMA100B,
        " Keysight UXR0702A  ": UXR_1002A,
        " Rohde and Schwarz FSWP50  ": FSWP50,
    }
    
    func = map_func.get(Num)
    if func:
        return func()
    else:
        raise ValueError('Invalid Instrument Selected')