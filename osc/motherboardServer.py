#!/usr/bin/python2

import oscServer as osc
from liblo import make_method, Address, Message
import sys
import logging

logging.basicConfig()


class MotherboardServer(osc.OscServer):
    def __init__(self, stage, port=7969):
        super(MotherboardServer, self).__init__(port)
        self.log = logging.getLogger('motherboard.osc')
        self.stage = stage
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
                if self.stage.sender is None:
                    self.stage.sender = sender
                self.stage.unparkAll()
            elif '/parkAll' in path:
                if self.stage.sender is None:
                    self.stage.sender = sender
                self.stage.parkAll()
            elif '/parkSolo' in path:
                motor, isParked = args
                retour = self.stage.parkSolo(motor, isParked)
                msgEtatParkage = Message("/config/stage/parkSoloReturn" + str(motor))
                msgEtatParkage.add(retour)
                self.send(self.stage.sender, msgEtatParkage)
            elif '/resetAll' in path:
                self.stage.resetAll()
            elif '/moveMotor' in path:
                motor, speed = args
                rtn = self.stage.moveMotor(motor, speed)
                #if rtn == "sendParkReturn":
                    #msgEtatParkage = Message("/config/stage/parkSoloReturn" + str(motor))
                    #msgEtatParkage.add(True)
                    #self.send(self.toClass.sender,msgEtatParkage)
                if (rtn is not None and rtn != False and rtn != True and self.stage.sender is not None):
                    msgDistanceDeBase = Message("/config/stage/distanceDeBase" + str(motor))
                    msgDistanceDeBase.add(rtn)
                    self.send(self.stage.sender, msgDistanceDeBase)
            elif '/lockPosition' in path:
                motor, position = args
                self.stage.lockPosition(motor, position)
            elif '/setMinAcceleration' in path:
                motor, pourcentage = args
                self.stage.setMinAcceleration(motor, pourcentage)
            elif '/setMaxAcceleration' in path:
                motor, pourcentage = args
                self.stage.setMaxAcceleration(motor, pourcentage)
            elif '/setMinMargeVitesse' in path:
                motor, pourcentage = args
                self.stage.setMinMargeVitesse(motor, pourcentage)
            elif '/setMaxMargeVitesse' in path:
                motor, pourcentage = args
                self.stage.setMaxMargeVitesse(motor, pourcentage)
            elif '/setReductionVitesse' in path:
                isSet, = args
                if (isSet == 1):
                    self.stage.reductionVitesse = True
                    self.log.info("Reduction de vitesse activee")
                elif (isSet == 0):
                    self.stage.reductionVitesse = False
                    self.log.info("Reduction de vitesse desactivee")


    @make_method('/config/stage/setMargeDestination', 'ff')
    def setMargeDestination(self, path, args, types, sender):
            motor, value = args
            if value < 0.05:
                value = 0.05
                self.log.error("Depassement - de la limite de marge d'erreur")
            elif value > 0.1:
                value = 0.1
                self.log.error("Depassement  + de la limite de marge d'erreur ")
            self.log.info("Changement de la marge d'erreur a " + str(value) + " pour le moteur " + str(motor))
            self.stage.margeError[int(motor)] = value

    @make_method(None, None)
    def defaultCallback(self, path, args, types, sender):
        self.log.warn('Unknown command: %s %s' % (path, ','.join([str(i) for i in args])))
        # self.heartbeat(sender, False)


