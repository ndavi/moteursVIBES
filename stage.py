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
import config
import time
class Stage(object):
    def __init__(self, modbusInstance, workingDir=None):
        self.workingDir = workingDir
        self.sender = None
        self.timerParkage = [time.time(),time.time(),time.time()]
        self.isTimerActivated = [True,True,True]
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
        self.vitesseMoteurs = [0,0,0]
        self.config = config.Conf(path.join(workingDir,'config.cfg'))
        self.limiteMoteurs = self.config.loadLastConfig()
        print(self.limiteMoteurs)
        print(self.isTimerActivated)
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
        for i in (0,1,2):
            self.timerParkage[i] = time.time()
        return True
    def parkSolo(self,motor,isParked):
        if(isParked == 1):
            self.movidrive[motor].setStatus(lock=True)
            return True
        elif(isParked == 0):
            self.movidrive[motor].setStatus(lock=False)
            return False

    def moveMotor(self, i, speed):
        try:
            positionMoteur = self.movidrive[i].position
            if self.parked or self.movidrive[i].getLockPosition() == None or positionMoteur == None:
                self.movidrive[i].setSpeed(0)
                return False
            if speed == 0 or self.movidrive[i].positionAtteinte == True:
                # try:
                #     if self.isTimerActivated[i] is True and self.movidrive[i].isAutoParked == False:
                #         if((time.time() - self.timerParkage[i]) >= 30):
                #             self.log.info("Parkage automatique du moteur " + str(i))
                #             self.parkSolo(i,True)
                #             self.isTimerActivated[i] = False
                #             self.movidrive[i].isAutoParked = True
                #             return "sendParkReturn"
                #         else:
                #             self.log.info("Timer parkage :" + "Moteur " + str(i) + " " + str(time.time() - self.timerParkage[i]))
                #     elif self.isTimerActivated[i] is False and self.movidrive[i].isAutoParked == False:
                #         self.timerParkage[i] = time.time()
                #         self.isTimerActivated[i] = True
                # except Exception as e:
                #      ex_type, ex, tb = sys.exc_info()
                #      traceback.print_tb(tb)
                #      self.log.info(e.message)

                self.movidrive[i].setSpeed(0)
                distanceDeBase = self.movidrive[i].distanceToLockPosition
            else:
                if(self.movidrive[i].isAutoParked == True):
                    self.movidrive[i].isAutoParked = False
                    self.parkSolo(i,False)
                    self.log.info("Deparkage automatique")
                self.isTimerActivated[i] = False
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
                    self.movidrive[i].sens = "avance"
                    self.log.debug("Le moteur avance : " + str(difference))
                    speed = float(speed) * -1
                if(difference > self.margeError):
                    self.movidrive[i].sens = "recule"
                    self.log.debug("Le moteur recule : " + str(difference))
                else:
                    self.log.debug("Dans la marge d'erreur : " + str(positionMoteur) + " " + str(self.movidrive[i].getLockPosition()))
                if i >= 0 and i < len(self.movidrive):
                    self.vitesseMoteurs[i] = speed
                    self.log.info("Reception de movemotor, Vitesse du  moteur 0 : " + str(self.vitesseMoteurs[0])
                                  + " Vitesse du moteur 1 : " + str(self.vitesseMoteurs[1]) + " Vitesse du moteur 2 : " + str(self.vitesseMoteurs[2]) + "   Ce programme semble concatener")
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
        if float(self.limiteMoteurs["moteur" + str(motor)][0]) - 0.2 > float(position) or float(self.limiteMoteurs["moteur" + str(motor)][1]) + 0.2 < float(position) :
            self.log.info("Depassement de la limite sur le moteur " + str(motor) + " position : " + str(position))
            return False
        self.movidrive[motor].setLockPosition(float(position))
        self.log.info("Verouillage du moteur : " + str(motor) + " a la position : " + str(position))
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
