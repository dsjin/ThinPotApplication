# -*- coding: utf-8 -*-

"""
Core Application - manage multiplexer connected with Analog Discovery 2
                | receive voltage from sensors to estimate distance
API : wavefroms API
Author: Thatchakon Jom-ud
"""

from ctypes import *
from dwfconstants import *
import sys
import time

class Core():
    hdwf = c_int()
    hzSys = c_double()
    volt = (c_double*1)()
    dwf = object
    distance = lambda self, volt: ((0.0325*(volt**3)) - (0.5832*(volt**2)) + (0.0768*volt) + 9.8164)

    def __init__(self, window):
        self.gui = window
        self.set_library()

    def set_library(self):
        if sys.platform.startswith("win"):
            self.dwf = cdll.dwf
        elif sys.platform.startswith("darwin"):
            self.dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
        else:
            self.dwf = cdll.LoadLibrary("libdwf.so")

    def set_device(self):
        self.dwf.FDwfDeviceOpen(c_int(-1), byref(self.hdwf))
        self.gui.status.emit("AD2: "+self.get_device_status())
        if self.get_device_status() != "Not Connect":
            self.enable_power_supplies(True)
            self.setup_digital_output()

        return False

    def get_device_status(self):
        return "Connected" if (self.hdwf.value != hdwfNone.value) else "Not Connect"

    def enable_power_supplies(self, enable):
        # set up analog IO channel nodes
        # enable positive supply
        self.dwf.FDwfAnalogIOChannelNodeSet(self.hdwf, c_int(0), c_int(0), c_double(True))
        # set voltage to 5 V
        self.dwf.FDwfAnalogIOChannelNodeSet(self.hdwf, c_int(0), c_int(1), c_double(5))
        # enable negative supply
        self.dwf.FDwfAnalogIOChannelNodeSet(self.hdwf, c_int(1), c_int(0), c_double(True))
        # set voltage to -5 V
        self.dwf.FDwfAnalogIOChannelNodeSet(self.hdwf, c_int(1), c_int(1), c_double(-5))
        self.dwf.FDwfAnalogIOEnableSet(self.hdwf, c_int(enable))

    def setup_digital_output(self):
        self.dwf.FDwfDigitalOutInternalClockInfo(self.hdwf, byref(self.hzSys))

        self.dwf.FDwfDigitalOutEnableSet(self.hdwf, c_int(0), c_int(1))
        # prescaler to 2kHz
        self.dwf.FDwfDigitalOutDividerSet(self.hdwf, c_int(0), c_int(int(self.hzSys.value / 2e3)))
        # 1 tick low, 1 tick high
        self.dwf.FDwfDigitalOutCounterSet(self.hdwf, c_int(0), c_int(1), c_int(1))

        self.dwf.FDwfDigitalOutEnableSet(self.hdwf, c_int(1), c_int(1))
        # prescaler to 2kHz
        self.dwf.FDwfDigitalOutDividerSet(self.hdwf, c_int(1), c_int(int(self.hzSys.value / 2e3)))
        # 2 tick low, 2 tick high
        self.dwf.FDwfDigitalOutCounterSet(self.hdwf, c_int(1), c_int(2), c_int(2))

        self.dwf.FDwfDigitalOutEnableSet(self.hdwf, c_int(2), c_int(1))
        # prescaler to 2kHz
        self.dwf.FDwfDigitalOutDividerSet(self.hdwf, c_int(2), c_int(int(self.hzSys.value / 2e3)))
        # 4 tick low, 4 tick high
        self.dwf.FDwfDigitalOutCounterSet(self.hdwf, c_int(2), c_int(4), c_int(4))

        self.dwf.FDwfDigitalOutConfigure(self.hdwf, c_int(1))

    def get_volt_and_distance(self):
        sts = c_byte()

        self.dwf.FDwfAnalogInFrequencySet(self.hdwf, c_double(20000000.0))
        self.dwf.FDwfAnalogInBufferSizeSet(self.hdwf, c_int(4000))
        self.dwf.FDwfAnalogInChannelEnableSet(self.hdwf, c_int(0), c_bool(True))
        self.dwf.FDwfAnalogInConfigure(self.hdwf, c_bool(False), c_bool(True))

        while True:
            self.dwf.FDwfAnalogInStatus(self.hdwf, c_int(1), byref(sts))
            if sts.value == DwfStateDone.value:
                break
            time.sleep(0.1)

        self.dwf.FDwfAnalogInStatusData(self.hdwf, c_int(0), self.volt, 1)
        return self.volt[0], self.distance(self.volt[0])

    def disconnect_ad2(self):
        self.enable_power_supplies(False)
        self.dwf.FDwfDeviceCloseAll()
        self.hdwf = c_int()
        self.gui.status.emit("AD2: Disconnected")
        return False
