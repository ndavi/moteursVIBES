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
        self.margeError = 0.1
        self.motorOffset = 475 # mm
        self.valeurMinVariationVitesse = 0.2
        self.valeurMaxVariationVitesse = 0.8
        self.log = logging.getLogger('stage')
        self.parked = False
        self.lastI = 0
        self.modbusInstance = modbusInstance
        self.DFE33B = self.modbusInstance.dfe
        self.reductionRatio = self.DFE33B.reductionRatio
        self.movidrive = list()
        for mv in self.modbusInstance.movidrive:
            self.movidrive.append(mv)

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
        if not self.testMode:
                self.DFE33B.setStatus(lockAll=True)
        self.parked = True
        self.log.info("Parkage des moteurs")

        return True

    def unparkAll(self):
        if not self.testMode:
            self.DFE33B.setStatus(lockAll=False)
        self.parked = False
        self.log.info("Unparkage des moteurs")
        return True

    def moveMotor(self, i, speed):
        try:
            if self.parked:
                return False
            if speed == 0 or self.movidrive[i].positionAtteinte == True:
                self.movidrive[i].setSpeed(0)
                self.log.debug("Vitesse 0 moteur + " + str(i))
                return True
            positions = self.getPositions()
            positionMoteur = positions[i]
            speed = self.modificationVitesse(speed,i,positionMoteur)
            difference = self.movidrive[i].getLockPosition() - positionMoteur
            self.log.info("Difference : " + str(difference))
            if(difference < self.margeError * -1):
                self.log.debug("Le moteur avance : " + str(difference))
                speed = float(speed) * -1
            if(difference > self.margeError):
                self.log.debug("Le moteur recule : " + str(difference))
            else:
                self.log.debug("Dans la marge d'erreur : " + str(positionMoteur) + " " + str(self.movidrive[i].getLockPosition()))
            if i >= 0 and i < len(self.movidrive):
                self.log.info("Mouvement : " + str(speed) + "moteur : " + str(i))
                self.movidrive[i].setSpeed(int(speed))
                self.lastI = i
                return True
        except Exception as e:
            self.log.debug("Exception dans movemotor : " + e.message)
        return False
    def lockPosition(self, motor, position):
        self.movidrive[motor].setLockPosition(float(position))
        self.log.info("Verouillage a la position : " + str(position))
        self.movidrive[motor].positionAtteinte = False

    def modificationVitesse(self,speed,i,positionMoteur):
        positionVerouillee = self.movidrive[i].getLockPosition()
        pourcentageDistance = positionMoteur / positionVerouillee
        if(pourcentageDistance < self.valeurMinVariationVitesse):
            pourcentage = pourcentageDistance / self.valeurMinVariationVitesse
            if(pourcentage < 0.1):
                pourcentage = 0.1
            rtnVitesse = speed * pourcentage
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

