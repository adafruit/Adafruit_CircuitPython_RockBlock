# The MIT License (MIT)
#
# Copyright (c) 2020 Carter Nelson for Adafruit Industries
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
"""
`adafruit_rockblock`
================================================================================

CircuitPython driver for Rock Seven RockBLOCK Iridium satellite modem


* Author(s): Carter Nelson

Implementation Notes
--------------------

**Hardware:**

* `RockBLOCK 9603 Iridium Satellite Modem <https://www.adafruit.com/product/4521>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_RockBlock.git"

class RockBlock:
    '''Driver for RockBLOCK Iridium satellite modem.'''

    def __init__(self, uart, baudrate=19200):
        self._uart = uart
        self._uart.baudrate = baudrate

    def _uart_xfer(self, cmd):
        '''Send AT command and return response.'''
        # response  = ATCMD\r\nRESP\r\n\r\nOK\r\n
        #       or  = ATCMD\r\nERROR\r\n

        cmd = str.encode('AT'+cmd)

        self._uart.reset_input_buffer()
        self._uart.write(cmd+'\r')

        resp = None
        if self._uart.readline().strip() == cmd:
            resp = self._uart.readline().strip().decode()

        self._uart.reset_input_buffer()
        return resp
