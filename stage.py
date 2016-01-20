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
        self.reductionVitesse = True
        self.modbusInstance = modbusInstance
        self.DFE33B = self.modbusInstance.dfe
        self.movidrive = list()
        self.distanceDeBase = 0
        for mv in self.modbusInstance.movidrive:
            self.movidrive.append(mv)

    def parkAll(self):
        self.DFE33B.setStatus(lockAll=True)
        self.parked = True
        self.log.info("Parkage des moteurs")

        return True
    def unparkAll(self):
        self.DFE33B.setStatus(lockAll=False)
        self.parked = False
        self.log.info("Unparkage des moteurs")
        return True

    def moveMotor(self, i, speed):
        try:
            positionMoteur = self.movidrive[i].position
            if self.parked or self.movidrive[i].getLockPosition() == None or positionMoteur == None:
                self.movidrive[i].setSpeed(0)
                return False
            if speed == 0 or self.movidrive[i].positionAtteinte == True:
                self.movidrive[i].setSpeed(0)
                distanceDeBase = self.movidrive[i].distanceToLockPosition
            else:
                difference = self.movidrive[i].getLockPosition() - positionMoteur
                distanceDeBase = self.movidrive[i].distanceToLockPosition
                distanceCalcul = difference
                if(distanceDeBase < 0):
                    distanceDeBase = distanceDeBase * -1
                if(distanceCalcul < 0):
                    distanceCalcul = distanceCalcul * -1
                pourcentageCalcul = distanceCalcul / distanceDeBase
                #self.log.info(str(pourcentageCalcul) + "   " + str(distanceNow) + "   " + str(distanceDeBase))
                if(pourcentageCalcul > 1):
                    pourcentageCalcul = 1
                pourcentageDistance = 1 - pourcentageCalcul
                if(self.reductionVitesse):
                    speed = self.modificationVitesse(speed,i,pourcentageDistance)
                self.log.debug("Difference : " + str(difference))
                if(difference < self.margeError * -1):
                    self.log.debug("Le moteur avance : " + str(difference))
                    speed = float(speed) * -1
                if(difference > self.margeError):
                    self.log.debug("Le moteur recule : " + str(difference))
                else:
                    self.log.debug("Dans la marge d'erreur : " + str(positionMoteur) + " " + str(self.movidrive[i].getLockPosition()))
                if i >= 0 and i < len(self.movidrive):
                    self.log.debug("Mouvement : " + str(speed) + "moteur : " + str(i))
                    self.movidrive[i].setSpeed(int(speed))
                    self.lastI = i
        except Exception as e:
            self.log.info("Exception dans movemotor : " + e.message)
            return False
        return distanceDeBase
    def modificationVitesse(self,speed,i,pourcentageDistance):
        #self.log.info("Apres : " + str(pourcentageDistance) + "val min : " + str(self.movidrive[i].valeurMinVariationVitesse))
        if(pourcentageDistance < self.movidrive[i].valeurMinVariationVitesse):
            pourcentage = pourcentageDistance / self.movidrive[i].valeurMinVariationVitesse
            if(pourcentage < self.movidrive[i].valeurMinMargeVitesse):
                pourcentage = self.movidrive[i].valeurMinMargeVitesse
            rtnVitesse = speed * pourcentage
            self.log.debug("Pourcentage : " + str(pourcentage) + ", vitesse : " + str(rtnVitesse) + "vitesse de base : " + str(speed))
        elif(pourcentageDistance > self.movidrive[i].valeurMaxVariationVitesse):
            positionValeurMax = pourcentageDistance - self.movidrive[i].valeurMaxVariationVitesse
            valeurMax = 1 - self.movidrive[i].valeurMaxVariationVitesse
            pourcentage = positionValeurMax / valeurMax
            if(pourcentage > self.movidrive[i].valeurMaxMargeVitesse):
                pourcentage = self.movidrive[i].valeurMaxMargeVitesse
            rtnVitesse = speed - (speed * pourcentage)
            self.log.debug("Au dessus de 0.8 Pourcentage : " + str(pourcentage) + ", vitesse : " + str(rtnVitesse)+ "vitesse de base : " + str(speed))
        else:
            rtnVitesse = speed
        return rtnVitesse
        #def resetAll(self):
    def resetAll(self):
        self.DFE33B.setStatus(resetAll=False)
        self.DFE33B.setStatus(resetAll=True)
        self.DFE33B.setStatus(resetAll=False)
    def lockPosition(self, motor, position):
        self.movidrive[motor].setLockPosition(float(position))
        self.log.debug("Verouillage a la position : " + str(position))
        self.movidrive[motor].positionAtteinte = False
        positions = self.getPositions()
        positionMoteur = positions[motor]
        difference = position - positionMoteur
        if(difference < 0):
            difference * -1
        self.movidrive[motor].distanceToLockPosition = difference

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

    #def stopAll(self):
    #    if not self.testMode:
    #        self.DFE33B.setSpeeds(0, 0, 0)
    #    return True
