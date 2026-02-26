# -*- coding: utf-8 -*-
"""
Created on Mon Aug  1 12:15:19 2022
Refactored by unifying identical Korad Drivers.

@author: Martin.Mihaylov
@author: Maxim Weizel
"""

from .RD3005 import RD3005

class KA3005p(RD3005):
    """
    Unified driver delegating immediately to RD3005, preserving backwards compatibility.
    The KA3005, KA3005p, and RD3005 power supplies are fundamentally identical Korad architectures.
    """
    pass
