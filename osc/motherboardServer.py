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


    @make_method('/config/stage/moveMotor', 'if')
    @make_method('/config/stage/lockPosition', 'if')
    @make_method('/config/stage/setMinAcceleration', 'if')
    @make_method('/config/stage/setMaxAcceleration', 'if')
    @make_method('/config/stage/setMinMargeVitesse', 'if')
    @make_method('/config/stage/setMaxMargeVitesse', 'if')
    @make_method('/config/stage/parkAll', None)
    @make_method('/config/stage/unparkAll', None)
    #@make_method('/config/stage/resetAll', None)
    #@make_method('/config/stage/stopAll', None)
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
            #elif '/stopAll' in path:
                #rtn = self.toClass.stopAll()
                #self.heartbeat(sender, rtn)
            #elif '/resetAll' in path:
                #rtn = self.toClass.resetAll()
            elif '/moveMotor' in path:
                motor, speed = args
                self.toClass.moveMotor(motor, speed)
            elif '/lockPosition' in path:
                motor, position = args
                self.toClass.lockPosition(motor,position)
            elif '/setMinAcceleration' in path:
                motor, pourcentage = args
                self.toClass.setMinAcceleration(motor,pourcentage)
            elif '/setMaxAcceleration' in path:
                motor, pourcentage = args
                self.toClass.setMaxAcceleration(motor,pourcentage)
            elif '/setMinMargeVitesse' in path:
                motor, pourcentage = args
                self.toClass.setMinMargeVitesse(motor,pourcentage)
            elif '/setMaxMargeVitesse' in path:
                motor, pourcentage = args
                self.toClass.setMaxMargeVitesse(motor,pourcentage)

    @make_method(None, None)
    def defaultCallback(self, path, args, types, sender):
        self.log.warn('Unknown command: %s %s' % (path, ','.join([str(i) for i in args])))
        #self.heartbeat(sender, False)