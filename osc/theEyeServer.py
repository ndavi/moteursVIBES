#!/usr/bin/python2

import oscServer as osc
from liblo import make_method, Address, Message
import sys
import logging
logging.basicConfig()


class TheEyeServer(osc.OscServer):
    def __init__(self):
        super(TheEyeServer, self).__init__(7970)
        self.log = logging.getLogger('theEyeServer')
        self.log.setLevel(logging.DEBUG)
        self.feedback = True
        self.feedbackPort = 7969

        self.motherboard = None

    def start(self):
        self.log.info('theEyeServer is starting...')
        super(TheEyeServer, self).start()

    def isItMother(self, sender):
        return True
        #if self.motherboard:
        #    if self.motherboard.get_hostname() == sender.get_hostname():
        #        return True
        #    self.send(sender, '/theEye/config/auth/youCantDoThis')
        #    self.log.info('You can\'t do this...')
        #else:
        #    self.send(sender, '/theEye/config/auth/youAreNotLogged')
        #    self.heartbeatf(sender, False, 'theEye')
                #    self.log.info('Nobody is logged...')
        #return False

    @make_method('/theEye/config/auth', None)
    @make_method('/theEye/config/wifi', None)
    def authCallback(self, path, args, types, sender):
        if '/auth' in path:
            if not self.motherboard:
                self.motherboard = sender
                self.send(self.motherboard, '/theEye/config/auth/youAreMyMaster')
                self.log.info('%s is logged in.' % self.motherboard.get_hostname())
                self.heartbeat(sender, True, 'theEye')
            else:
                self.send(sender, '/theEye/config/auth/youAreMyMaster')
                self.heartbeat(sender, False, 'theEye')
        elif '/wifi' in path:
            if self.isItMother(sender):
                ssidCmd = Message('/theEye/config/wifi/ssid')
                ssidCmd.add('PedroParamo')
                qualityCmd = Message('/theEye/config/wifi/quality')
                qualityCmd.add(-89)
                self.log.info('Sending wifi stats.')
                self.send(sender, ssidCmd)
                self.send(sender, qualityCmd)
                self.heartbeat(sender, True, 'theEye')

    @make_method('/theEye/led', 'i')
    def ledCallback(self, path, args, types, sender):
        if self.isItMother(sender):
            ledLevel, = args
            self.led = ledLevel
            self.log.info('Led set to %i' % ledLevel)
            self.heartbeat(sender, True, 'theEye')

    @make_method('/theEye/pan', 'i')
    @make_method('/theEye/pan/setZero', None)
    def panCallback(self, path, args, types, sender):
        if self.isItMother(sender):
            if '/setZero' in path:
                self.log.info('This position is now my zero.')
                self.heartbeat(sender, True, 'theEye')
            else:
                pan, = args
                self.log.info('Pan set to: %i' % (pan))
                self.heartbeat(sender, True, 'theEye')

    @make_method('/theEye/motors/enabled', 'i')
    @make_method('/theEye/motors/mode', 'i')
    def motorsCallback(self, path, args, types, sender):
        if self.isItMother(sender):
            state, = args
            if '/enabled' in path:
                state = bool(state)
                self.log.info('Motors set to: %i' % (state))
                self.heartbeat(sender, True, 'theEye')

    @make_method(None, None)
    def defaultCallback(self, path, args, types, sender):
        if self.isItMother(sender):
            self.log.warn('Unknown command: %s' % path)
            self.heartbeat(sender, False, 'theEye')

if __name__ == "__main__":
    theEye = TheEyeServer()
    theEye.start()
    raw_input('Press enter to exit...\n')
