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
    def __init__(self, modbusInstance, workingDir=None):
        self.workingDir = workingDir
        self.sender = None
        self.margeError = 0.1
        self.motorOffset = 475 # mm
        self.log = logging.getLogger('stage')
        self.parked = False
        self.lastI = 0
        self.modbusInstance = modbusInstance
        self.DFE33B = self.modbusInstance.dfe
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
    def modificationVitesse(self,speed,i,positionMoteur):
        positionVerouillee = self.movidrive[i].getLockPosition()
        pourcentageDistance = positionMoteur / positionVerouillee
        if(pourcentageDistance < self.movidrive[i].valeurMinVariationVitesse):
            pourcentage = pourcentageDistance / self.movidrive[i].valeurMinVariationVitesse
            if(pourcentage < self.movidrive[i].valeurMinMargeVitesse):
                pourcentage = self.movidrive[i].valeurMinMargeVitesse
            rtnVitesse = speed * pourcentage
        elif(pourcentageDistance > self.movidrive[i].valeurMaxVariationVitesse):
            positionValeurMax = pourcentageDistance - self.movidrive[i].valeurMaxVariationVitesse
            valeurMax = 1 - self.movidrive[i].valeurMaxVariationVitesse
            pourcentage = positionValeurMax / valeurMax
            if(pourcentage > self.movidrive[i].valeurMaxMargeVitesse):
                pourcentage = self.movidrive[i].valeurMaxMargeVitesse
            rtnVitesse = speed - (speed * pourcentage)
        return rtnVitesse
    def lockPosition(self, motor, position):
        self.movidrive[motor].setLockPosition(float(position))
        self.log.info("Verouillage a la position : " + str(position))
        self.movidrive[motor].positionAtteinte = False

    def setMinAcceleration(self,motor,pourcentage):
        self.movidrive[motor].valeurMinVariationVitesse = pourcentage
    def setMaxAcceleration(self,motor,pourcentage):
        self.movidrive[motor].valeurMaxVariationVitesse = pourcentage

    def setMinMargeVitesse(self,motor,pourcentage):
        self.movidrive[motor].valeurMinMargeVitesse = pourcentage
    def setMaxMargeVitesse(self,motor,pourcentage):
        self.movidrive[motor].valeurMaxMargeVitesse = pourcentage

    @property
    def ready(self):
        return True

    def getPositions(self):
        positions = self.DFE33B.getPositions()
        return positions

