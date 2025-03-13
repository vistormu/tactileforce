import socket
import json


class Client:
    def __init__(self, server_host: str, server_port: int) -> None:
        self.server_host = server_host
        self.server_port = server_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send_data(self, data: dict) -> None:
        try:
            json_data = json.dumps(data)
            self.socket.sendto(json_data.encode('utf-8'), (self.server_host, self.server_port))
        except Exception as e:
            print(f"Error sending data: {e}")

    def close(self) -> None:
        self.socket.close()
