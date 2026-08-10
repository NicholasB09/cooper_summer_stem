"""
Background Wi-Fi connection to the ESP32.

Runs in its own thread so the GUI never blocks on network I/O. Incoming bytes
are buffered and split into complete lines and pushed onto a thread-safe queue.
Outgoing commands are queued the same way.
"""

import queue
import threading
import time
import socket

import config


class WiFiManager:
    def __init__(self, ip=None, port=None):
        self.ip = ip or config.ESP32_IP
        self.port = port or config.ESP32_PORT

        # Messages from the ESP32 -> GUI
        self.incoming_queue = queue.Queue()

        # Commands from the GUI -> ESP32
        self._outgoing_queue = queue.Queue()

        self._socket = None
        self._stop_event = threading.Event()
        self.connected = False
        self.active_address = f"{self.ip}:{self.port}"
        
        self.thread = None

    def start(self):
        self._stop_event.clear()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        self._stop_event.set()
        if self.thread is not None:
            self.thread.join(timeout=1.0)
        self._close_socket()

    def send_command(self, command_str):
        """Queue a string to be sent to the ESP32."""
        self._outgoing_queue.put(command_str)

    def _open_socket(self):
        try:
            # Create a TCP socket
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(config.SOCKET_TIMEOUT)
            self._socket.connect((self.ip, self.port))
            
            self.connected = True
            self.incoming_queue.put(("status", "connected", self.active_address))
            return True
        except Exception:
            self._close_socket()
            return False

    def _close_socket(self):
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
        self._socket = None
        self.connected = False

    def _run(self):
        read_buffer = b""
        while not self._stop_event.is_set():
            if self._socket is None:
                if not self._open_socket():
                    time.sleep(config.RECONNECT_DELAY)
                    continue
                read_buffer = b""

            try:
                # 1. Send any waiting outgoing commands
                while not self._outgoing_queue.empty():
                    msg = self._outgoing_queue.get_nowait()
                    self._socket.sendall((msg + "\n").encode("utf-8"))

                # 2. Read incoming data
                try:
                    chunk = self._socket.recv(1024)
                    if not chunk:
                        # An empty chunk means the ESP32 closed the connection
                        raise OSError("Connection closed by server")
                    
                    read_buffer += chunk
                    # Parse full lines from the buffer
                    while b"\n" in read_buffer:
                        line, read_buffer = read_buffer.split(b"\n", 1)
                        text = line.decode("utf-8", errors="ignore").strip()
                        if text:
                            self.incoming_queue.put(("data", text, None))
                            
                except socket.timeout:
                    # Timeout is normal, it just means no new data arrived this cycle.
                    # We pass so the loop continues and we can send outgoing data.
                    pass

            except (OSError, socket.error):
                self.incoming_queue.put(("status", "disconnected", self.active_address))
                self._close_socket()
                time.sleep(config.RECONNECT_DELAY)