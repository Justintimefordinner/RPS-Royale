import socket
import pickle

class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = '172.16.102.146'
        self.port = 1738
        self.addr = (self.host, self.port)
        self.id = self.connect()

    def connect(self):
        self.client.connect(self.addr)
        return pickle.loads(self.client.recv(2048))

    def send(self, data):
        """
        :param data: Object
        :return: Object
        """
        try:
            self.client.send(pickle.dumps(data))
            reply = pickle.loads(self.client.recv(2048))
            return reply
        except socket.error as e:
            return str(e)