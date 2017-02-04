import socket
from artnet import packet, STANDARD_PORT, OPCODES, STYLE_CODES
import logging
logging.basicConfig()
log = logging.getLogger(__name__)


class ArtNetSender():
    def __init__(self,address='127.0.0.1', port=6454):
        self.log = logging.getLogger('motherboard.artnet')
        self.address = address
        self.port = port
        self.log.info('Le service artnet est pret')
        self.packet = packet.DmxPacket()


    def sendFrames(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(self.packet.encode(), (self.address, self.port))

    # def setConfig(self, c):
    #     for k, l in c:
    #         if k in ('feedback',):
    #             if k == 'feedback':
    #                 self.feedback = bool(*l)
    #
    # def getConfig(self):
    #     rtn = dict()
    #     rtn.update({'feedback', int(self.feedback), })
    #
    #     return rtn
