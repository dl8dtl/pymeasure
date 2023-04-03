#
# This file is part of the PyMeasure package.
#
# Copyright (c) 2013-2023 PyMeasure Developers
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

import logging
import re

from pymeasure.instruments import Instrument

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class Fpu60(Instrument):
    """Represents a fpu60 power supply unit for the finesse laser series by Laserquantum,
    a Novanta company."""

    def __init__(self, adapter, name="Laserquantum fpu60 power supply unit", **kwargs):
        super().__init__(adapter,
                         name=name,
                         includeSCPI=False,
                         asrl={'baud_rate': 19200},
                         write_termination="\r",
                         read_termination="\r\n",
                         **kwargs)

    interlock = Instrument.measurement(
        "INTERLOCK?",
        """Measure the interlock enabled status.""",
        values={True: "ENABLED", False: "DISABLED"},
        map_values=True,
    )

    emission_enabled = Instrument.measurement(
        "STATUS?",
        """Measure the emission status.""",
        values={True: "ENABLED", False: "DISABLED"},
        map_values=True,
    )

    power = Instrument.measurement(
        "POWER?",
        """Measure current output power in Watts.""",
        # Response is in form:" ##.###W"
        preprocess_reply=lambda r: r.replace("W", ""),
    )

    power_setpoint = Instrument.control(
        "SETPOWER?", "POWER=%.3f",
        """Control the output power setpoint in Watts.""",
        # Getter response is in form:" ##.###W"
        preprocess_reply=lambda r: r.replace("W", ""),
        check_set_errors=True,
    )

    shutter = Instrument.control(
        "SHUTTER?", "SHUTTER %s",
        """Control the shutter.""",
        # set values: OPEN, CLOSE
        # get response: "SHUTTER OPEN", "SHUTTER CLOSED"
        values={True: "OPEN", False: "CLOSE"},
        map_values=True,
        preprocess_reply=lambda r: r.replace("SHUTTER ", "").replace("D", ""),
        check_set_errors=True,
    )

    current = Instrument.measurement(
        "CURRENT?",
        """Measure the diode current in percent.""",
        # Response: " ###.#%"
        preprocess_reply=lambda r: r.replace("%", ""),
    )

    psu_temperature = Instrument.measurement(
        "PSUTEMP?",
        """Measure the power supply unit temperature in °C.""",
        # Response: " ##.###C"
        preprocess_reply=lambda r: r.replace("C", ""),
    )

    head_temperature = Instrument.measurement(
        "HTEMP?",
        """Measure the laser head temperature in °C.""",
        # Response: " ##.###C"
        preprocess_reply=lambda r: r.replace("C", ""),
    )

    serial = Instrument.measurement("SERIAL?", """Get the serial number""", cast=str)

    software_version = Instrument.measurement("SOFTVER?", """Get the software version.""", cast=str)

    def get_operation_times(self):
        """Get the operation times in minutes as a dictionary."""
        self.write("TIMERS?")
        timers = {}
        timers['psu'] = int(re.search(r"\d+", self.read()).group())
        timers['laser'] = int(re.search(r"\d+", self.read()).group())
        timers['laser_above_1A'] = int(re.search(r"\d+", self.read()).group())
        self.read()  # an empty line is at the end.
        return timers

    def disable_emission(self):
        """Disable emission and unlock the button afterwards.

        You have to press the physical button to enable emission again.
        """
        self.ask("LASER=OFF")
        self.ask("LASER=ON")  # unlocks emission button, does NOT start emission!

    def check_errors(self):
        """Use check_errors to read the responses of setters."""
        # TODO change to check_set_errors, once that is merged.
        self.read()
