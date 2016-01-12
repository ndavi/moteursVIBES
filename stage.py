#!/usr/bin/python2
# All measures in millimeters
from __future__ import division
import math
import logging
from collections import OrderedDict
import os.path as path
import datetime

from liblo import Message


import logging
logging.basicConfig()


class Stage(object):
    def __init__(self, modbusInstance, testMode=False, plot=False, workingDir=None):
        self.testMode = testMode
        self.plot = plot
        self.workingDir = workingDir
        self.sender = None
        self.storePos = True
        self.margeError = 0.1
        self.motorOffset = 475 # mm
        self.valeurMinVariationVitesse = 0.2
        self.valeurMaxVariationVitesse = 0.8
        self.timeout = datetime.timedelta(seconds=1)

        self.log = logging.getLogger('stage')
        self.config = False
        self.calibrated = False
        self.parked = False
        self.motors = OrderedDict()
        self.lastI = 0

        self.modbusInstance = modbusInstance
        self.DFE33B = self.modbusInstance.dfe

        self.reductionRatio = self.DFE33B.reductionRatio

        self.oscTarget = None

        self.movidrive = list()
        self.motorSpeeds = list()
        for mv in self.modbusInstance.movidrive:
            self.movidrive.append(mv)
            self.motorSpeeds.append(0)

    def resetAll(self):
        if not self.testMode:
            self.DFE33B.setStatus(resetAll=False)
            self.DFE33B.setStatus(resetAll=True)
            self.DFE33B.setStatus(resetAll=False)
        return True

    def stopAll(self):
        if not self.testMode:
            self.DFE33B.setSpeeds(0, 0, 0)
        return True

    def parkAll(self):
        self.absSpeedGui = (0, 0, 0,)
        self.absSpeedCommand = (0, 0, 0,)
        if not self.testMode:
                self.DFE33B.setStatus(lockAll=True)
        self.parked = True

        if self.oscTarget:
            self.oscTarget.iAmParked(int(self.parked))

        return True

    def unparkAll(self):
        self.log.info("passe dans la fonction unpark")
        if not self.testMode:
            self.DFE33B.setStatus(lockAll=False)
        self.parked = False
        if self.oscTarget:
            self.oscTarget.iAmParked(int(self.parked))

        return True

    def moveMotor(self, i, speed):
        try:
            if self.parked:
                return False
            if speed == 0 or self.movidrive[i].positionAtteinte == True:
                self.movidrive[i].setSpeed(0)
                self.log.debug("Vitesse 0 moteur + " + str(i))
                return True
            speed = self.modificationVitesse(speed,i)
            positions = self.getPositions()
            positionMoteur = positions[i]
            difference = self.movidrive[i].getLockPosition() - positionMoteur
            self.log.info("Difference : " + str(difference))
            if(difference < self.margeError * -1):
                self.log.info("Le moteur avance : " + str(difference))
                speed = float(speed) * -1
            if(difference > self.margeError):
                self.log.info("Le moteur recule : " + str(difference))
            else:
                self.log.info("Dans la marge d'erreur : " + str(positionMoteur) + " " + str(self.movidrive[i].getLockPosition()))
            if i >= 0 and i < len(self.movidrive):
                self.log.info("Passe dans la fonction movemotor : " + str(speed) + "moteur" + str(i))
                self.movidrive[i].setSpeed(int(speed))
                self.lastI = i
                return True
        except Exception:
            self.log.info("Exception dans movemotor")
        return False
    def lockPosition(self, motor, position):
        self.movidrive[motor].lastLockPosition = self.movidrive[motor].getLockPosition()
        self.movidrive[motor].setLockPosition(float(position))
        self.log.info("Verouillage a la position : " + str(position) + " " + str(self.movidrive[motor].lastLockPosition))
        self.movidrive[motor].positionAtteinte = False

    def modificationVitesse(self,speed,i):
        positions = self.getPositions()
        positionMoteur = positions[i]
        positionVerouillee = self.movidrive[i].getLockPosition()
        pourcentageDistance = positionMoteur / positionVerouillee
        if(pourcentageDistance < self.valeurMinVariationVitesse):
            pourcentage = pourcentageDistance / self.valeurMinVariationVitesse
            if(pourcentage < 0.1):
                pourcentage = 0.1
            rtnVitesse = speed * pourcentage
            return rtnVitesse
        elif(pourcentageDistance > self.valeurMaxVariationVitesse):
            positionValeurMax = pourcentageDistance - self.valeurMaxVariationVitesse
            valeurMax = 1 - self.valeurMaxVariationVitesse
            pourcentage = positionValeurMax / valeurMax
            if(pourcentage > 0.9):
                pourcentage = 0.9
            rtnVitesse = speed - (speed * pourcentage)
            return rtnVitesse

    @property
    def ready(self):
        return True


    def getPositions(self):
        positions = self.DFE33B.getPositions()
        return positions

    def setSpeed(self):
        for i, d in enumerate(self.deltaLenghts):
            self.motorSpeeds[i] = self.getRpm(d)
            self.log.debug('Movidrive n%i speed (rpm): %f' % (i, self.motorSpeeds[i]))
        if self.testMode is False:
            self.DFE33B.setSpeeds(*self.motorSpeeds)
        return True

    def getRpm(self, d):
        cableSpeed = d / (self.interval / 60)
        cableDrumSpeed = cableSpeed / self.cableDrumPerimeter
        CMP50SSpeed = cableDrumSpeed
        return round(CMP50SSpeed, 2)

