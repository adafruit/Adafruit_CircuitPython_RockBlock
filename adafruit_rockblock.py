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

import time
import struct

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_RockBlock.git"


class RockBlock:
    """Driver for RockBLOCK Iridium satellite modem."""

    def __init__(self, uart, baudrate=19200):
        self._uart = uart
        self._uart.baudrate = baudrate
        self._buf_out = None
        self.reset()

    def _uart_xfer(self, cmd):
        """Send AT command and return response as tuple of lines read."""

        self._uart.reset_input_buffer()
        self._uart.write(str.encode("AT" + cmd + "\r"))

        resp = []
        line = self._uart.readline()
        resp.append(line)
        while not any(EOM in line for EOM in (b"OK\r\n", b"ERROR\r\n")):
            line = self._uart.readline()
            resp.append(line)

        self._uart.reset_input_buffer()

        return tuple(resp)

    def reset(self):
        """Perform a software reset."""
        self._uart_xfer("&F0")  # factory defaults
        self._uart_xfer("&K0")  # flow control off

    @property
    def data_out(self):
        "The binary data in the outbound buffer."
        return self._buf_out

    @data_out.setter
    def data_out(self, buf):
        if buf is None:
            # clear the buffer
            resp = self._uart_xfer("+SBDD0")
            resp = int(resp[1].strip().decode())
            if resp == 1:
                raise RuntimeError("Error clearing buffer.")
        else:
            # set the buffer
            if len(buf) > 340:
                raise RuntimeError("Maximum length of 340 bytes.")
            self._uart.write(str.encode("AT+SBDWB={}\r".format(len(buf))))
            line = self._uart.readline()
            while line != b"READY\r\n":
                line = self._uart.readline()
            # binary data plus checksum
            self._uart.write(buf + struct.pack(">H", sum(buf)))
            line = self._uart.readline()  # blank line
            line = self._uart.readline()  # status response
            resp = int(line)
            if resp != 0:
                raise RuntimeError("Write error", resp)
            # seems to want some time to digest
            time.sleep(0.1)
        self._buf_out = buf

    @property
    def text_out(self):
        """The text in the outbound buffer."""
        text = None
        # TODO: add better check for non-text in buffer
        # pylint: disable=broad-except
        try:
            text = self._buf_out.decode()
        except Exception:
            pass
        return text

    @text_out.setter
    def text_out(self, text):
        if not isinstance(text, str):
            raise ValueError("Only strings allowed.")
        if len(text) > 120:
            raise ValueError("Text size limited to 120 bytes.")
        self.data_out = str.encode(text)

    @property
    def data_in(self):
        """The binary data in the inbound buffer."""
        data = None
        if self.status[2] == 1:
            resp = self._uart_xfer("+SBDRB")
            data = resp[0].splitlines()[1]
            data = data[2:-2]
        return data

    @data_in.setter
    def data_in(self, buf):
        if buf is not None:
            raise ValueError("Can only set in buffer to None to clear.")
        resp = self._uart_xfer("+SBDD1")
        resp = int(resp[1].strip().decode())
        if resp == 1:
            raise RuntimeError("Error clearing buffer.")

    @property
    def text_in(self):
        """The text in the inbound buffer."""
        text = None
        if self.status[2] == 1:
            resp = self._uart_xfer("+SBDRT")
            try:
                text = resp[2].strip().decode()
            except UnicodeDecodeError:
                pass
        return text

    @text_in.setter
    def text_in(self, text):
        self.data_in = text

    def satellite_transfer(self, location=None):
        """Initiate a Short Burst Data transfer with satellites."""
        status = (None,) * 6
        if location:
            resp = self._uart_xfer("+SBDIX=" + location)
        else:
            resp = self._uart_xfer("+SBDIX")
        if resp[-1].strip().decode() == "OK":
            status = resp[-3].strip().decode().split(":")[1]
            status = [int(s) for s in status.split(",")]
            if status[0] <= 8:
                # outgoing message sent successfully
                self.data_out = None
        return tuple(status)

    @property
    def status(self):
        """Return tuple of Short Burst Data status."""
        resp = self._uart_xfer("+SBDSX")
        if resp[-1].strip().decode() == "OK":
            status = resp[1].strip().decode().split(":")[1]
            return tuple([int(a) for a in status.split(",")])
        return (None,) * 6

    @property
    def model(self):
        """Return modem model."""
        resp = self._uart_xfer("+GMM")
        if resp[-1].strip().decode() == "OK":
            return resp[1].strip().decode()
        return None

    def _transfer_buffer(self):
        """Copy out buffer to in buffer to simulate receiving a message."""
        self._uart_xfer("+SBDTC")
