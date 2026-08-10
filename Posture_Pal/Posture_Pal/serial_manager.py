"""
Background serial connection to the ESP32.

Runs in its own thread so the GUI never blocks on serial I/O. Incoming bytes
are buffered and split into complete lines (handling lines that arrive in
multiple chunks) and pushed onto a thread-safe queue for the GUI to poll.
Outgoing commands are queued the same way so a single thread owns the serial
port at all times.
"""

import queue
import threading
import time

import serial_manager
import serial.tools.list_ports

import config


class SerialManager:
    def __init__(self, port=None, baud_rate=None):
        self.port = port or config.SERIAL_PORT
        self.baud_rate = baud_rate or config.BAUD_RATE

        # Messages from the ESP32 -> GUI: tuples of (kind, value, extra)
        #   ("data", "okay", None)             -> a recognized/unrecognized signal line
        #   ("status", "connected", "COM5")    -> connection established
        #   ("status", "disconnected", "COM5") -> connection lost, retrying
        #   ("status", "no_port", None)        -> no serial port could be found/opened
        self.incoming_queue = queue.Queue()

        # Commands from the GUI -> ESP32 (e.g. "UNLOCK:confetti")
        self._outgoing_queue = queue.Queue()

        self._serial = None
        self._stop_event = threading.Event()
        self._thread = None

        self.connected = False
        self.active_port = None

    def start(self):
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2)
        self._close_serial()

    def send_command(self, text):
        """Queue a line to be sent to the ESP32. Safe to call from the GUI thread."""
        self._outgoing_queue.put(text)

    # -- internals -----------------------------------------------------

    def _auto_detect_port(self):
        ports = list(serial_manager.tools.list_ports.comports())
        if not ports:
            return None
        keywords = ("esp32", "cp210", "ch340", "silicon labs", "bluetooth", "spp")
        for p in ports:
            if any(k in (p.description or "").lower() for k in keywords):
                return p.device
        return ports[0].device

    def _open_serial(self):
        port = self.port or self._auto_detect_port()
        if not port:
            self.incoming_queue.put(("status", "no_port", None))
            return False
        try:
            self._serial = serial_manager.Serial(port, self.baud_rate, timeout=config.SERIAL_READ_TIMEOUT)
            self.active_port = port
            self.connected = True
            self.incoming_queue.put(("status", "connected", port))
            return True
        except (serial_manager.SerialException, OSError):
            self._serial = None
            self.connected = False
            self.incoming_queue.put(("status", "disconnected", port))
            return False

    def _close_serial(self):
        if self._serial is not None:
            try:
                self._serial.close()
            except Exception:
                pass
        self._serial = None
        self.connected = False

    def _run(self):
        read_buffer = b""
        while not self._stop_event.is_set():
            if self._serial is None:
                if not self._open_serial():
                    time.sleep(config.RECONNECT_DELAY)
                    continue
                read_buffer = b""

            try:
                while not self._outgoing_queue.empty():
                    msg = self._outgoing_queue.get_nowait()
                    self._serial.write((msg + "\n").encode("utf-8"))

                # Read whatever is already available; if nothing is waiting yet,
                # block briefly for at least one byte so we don't busy-loop.
                chunk = self._serial.read(self._serial.in_waiting or 1)
                if chunk:
                    read_buffer += chunk
                    while b"\n" in read_buffer:
                        line, read_buffer = read_buffer.split(b"\n", 1)
                        text = line.decode("utf-8", errors="ignore").strip()
                        if text:
                            self.incoming_queue.put(("data", text, None))
            except (serial_manager.SerialException, OSError):
                self.incoming_queue.put(("status", "disconnected", self.active_port))
                self._close_serial()
                time.sleep(config.RECONNECT_DELAY)