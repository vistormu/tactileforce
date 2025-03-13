import socket
import queue
import json
import threading
import time
from typing import Union

from . import ansi


def exception_handler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return e
    return wrapper


def get_local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))  # Connects to Google's DNS
        ip = s.getsockname()[0]

    except Exception:
        ip = "not found"

    finally:
        s.close()

    return ip


class Server:
    def __init__(self,
                 data_queue: queue.Queue,
                 event_queue: queue.Queue,
                 timeout: float,
                 ) -> None:
        self.socket = None
        self.data_queue = data_queue
        self.event_queue = event_queue

        self.timeout = timeout
        self.client_address = None
        self.last_data_time = 0.0

        self.running = False

    def start(self, host: str, port: int) -> None:
        if host == "auto":
            host = get_local_ip()

        if host == "not found":
            print(
                f"{ansi.BOLD}{ansi.YELLOW_BRIGHT}-> could not find local ip{ansi.RESET}",
                "   |> starting server on localhost",
                "   |> specify ip manually to avoid this message",
                sep="\n",
                end="\n\n",
            )
            host = "localhost"

        self.server_thread = threading.Thread(target=self._start, args=(host, port))
        self.server_thread.start()

    @exception_handler
    def _start(self, host: str, port: int) -> Union[Exception, None]:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((host, port))

        print(
            f"{ansi.BOLD}{ansi.BLUE}-> server started{ansi.RESET}",
            f"   |> host: {host}",
            f"   |> port: {port}",
            sep="\n",
            end="\n\n",
        )

        self.socket.settimeout(0.1)

        self.running = True
        while self.running:
            try:
                data, addr = self.socket.recvfrom(4096)
                now = time.time()
                self.last_data_time = now

                # new client connects
                if self.client_address is None:
                    self.client_address = addr

                    print(
                        f"{ansi.BOLD}{ansi.GREEN}-> client connected{ansi.RESET}",
                        f"   |> ip: {addr[0]}",
                        f"   |> port: {addr[1]}",
                        sep="\n",
                        end="\n\n",
                    )

                    self.event_queue.put("connected")

                self.data_queue.put(json.loads(data.decode('utf-8')))

            except socket.timeout:
                if self.client_address is not None:
                    now = time.time()
                    if now - self.last_data_time > self.timeout:
                        self.event_queue.put("disconnected")

                        print(
                            f"{ansi.BOLD}{ansi.RED}-> client disconnected{ansi.RESET}",
                            f"   |> ip: {self.client_address[0]}",
                            f"   |> port: {self.client_address[1]}",
                            sep="\n",
                            end="\n\n",
                        )

                        self.client_address = None

                continue

    def stop(self) -> None:
        self.running = False
        if not self.socket:
            return

        self.socket.close()
        self.socket = None
        self.server_thread.join()
