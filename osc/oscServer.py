#!/usr/bin/python2

from liblo import *
import sys
import logging
logging.basicConfig()
log = logging.getLogger(__name__)


class OscServer(ServerThread):
    def __init__(self, port=7969):
        super(OscServer, self).__init__(port, UDP)
        self.log = logging.getLogger('motherboard.osc')
        self.feedback = False
        self.feedbackPort = 7376
        self.config = None
        self.ready = True

    def start(self):
        self.log.info('Osc thread starting.')
        super(OscServer, self).start()

    def send(self, dst, msg):
        super(OscServer, self).send(Address(dst.get_hostname(), self.feedbackPort), msg)

    def setConfig(self, c):
        for k, l in c:
            if k in ('feedback',):
                if k == 'feedback':
                    self.feedback = bool(*l)

    def getConfig(self):
        rtn = dict()
        rtn.update({'feedback', int(self.feedback), })

        return rtn

    #valeur de retour pour la machine envoyant le signal
    def heartbeat(self, destination, ok=True, src=None):
        if ok:
            state = '/ok'
        else:
            state = '/nok'
        if not src:
            src = 'mother'
        #self.send(destination, '/heartbeat' + state + '/' + src)
