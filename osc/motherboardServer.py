#!/usr/bin/python2

import oscServer as osc
from liblo import make_method, Address, Message
import sys
import logging
logging.basicConfig()


class MotherboardServer(osc.OscServer):
    def __init__(self, toClass, port=7969):
        super(MotherboardServer, self).__init__(port)
        self.log = logging.getLogger('motherboard.osc')
        self.toClass = toClass
        self.feedback = False
        self.feedbackPort = 7376

        self.gui = None
        self.theEye = None

    def start(self):
        self.log.info('MotherboardServer is starting.')
        super(MotherboardServer, self).start()
        #self.theEye = self.toClass.TheEye.auth()


    def iAmParked(self, state):
        if self.gui:
            iAmParkedMsg = Message('/iAmParked')
            iAmParkedMsg.add(state)
            self.send(self.gui, iAmParkedMsg)


    @make_method('/config/stage/moveMotor', 'if')
    @make_method('/config/stage/lockPosition', 'if')
    @make_method('/config/stage/initialPosition', 'if')
    @make_method('/config/stage/hasChanged', 'f')
    @make_method('/config/stage/stopAll', None)
    @make_method('/config/stage/parkAll', None)
    @make_method('/config/stage/unparkAll', None)
    #@make_method('/config/stage/resetAll', None)
    def configStageCallback(self, path, args, types, sender):
        if '/stage' in path:
            if '/unparkAll' in path:
                self.toClass.sender = sender
                rtn = self.toClass.unparkAll()
                #self.heartbeat(sender, rtn)
            elif '/parkAll' in path:
                self.toClass.sender = sender
                rtn = self.toClass.parkAll()
                #self.heartbeat(sender, rtn)
            elif '/stopAll' in path:
                rtn = self.toClass.stopAll()
                #self.heartbeat(sender, rtn)
            elif '/resetAll' in path:
                rtn = self.toClass.resetAll()
                #self.heartbeat(sender, rtn)
            elif '/moveMotor' in path:
                    motor, speed = args
                    rtn = self.toClass.moveMotor(motor, speed)
                    self.heartbeat(sender, rtn)
                    if rtn != False and rtn != True and rtn != None:
                        self.send(self.toClass.sender,rtn)
                        self.log.info("Envoie du message")
            elif '/lockPosition' in path:
                motor, position = args
                self.toClass.lockPosition(motor,position)
                #self.heartbeat(sender, rtn)
            elif '/hasChanged' in path:
                motor = args
                self.toClass.hasChanged(motor)
                #self.heartbeat(sender, rtn)

    @make_method(None, None)
    def defaultCallback(self, path, args, types, sender):
        self.log.warn('Unknown command: %s %s' % (path, ','.join([str(i) for i in args])))
        #self.heartbeat(sender, False)


if __name__ == '__main__':
    from . import stage
    s = stage.Stage()
    if not s.config.loadLastConfig():
        s.config.load('./conf.sample')
    s.debug = True
    try:
        osc = OscServer(s, 7969)
        osc.feedback = True
    except ServerError, err:
        print str(err)
        sys.exit()

    osc.start()
    print s.getConfig()
    raw_input('press enter to quit...\n')
    osc.stop()
