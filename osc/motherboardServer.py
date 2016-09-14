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
        self.log.info('Le service des moteurs demarre.')
        super(MotherboardServer, self).start()

    @make_method('/config/stage/moveMotor', 'if')
    @make_method('/config/stage/lockPosition', 'if')
    @make_method('/config/stage/setMinAcceleration', 'if')
    @make_method('/config/stage/setMaxAcceleration', 'if')
    @make_method('/config/stage/setMinMargeVitesse', 'if')
    @make_method('/config/stage/setMaxMargeVitesse', 'if')
    @make_method('/config/stage/parkSolo', 'ii')
    @make_method('/config/stage/unpark', 'i')
    @make_method('/config/stage/setReductionVitesse', 'i')
    @make_method('/config/stage/parkAll', None)
    @make_method('/config/stage/unparkAll', None)
    @make_method('/config/stage/resetAll', None)
    # @make_method('/config/stage/stopAll', None)
    def configStageCallback(self, path, args, types, sender):
        if '/stage' in path:
            if '/unparkAll' in path:
                if self.toClass.sender == None:
                    self.toClass.sender = sender
                self.toClass.unparkAll()
            elif '/parkAll' in path:
                if self.toClass.sender == None:
                    self.toClass.sender = sender
                self.toClass.parkAll()
            elif '/parkSolo' in path:
                motor, isParked = args
                retour = self.toClass.parkSolo(motor,isParked)
                msgEtatParkage = Message("/config/stage/parkSoloReturn" + str(motor))
                msgEtatParkage.add(retour)
                self.send(self.toClass.sender, msgEtatParkage)
            elif '/resetAll' in path:
                self.toClass.resetAll()
            elif '/moveMotor' in path:
                motor, speed = args
                rtn = self.toClass.moveMotor(motor, speed)
                #if rtn == "sendParkReturn":
                    #msgEtatParkage = Message("/config/stage/parkSoloReturn" + str(motor))
                    #msgEtatParkage.add(True)
                    #self.send(self.toClass.sender,msgEtatParkage)
                if (rtn != None and rtn != False and rtn != True and self.toClass.sender != None):
                    msgDistanceDeBase = Message("/config/stage/distanceDeBase" + str(motor))
                    msgDistanceDeBase.add(rtn)
                    self.send(self.toClass.sender, msgDistanceDeBase)
            elif '/lockPosition' in path:
                motor, position = args
                self.toClass.lockPosition(motor, position)
            elif '/setMinAcceleration' in path:
                motor, pourcentage = args
                self.toClass.setMinAcceleration(motor, pourcentage)
            elif '/setMaxAcceleration' in path:
                motor, pourcentage = args
                self.toClass.setMaxAcceleration(motor, pourcentage)
            elif '/setMinMargeVitesse' in path:
                motor, pourcentage = args
                self.toClass.setMinMargeVitesse(motor, pourcentage)
            elif '/setMaxMargeVitesse' in path:
                motor, pourcentage = args
                self.toClass.setMaxMargeVitesse(motor, pourcentage)
            elif '/setReductionVitesse' in path:
                isSet, = args
                if (isSet == 1):
                    self.toClass.reductionVitesse = True
                    self.log.info("Reduction de vitesse activee")
                elif (isSet == 0):
                    self.toClass.reductionVitesse = False
                    self.log.info("Reduction de vitesse desactivee")


    @make_method(None, None)
    def defaultCallback(self, path, args, types, sender):
        self.log.warn('Unknown command: %s %s' % (path, ','.join([str(i) for i in args])))
        # self.heartbeat(sender, False)
