#!/usr/bin/python2
# All measures in millimeters
from __future__ import division
import math
import logging
from collections import OrderedDict
import os.path as path
import datetime

from liblo import Message

import theEye
import vectors
from trilateration import Trilateration
import utils

import logging
logging.basicConfig()


class Stage(object):
    def __init__(self, modbusInstance, testMode=False, plot=False, workingDir=None):
        self.testMode = testMode
        self.plot = plot
        self.workingDir = workingDir
        self.lastCoordsPath = path.join(self.workingDir,
                '.last.coords')
        self.sender = None
        self.storePos = True
        self.margeError = 0.1
        self.motorOffset = 475 # mm
        self.xyMaxAcc = 0.005 #m.s.s
        self.xyMaxSpeed = 1 #m.s
        self.zMaxAcc = 0.015 #m.s.s
        self.zMaxSpeed = 1 #m.s

        self.xyMaxAcc *= 1000     # Convert in mm.s.s
        self.xyMaxSpeed *= 1000   # Convert in mm.s
        self.zMaxAcc *= 1000     # Convert in mm.s.s
        self.zMaxSpeed *= 1000   # Convert in mm.s
        self.coeffDs = 0.0001
        if self.testMode is 2:
            self.xyMaxAcc /= 100
            self.xyMaxSpeed /= 100
            self.zMaxAcc /= 100
            self.zMaxSpeed /= 100
            self.coeffDs = 100

        self.distanceDepart = 0.5
        self.minDs = 600 # mm
        self.maxDs = self.minDs + ((self.xyMaxSpeed**2)/2*self.coeffDs*self.xyMaxAcc)
        print self.maxDs
        self.minMotorDs = 3000 # mm
        self.maxMotorDs = self.minMotorDs + ((self.zMaxSpeed**2)/2*self.coeffDs*self.zMaxAcc)
        print self.maxMotorDs
        self.offsetFloor = 377
        self.minFloorDs = 200 + self.offsetFloor # mm
        self.maxFloorDs = self.minFloorDs + ((self.zMaxSpeed**2)/2*self.coeffDs*self.zMaxAcc)
        print self.maxFloorDs

        self.cableDrumDiameter = 134 # mm
        self.cableDiameter = 3 # mm

        self.timeout = datetime.timedelta(seconds=1)
        self.lastGotoTime = datetime.datetime.now()
 

        self.log = logging.getLogger('stage')
        self.config = False
        self.calibrated = False
        self.parked = False
        self.dimensions = (0, 0, 0,)
        self.boundaryOffset = 0
        self.absCoords = (0, 0, 0,)
        self.absCoordsCommand = (0, 0, 0,)
        self.prevAbsSpeedCommand = (0, 0, 0,)
        self.absSpeedCommand = (0, 0, 0,)
        self.absSpeedGui = (0, 0, 0,)
        self.interval = float(1)
        self.absInc = (0, 0, 0,)
        self.initAbsInc = (0, 0, 0,)

        self.trilateration = None
        self.motors = OrderedDict()
        self.lastI = 0

        self.initCableLenghts = (0, 0, 0,)
        self.cableLenghts = [-1, -1, -1,]
        self.deltaLenghts = self.cableLenghts
        self.deltaLenghtsCommand = self.cableLenghts

        if self.plot:
            self.plotVx = list()
            self.plotVy = list()
            self.plotVz = list()
            self.plotX = list()
            self.plotY = list()
            self.plotZ = list()
            self.plotG = list()

        self.cableDrumPerimeter = (math.pi *
                (self.cableDrumDiameter + self.cableDiameter))

        self.modbusInstance = modbusInstance
        self.DFE33B = self.modbusInstance.dfe

        self.log.debug('Cable drum perimeter: %fmm' % self.cableDrumPerimeter)
        self.reductionRatio = self.DFE33B.reductionRatio
        self.incLenghtRatio = self.cableDrumPerimeter

        self.TheEye = theEye.TheEye()
        self.oscTarget = None

        self.movidrive = list()
        self.motorSpeeds = list()
        for mv in self.modbusInstance.movidrive:
            self.movidrive.append(mv)
            self.motorSpeeds.append(0)

    @property
    def ready(self):
        if self.TheEye.ready:
            if self.testMode:
                self.log.warning('Test mode is enabled.')
            return True
        else:
            return False

    def setConfig(self, c):
        for k, l in c:
            if k in ('stage', 'motor0', 'motor1', 'motor2',):
                if k == 'stage':
                    self.setDimensions(*l)
                elif k[0:-1] == 'motor':
                    self.addMotor(*l, i=int(k[-1]))

    def getConfig(self):
        rtn = OrderedDict()
        rtn.update({'stage', self.dimensions, })
        for num, motor in enumerate(self.motors):
            rtn.update({'motor%s' % num: motor, })

        return rtn

    def setDimensions(self, width, depth, height):
        self.dimensions = int(width), int(depth), int(height)
        self.calibrated = False
        self.log.info('Setting new dimensions for stage: %s %s %s' % (width, depth, height))
        if self.config:
            self.config.mergeConfig({'stage': self.dimensions, })
        return True

    def addMotor(self, x, y, z=None, o=None, i=None):
        for dim in self.dimensions:
            if dim == 0:
                self.log.warn('Stage dimensions must be set before adding a motor')
                return False

        if len(self.motors) <= 2 or i is not None:
            if not z:
                z = self.dimensions[2]

            if o:
                motor = (int(x), int(y), int(z), int(o),)
            else:
                motor = (int(x), int(y), int(z), self.motorOffset,)
            if i is None:
                i = len(self.motors)

            dim = self.dimensions
            if dim[0] < motor[0]\
                or dim[1] < motor[1]\
                    or dim[2] < motor[2]:
                self.log.warning('Motor can\'t be outside of stage: x %f y %f z %f o %f' % motor)
                return False

            self.motors.update({i: motor})
            self.cableLenghts[i] = -1

            c = OrderedDict()
            for i, m in self.motors.items():
                key = 'motor%d' % i
                c.update({key: m, })

            self.log.info('Motor added: x %s y %s z %s o %s' % motor)
            if self.config:
                self.config.mergeConfig(c)
            self.calibrated = False
            return True
        else:
            return False

    def deleteMotors(self):
        self.calibrated = False
        self.motors = OrderedDict()
        self.cableLenghts = list()
        self.log.info('Motors deleted')
        return True

    def getMotor(self, num):
        return self.motors.get(num, False)

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

    def calibrate(self):
        self.calibrated = False
        if len(self.motors) != 3:
            return False
        self.trilateration = Trilateration(self.motors[0], self.motors[1], self.motors[2])
        if not self.testMode:
            s = self.DFE33B.setSpeeds(0, 0, 0)
        self.log.info("Starting calibration mode.\n\
        Move each motor to get TheEye centered on stage at %fm high." % (self.minFloorDs / 1000))
        return True

    def calibrateEnd(self):
        if not self.calibrated:
            if self.testMode:
                self.initAbsInc = (0, 0, 0,)
            else:
                s = self.DFE33B.setSpeeds(0, 0, 0)
                self.parkAll()
            if self.testMode is not 2:
                self.initAbsInc = self.getAbsIncs()
            if not self.initAbsInc:
                return False
            self.calibAbsCoords = (self.dimensions[0]/2, self.dimensions[1]/2, self.minFloorDs)
            self.initCableLenghts = (0, 0, 0,)
            self.initCableLenghts = self.getCableLenghtsByCoords(self.calibAbsCoords)
            self.cableLenghts = self.initCableLenghts
            #self.cableLenghtsCommand = self.initCableLenghts

            self.absCoordsFeedback = self.calibAbsCoords
            self.calibrated = True
            self.log.info("End of calibration mode.")
            return True
        return False

    def restoreCalibration(self):
        self.calibrated = False
        if len(self.motors) != 3:
            return False
        self.trilateration = Trilateration(self.motors[0], self.motors[1], self.motors[2])
        if self.testMode is not 2:
            self.initAbsInc = self.getAbsIncs()
            self.parkAll()
        if not self.initAbsInc:
            return False
        strCoords = utils.getLinesFromFile(self.lastCoordsPath)
        print strCoords
        if strCoords:
            calibCoords = [float(c) for c in strCoords[0].split(' ')]
            self.calibAbsCoords = calibCoords
            self.initCableLenghts = (0, 0, 0,)
            self.initCableLenghts = self.getCableLenghtsByCoords(self.calibAbsCoords)
            self.cableLenghts = self.initCableLenghts

            self.absCoordsFeedback = self.calibAbsCoords
            self.calibrated = True
            self.log.info("Calibration restored successfully.")
            return True
        self.log.warning("Unable to restore calibration.")
        return False

    def moveMotor(self, i, speed):
        try:
            if speed == int(0) or self.movidrive[i].positionAtteinte == True:
                self.movidrive[i].setSpeed(0)
                self.log.debug("Vitesse 0 moteur + " + str(i))
                return False
            positions = self.getPositions()
            positionMoteur = positions[i]
            difference = self.movidrive[i].getLockPosition() - positionMoteur
            self.log.info("Difference : " + str(difference))
        #if(self.movidrive[i].getLockPosition() > positionMoteur):
            if(difference < self.margeError * -1):
                self.log.info("Le moteur avance : " + str(difference))
                speed = float(speed) * -1
            #elif(self.movidrive[i].getLockPosition() < positionMoteur):
            if(difference > self.margeError):
                self.log.info("Le moteur recule : " + str(difference))
            #self.movidrive[i].positionAtteinte = True
            else:
                self.log.info("Dans la marge d'erreur : " + str(positionMoteur) + " " + str(self.movidrive[i].getLockPosition()))
        #if(self.movidrive[i].isLocked == True):
            #self.movidrive[i].setSpeed(0)
            #self.log.info("Moteur verouille")
            #return True
            if self.parked:
                return False
            if i >= 0 and i < len(self.movidrive):
                #if(self.movidrive[i].lastLockPosition > self.movidrive[i].getLockPosition()):
                    #speed = int(speed) * -1
                #else:
                #self.log.info("Changement de sens")
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
    def hasChanged(self,motor):
        self.movidrive[motor].isLocked(False)
    def initialPosition(self,motor,position):
        self.movidrive[motor].lastLockPosition = position
        self.log.info("Position initiale : " + str(position))

    def limitSpeed(self):
        Vx, Vy, Vz = self.absSpeedCommand

        # Vi
        V = math.sqrt(math.pow(Vx, 2) + math.pow(Vy, 2))
        VzNorm = math.fabs(Vz)

        if V > self.xyMaxSpeed:
            Vx = (Vx / V) * self.xyMaxSpeed
            Vy = (Vy / V) * self.xyMaxSpeed
        if VzNorm > self.zMaxSpeed:
            Vz = (Vz / VzNorm) * self.zMaxSpeed
        
        self.absSpeedCommand = (Vx, Vy, Vz,)
        self.log.debug('TheEye absolute speed after Vmax limits (mm.s): %f %f %f' % self.absSpeedCommand)
        return True

    def dynConstraints(self):
        Vx, Vy, Vz = self.absSpeedCommand
        Vxy = (Vx, Vy,)
        V = (Vx, Vy, Vz,)
        VxyNorm = vectors.norm(Vxy)

        Ox, Oy, Oz = self.absCoords
        Oxy = (Ox, Oy,)
        O = (Ox, Oy, Oz,)

        M0 = (self.motors[0][0], self.motors[0][1], 0,)
        M1 = (self.motors[1][0], self.motors[1][1], 0,)
        M2 = (self.motors[2][0], self.motors[2][1], 0,)
        M = (M0, M1, M2,)

        Mxy0 = M0[0:2]
        Mxy1 = M1[0:2]
        Mxy2 = M2[0:2]

        Mz0 = self.motors[0][2]
        Mz1 = self.motors[1][2]
        Mz2 = self.motors[2][2]

        M01 = vectors.diff(M1, M0)
        M12 = vectors.diff(M2, M1)
        M20 = vectors.diff(M0, M2)

        uz = (0, 0, 1,)

        n01 = vectors.mul(vectors.cross3D(vectors.div(M01, vectors.norm(M01)), uz), -1)
        n12 = vectors.mul(vectors.cross3D(vectors.div(M12, vectors.norm(M12)), uz), -1)
        n20 = vectors.mul(vectors.cross3D(vectors.div(M20, vectors.norm(M20)), uz), -1)

        Vn01 = vectors.dot(V, n01)
        Vn12 = vectors.dot(V, n12)
        Vn20 = vectors.dot(V, n20)
        
        O0 = vectors.diff(Mxy0, Oxy)
        O1 = vectors.diff(Mxy1, Oxy)
        O2 = vectors.diff(Mxy2, Oxy)

        Doij = list()
        for k, motor in enumerate(M):
            l = k+1
            if k is 2:
                l = 0
            Aij = ((M[l][1] - M[k][1]) / (M[l][0] - M[k][0]))
            Cij = ((M[k][1] - Aij * M[k][0]))
            Doij.append(math.fabs(Aij * Ox - Oy + Cij) / math.sqrt(math.pow(Aij, 2) + 1))

        #Do01 = math.sqrt(math.pow(vectors.norm(O0), 2) - \
        #        math.pow(vectors.dot(O0, vectors.div(M01, vectors.norm(M01))), 2))
        #Do12 = math.sqrt(math.pow(vectors.norm(O1), 2) - \
        #        math.pow(vectors.dot(O1, vectors.div(M12, vectors.norm(M12))), 2))
        #Do20 = math.sqrt(math.pow(vectors.norm(O2), 2) - \
        #        math.pow(vectors.dot(O2, vectors.div(M20, vectors.norm(M20))), 2))
        Dof = Oz
        Dom = min(Mz0, Mz1, Mz2) - Oz

        if self.oscTarget:
            self.oscTarget.iAmAwayFrom(Dof, Dom, *Doij)
            self.oscTarget.iAmGoingToAt(Vn01, Vn12, Vn20)



        Ds01 = ((self.maxDs - self.minDs) / self.xyMaxSpeed) * math.fabs(Vn01) + self.minDs
        Ds12 = ((self.maxDs - self.minDs) / self.xyMaxSpeed) * math.fabs(Vn12) + self.minDs
        Ds20 = ((self.maxDs - self.minDs) / self.xyMaxSpeed) * math.fabs(Vn20) + self.minDs
        Dsof = ((self.maxFloorDs - self.minFloorDs) / self.zMaxSpeed) * math.fabs(Vz) + self.minFloorDs
        Dsom = ((self.maxMotorDs - self.minMotorDs) / self.zMaxSpeed) * math.fabs(Vz) + self.minMotorDs
        Ds01, Ds12, Ds20 = self.minDs, self.minDs, self.minDs
        Dsof = self.minFloorDs
        Dsom = self.maxMotorDs

        if Vn01 > 0 and Doij[0] <= Ds01:
            Vp01 = vectors.mul(vectors.div(M01, vectors.norm(M01)), \
                    vectors.dot(V, vectors.div(M01, vectors.norm(M01))))
            Vx, Vy = Vp01[0:2]
            V = Vx, Vy, Vz
            Vn12 = vectors.dot(V, n12)
            Vn20 = vectors.dot(V, n20)
        if Vn12 > 0 and Doij[1] <= Ds12:
            Vp12 = vectors.mul(vectors.div(M12, vectors.norm(M12)), \
                    vectors.dot(V, vectors.div(M12, vectors.norm(M12))))
            Vx, Vy = Vp12[0:2]
            V = Vx, Vy, Vz
            Vn01 = vectors.dot(V, n01)
            Vn20 = vectors.dot(V, n20)
        if Vn20 > 0 and Doij[2] <= Ds20:
            Vp20 = vectors.mul(vectors.div(M20, vectors.norm(M20)), \
                    vectors.dot(V, vectors.div(M20, vectors.norm(M20))))
            Vx, Vy = Vp20[0:2]
            V = Vx, Vy, Vz
            Vn01 = vectors.dot(V, n01)
            Vn12 = vectors.dot(V, n12)

        if Vn01 > 0 and Doij[0] <= Ds01 and Vn12 > 0 and Doij[1] <= Ds12:
            Vx, Vy = 0, 0
            V = Vx, Vy, Vz
            Vn01 = vectors.dot(V, n01)
            Vn12 = vectors.dot(V, n12)
        if Vn12 > 0 and Doij[1] <= Ds12 and Vn20 > 0 and Doij[2] <= Ds20:
            Vx, Vy = 0, 0
            V = Vx, Vy, Vz
            Vn01 = vectors.dot(V, n01)
            Vn12 = vectors.dot(V, n12)
        if Vn20 > 0 and Doij[2] <= Ds20 and Vn01 > 0 and Doij[0] <= Ds01:
            Vx, Vy = 0, 0
            V = Vx, Vy, Vz
            Vn01 = vectors.dot(V, n01)
            Vn12 = vectors.dot(V, n12)

        if Vz < 0 and Dof <= Dsof:
            Vz = 0
        if Vz > 0 and Dom <= Dsom:
            Vz = 0

        self.absSpeedCommand = (Vx, Vy, Vz,)
        self.limitSpeed()

        self.log.debug('TheEye absolute speed after dynamic constraints (mm.s): %f %f %f' % self.absSpeedCommand)
        return True

    def limitAccDec(self):
        Vxp, Vyp, Vzp = self.prevAbsSpeedCommand
        Vx, Vy, Vz = self.absSpeedCommand

        GammaX = (Vx - Vxp) / self.interval
        GammaY = (Vy - Vyp) / self.interval
        GammaZ = (Vz - Vzp) / self.interval

        self.GammaXY = math.sqrt(math.pow(GammaX, 2) + math.pow(GammaY, 2))
        self.GammaZ = math.sqrt(math.pow(GammaZ, 2))

        if self.GammaXY > self.xyMaxAcc:
            GammaX = (GammaX / self.GammaXY) * self.xyMaxAcc
            GammaY = (GammaY / self.GammaXY) * self.xyMaxAcc

            Vx = Vxp + GammaX * self.interval
            Vy = Vyp + GammaY * self.interval

        if self.GammaZ > self.zMaxAcc:
            GammaZ = (GammaZ / self.GammaZ) * self.zMaxAcc

            Vz = Vzp + GammaZ * self.interval

        self.absSpeedCommand = (Vx, Vy, Vz,)
        self.log.debug('TheEye absolute speed after AccDec limits (mm.s): %f %f %f' % self.absSpeedCommand)
        return True

    def resolvedAbs(self):
        xP, yP, zP = self.absCoords
        Vx, Vy, Vz = self.absSpeedCommand

        xN = xP - Vx * self.interval
        yN = yP - Vy * self.interval
        zN = zP - Vz * self.interval

        if self.testMode is 2:
            xN = xP + Vx * self.interval
            yN = yP + Vy * self.interval
            zN = zP + Vz * self.interval

        self.absCoordsCommand = (xN, yN, zN,)
        return True

    def goto(self, Vx, Vy, Vz):
        if self.calibrated is False:
            return False

        if self.parked is True:
            return False

        self.log.debug('Received new speeds: %f %f %f' % (Vx, Vy, Vz))
        self.absSpeedGui = (Vx, Vy, Vz,)
        self.lastGotoTime = datetime.datetime.now()
        return True


    def getAbsIncs(self):
        if self.trilateration:
            self.absInc = self.DFE33B.getPositions()
            if self.absInc is False:
                self.parkAll()
                return False
            self.log.debug('Absolute increments: %f %f %f' % self.absInc)
            return self.absInc
        return False

    def getPositions(self):
        positions = self.DFE33B.getPositions()
        return positions
        #moteur1, moteur2, moteur3 = positions
        #self.log.info(moteur1)
        #for i in positions:
            #self.log.info(i)
    def getRealCableLenghts(self):
        if self.trilateration:
            if self.testMode is 2:
                self.cableLenghts = tuple(self.cableLenghtsCommand)

                self.log.debug('Real cable lenghts: %f %f %f' % self.cableLenghts)
                return True
            elif self.absInc:
                self.cableLenghts = list(self.cableLenghts)
                for i, m in self.motors.items():
                    self.cableLenghts[i] = self.initCableLenghts[i] + \
                            (self.absInc[i] - self.initAbsInc[i]) * \
                            self.incLenghtRatio # + \
                            #m[3]
                self.cableLenghts = tuple(self.cableLenghts)
                return True
        return False

    def getTrilateration(self):
        if self.trilateration:
            if self.absInc:
                self.absCoords = self.trilateration.trilateration(self.cableLenghts)
                if self.absCoords is False:
                    self.parkAll()

                self.log.debug('Real coords: %f %f %f' % self.absCoords)
                strCoords = [str(c) for c in self.absCoords]
                utils.setLinesToFile(self.lastCoordsPath,
                        ' '.join(strCoords))
                return True
            elif self.testMode is 2:
                self.absCoords = self.trilateration.trilateration(self.cableLenghts)
                self.log.debug('Real coords: %f %f %f' % self.absCoords)
                return True
        return False

    def resolve(self):
        self.log.debug('----####----')
        if self.calibrated is False:
            self.log.debug('Stage is not calibrated.')
            return False

        if len(self.motors) != 3:
            self.log.warning('Cannot resolve coords without 3 motors.')
            return False

        self.prevAbsSpeedCommand = self.absSpeedCommand

        if self.absSpeedGui != (0, 0, 0,) and \
                datetime.datetime.now() - self.lastGotoTime > self.timeout:
            self.absSpeedGui = (0, 0, 0,)
            self.log.info('Timeout: Stop.')

        self.absSpeedCommand = self.absSpeedGui
        if not self.testMode is 2:
            if not self.getAbsIncs():
                self.parkAll()
                self.log.warning('Unable to get real increments.')
                return False
        else:
            self.absInc = (0, 0, 0,)
            self.log.debug('Simulated real increments.')

        if not self.getRealCableLenghts():
            self.log.warning('Unable to get real lenghts.')
            return False
        if not self.getTrilateration():
            self.log.warning('Unable to get real coords.')
            return False

        if self.parked is True:
            self.log.debug('Motors are parked !')
            return False

        self.log.debug('Command speed: %f %f %f' % self.absSpeedCommand)
        self.limitSpeed()
        self.dynConstraints()
        self.limitAccDec()
        self.resolvedAbs()
        self.log.debug('Command absolute coords: %f %f %f' % self.absCoordsCommand)

        if self.oscTarget:
            self.absCoordsFeedback = self.absCoords
            self.oscTarget.iAmAt(*self.absCoordsFeedback)
            self.oscTarget.iAmMovingAt(*self.absSpeedCommand)

        if self.plot:
            Vx, Vy, Vz = self.absSpeedCommand
            X, Y, Z = self.absCoords
            print "%f %f %f %f %f %f %f %f" % (Vx, Vy, Vz, X, Y, Z, self.GammaXY, self.GammaZ)
            self.plotVx.append(str(Vx))
            self.plotVy.append(str(Vy))
            self.plotVz.append(str(Vz))
            self.plotX.append(str(X))
            self.plotY.append(str(Y))
            self.plotZ.append(str(Z))

        self.getCableLenghts()
        self.log.debug('Command cable lenghts: %f %f %f' % tuple(self.cableLenghtsCommand))
        self.deltaCableLenghts()
        self.log.debug('Delta cable lenghts: %f %f %f' % tuple(self.deltaLenghtsCommand))
        self.setSpeed()
        return True

    def getCableLenghtsByCoords(self, coords):
        x, y, z = coords
        self.cableLenghtsCommand = list()
        for key, motor in self.motors.items():
            # Resolving with Pythagore 3D + offset
            Xm, Ym, Zm, Om = motor
            self.cableLenghtsCommand.append(math.sqrt(
                math.pow(Xm - x, 2) +
                math.pow(Ym - y, 2) +
                math.pow(Zm - z, 2)) + Om)
        return tuple(self.cableLenghtsCommand)

    def getCableLenghts(self):
        return self.getCableLenghtsByCoords(self.absCoordsCommand)

    def deltaCableLenghts(self):
        for i, prevL in enumerate(self.cableLenghts):
            self.deltaLenghtsCommand[i] = prevL - self.cableLenghtsCommand[i]
            self.log.debug('Movidrive n%i delta cable (mm): %f' % (i, self.deltaLenghtsCommand[i]))

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
    def setEnabled(self):
        self.movidrive


if __name__ == "__main__":
    import time
    import modbus

    stage = Stage(modbus.ModbusBackend(), testMode=2, plot=True)
    stage.log = log
    stage.setDimensions(14100, 7900, 7000)
    stage.addMotor(0, 0, 7000)
    stage.addMotor(6300, 7900, 7000)
    stage.addMotor(14100, 0, 7000)
    stage.calibrate()
    stage.calibrateEnd()
    stage.unparkAll()
    for i in range(800):
        stage.resolve()
        if i is 5:
            stage.goto(-100, 0, 0)
        elif i is 505:
            stage.goto(0, 0, 0)
    #    elif i is 700:
    #        stage.goto(0, 10, 0)
        #elif i is 26:
        #    stage.goto(0, 0, 0)

        time.sleep(stage.interval / 60)

    #print "plot '" + " ".join(stage.plotVx) + "' with lines;"
