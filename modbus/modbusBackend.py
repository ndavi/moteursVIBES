#!/usr/bin/python2

from pymodbus.client.sync import ModbusTcpClient as ModbusClient

from pymodbus.register_read_message import *
from pymodbus.register_write_message import *
from pymodbus.other_message import *
from pymodbus.mei_message import *
from pymodbus.pdu import *

import bitstring

import logging
logging.basicConfig()
log = logging.getLogger(__name__)


class DFE33B(object):
    '''
    Handle all operations requests and responses for DFE33B
    '''

    class _Requests(object):
        '''
        Requests class: basic functions for DFE33B
        '''

        def __init__(self, client):
            ''' Initializes a new instance

            :param client: Modbus client
            '''
            self.client = client

        def execute(self, request):
            ''' Execute reguest

            :param request: Request to execute
            '''
            try:
                return self.client.execute(request)
            except:
                return False

        def getDeviceInformation(self, code=None, obj=None, **kwargs): #FC43
            rq = ReadDeviceInformationRequest(read_code=code, object_id=obj, **kwargs)
            return self.execute(rq)

        def readHoldingRegisters(self, unit_id=0x00, address=None, count=None, **kwargs): #FC3
            rq = ReadHoldingRegistersRequest(address, count, transaction_id=0, unit_id=unit_id, **kwargs)
            return self.execute(rq)

        def writeMultipleRegisters(self, unit_id=0x00, address=None, values=None, **kwargs): #FC16
            rq = WriteMultipleRegistersRequest(address, values, transaction_id=0, unit_id=unit_id, **kwargs)
            return self.execute(rq)

        def readWriteMultipleRegisters(self, unit_id=0x00, address=None, count=None, **kwargs): #FC23
            rq = ReadWriteMultipleRegistersRequest(address, count, transaction_id=0, unit_id=unit_id, **kwargs)
            return self.execute(rq)

        def reportSlaveId(self, **kwargs):
            rq = ReportSlaveIdRequest(**kwargs)
            return self.execute(rq)

    ExceptionCodes = [
            'IllegalFunction',
            'IllegalDataAddress',
            'IllegalDataValue',
            'IllegalDeviceFailure',
            'SlaveDeviceFailure',
            'SlaveDeviceBusy',
            None,
            None,
            None,
            'GatewayPathUnavailable',
            ]

    _faultCodes = {
            0: 'NoFault',
            1: 'ControlerInhibit',
            10: 'NotEnabled',
            101: 'Enabled(N)',
            1110: 'EncoderFault',
            11100: 'FieldbusTimeout',
            1101111: 'StationCannotBeReached',

            }


    def __init__(self):
        ''' Initializes a new instance
        '''
        self.ip = '192.168.0.2'
        self.port = 502

        self.baseOffset = 0x04

        self.nbMovidrives = 3
        self.nbDataProcess = 3
        self.wordLenght = 16
        self.cycleTime = 2 # milliseconds
        self.refreshTime = self.cycleTime * self.nbMovidrives

        self.maxSpeed = 200

        self.client = ModbusClient(self.ip, self.port)
        self.rq = self._Requests(self.client)

        self.dpValuesInput = list()
        self.dpValuesOutput = list()
        self.statusState = list()
        for i in range(self.nbMovidrives):
            for i in range(self.nbDataProcess):
                self.dpValuesInput.append(0)
                self.dpValuesOutput.append(0)
            self.statusState.append([0, 0, 0, 0, 0, 0, 0, 0, 0])

        self.reductionRatio = 12.98
        self.nbMotorInc = 4096
        self.nbOutputInc = self.nbMotorInc * self.reductionRatio

    @property
    def ready(self):
        ''' Return ready state

        Returns True if ModbusClient is connected
        '''
        try:
            self.client.connect()
            return True
        except:
            pass

    def testFunctionCode(self, response, count=None):
        if count is None:
            count= self.nbMovidrives
        ''' Handle responses and returns address, count, values or exception code

        :param response: Response to analyze
        '''
        if response:
            if type(response) == ExceptionResponse:
                return 'ExceptionCode', response.function_code, self.ExceptionCodes[response.exception_code-1]
            elif type(response) == WriteMultipleRegistersResponse:
                if response.function_code != 0x83:
                    return 'WriteRegisters', response.address, response.count
                else:
                    return 'Error'
            elif type(response) == ReadHoldingRegistersResponse:
                registers = list()
                fmt = "{:0>"+str(self.wordLenght)+"b}"
                for i in range(self.nbDataProcess * count):
                    registers.append(fmt.format(response.getRegister(i)))
                return 'ReadRegisters', tuple(registers)
            else:
                if response.read_code != 0x83:
                    return response.information
                else:
                    return 'Error'

    #TODO: get busTimeout address
    def getBusTimeout(self):
        response = self.rq.readHoldingRegisters(0, 0x219E, 24)
        result = self.testFunctionCode(response)
        return result

    def setBusTimeout(self, value):
        response = self.rq.writeMultipleRegisters(0, 8606, value)
        result = self.testFunctionCode(response)
        return result

    def getStatus(self, unit_id=0, key='all'):
        response = self.rq.readHoldingRegisters(unit_id, self.baseOffset, self.nbMovidrives \
                * self.nbDataProcess)
        result = self.testFunctionCode(response)

        offset = unit_id * self.nbDataProcess

        if not result or result[0] != "ReadRegisters":
            return False

        statusRegisters = result[1]
        statusRegister = statusRegisters[offset]
        positionRegister = statusRegisters[offset+1] + statusRegisters[offset+2]
        self.dpValuesOutput = result[1]
        #print(str(result[1]))
        powerStage, ready, \
                outputProcessFree, rampSet, \
                parameterSet, fault, \
                endStopRight, endStopLeft, \
                faultCode = \
                int(statusRegister[15]), int(statusRegister[14]), \
                int(statusRegister[13]), int(statusRegister[12]), \
                int(statusRegister[11]), int(statusRegister[11]), \
                int(statusRegister[10]), int(statusRegister[9]), \
                int(statusRegister[0:8])

        position = bitstring.Bits(bin='0b'+positionRegister)
        position = position.int

        faultText = self._faultCodes[faultCode]

        if key is "all":
            return powerStage, ready, outputProcessFree, rampSet, \
                    parameterSet, fault, endStopRight, endStopLeft, \
                    '{} : {}'.format(faultCode, faultText)

        res = list()

        if key is"positions":
            positions = list()
            for i in range(self.nbMovidrives):
                offset = i * self.nbDataProcess
                #print(bitstring.Bits(bin='0b' + self.dpValuesOutput[6]).str)
                positions.append(
                        bitstring.Bits(bin='0b' + \
                                self.dpValuesOutput[offset+1] + \
                                self.dpValuesOutput[offset+2]).int)
            return tuple(positions)
        for k in key:
            if k is "powerStage":
                res.append(powerStage)
            elif k is "ready":
                res.append(ready)
            elif k is "outputProcessFree":
                res.append(outputProcessFree)
            elif k is "rampSet":
                res.append(rampSet)
            elif k is "parameterSet":
                res.append(parameterSet)
            elif k is "fault":
                res.append(fault)
            elif k is "endStopRight":
                res.append(endStopRight)
            elif k is "endStopLeft":
                res.append(endStopLeft)
            elif k is "faultCode":
                res.append(faultCode)
            elif k is "position":
                res.append(position)

        return res

    def getPositions(self):
        positions = self.getStatus(0, "positions")
        if positions:
            scaledPositions = list()
            for v in positions:
                scaledPositions.append((v / self.nbOutputInc))
            return tuple(scaledPositions)
        return False

    def setStatus(self, unit_id=0x00, value=None, **kwargs):
        offset = unit_id * self.nbDataProcess

        for k, v in kwargs.items():
            if k is "lock":
                if v is True:
                    self.statusState[unit_id][0] = 1
                else:
                    self.statusState[unit_id][0] = 0
            elif k is"lockAll":
                if v is True:
                    v = 1
                else:
                    v = 0
                for i in range(self.nbMovidrives):
                    self.statusState[i][0] = v
            elif k is "enabled":
                if v is True:
                    self.statusState[unit_id][1] = 1
                    self.statusState[unit_id][2] = 1
                else:
                    self.statusState[unit_id][1] = 0
                    self.statusState[unit_id][2] = 0
            elif k is"enabledAll":
                if v is True:
                    v = 1
                else:
                    v = 0
                for i in range(self.nbMovidrives):
                    self.statusState[i][1] = v
                    self.statusState[i][2] = v
            elif k is "rapidStop":
                if v is True:
                    self.statusState[unit_id][1] = 0
                else:
                    self.statusState[unit_id][1] = 1
            elif k is "stop":
                if v is True:
                    self.statusState[unit_id][2] = 0
                else:
                    self.statusState[unit_id][2] = 1
            elif k is "holdControl":
                if v is True:
                    self.statusState[unit_id][3] = 1
                else:
                    self.statusState[unit_id][3] = 0
            elif k is "rampSet":
                if v is True:
                    self.statusState[unit_id][4] = 1
                else:
                    self.statusState[unit_id][4] = 0
            elif k is "parameterSet":
                if v is True:
                    self.statusState[unit_id][5] = 1
                else:
                    self.statusState[unit_id][5] = 0
            elif k is "reset":
                if v:
                    self.statusState[unit_id][6] = 1
                else:
                    self.statusState[unit_id][6] = 0
            elif k is"resetAll":
                if v is True:
                    v = 1
                else:
                    v = 0
                for i in range(self.nbMovidrives):
                    self.statusState[i][6] = v
            elif k is "direction":
                if v:
                    if v is "CW":
                        self.statusState[unit_id][8] = 0
                    elif v is "CCW":
                        self.statusState[unit_id][8] = 1
                else:
                    self.statusState[unit_id][8] = 0
        if value is None:
            for thisState, statusState in enumerate(self.statusState):
                value = 0
                for i, v in enumerate(statusState):
                    value += v * (2**i)

                self.dpValuesInput[thisState * self.nbDataProcess] = value

        else:
            self.dpValuesInput[unit_id] = value

        request = self.rq.writeMultipleRegisters(unit_id, self.baseOffset, self.dpValuesInput)

        result = self.testFunctionCode(request)
        return result

    def setSpeed(self, unit_id=0, speed=0):
        offset = unit_id * self.nbDataProcess

        if speed > self.maxSpeed:
            speed = self.maxSpeed
        elif speed < (self.maxSpeed * -1):
            speed = self.maxSpeed * -1

        direction = False
        if speed < 0:
            speed *= -1
            direction = True

        motorSpeed = speed * self.reductionRatio
        motorSpeedScaled = motorSpeed * 5
        motorSpeedScaled = int(motorSpeedScaled)

        speed = motorSpeedScaled

        if direction:
            speed = 65535 - speed

        self.dpValuesInput[1+offset] = speed

        request = self.rq.writeMultipleRegisters(unit_id, self.baseOffset, self.dpValuesInput)
        result = self.testFunctionCode(request)
        return result

    def setSpeeds(self, *args):
        if len(args) != self.nbMovidrives:
            return False

        for unit_id, speed in enumerate(args):
            offset = unit_id * self.nbDataProcess

            if speed > self.maxSpeed:
                speed = self.maxSpeed
            elif speed < (self.maxSpeed * -1):
                speed = self.maxSpeed * -1

            direction = False
            if speed < 0:
                speed *= -1
                direction = True

            motorSpeed = speed * self.reductionRatio
            motorSpeedScaled = motorSpeed * 5
            motorSpeedScaled = int(motorSpeedScaled)

            speed = motorSpeedScaled

            if direction:
                speed = 65535 - speed

            self.dpValuesInput[1+offset] = speed

        request = self.rq.writeMultipleRegisters(unit_id, self.baseOffset, self.dpValuesInput)
        result = self.testFunctionCode(request)
        return result

    def scanAddress(self, rng=1000, start=0, mode="r", value=None, unit_id=0x00):
        if mode is "r":
            for i in range(rng, start+rng):
                for l in range(128):
                    request = self.rq.readHoldingRegisters(unit_id, i, (l+1)*8)
                    result = self.testFunctionCode(request, l+1)
                    print i, result, (l+1)*8

        else:
            if not value:
                value = True*8
            for i in range(rng, start+rng):
                request = self.rq.writeMultipleRegisters(unit_id, i, (value,))
                result = self.testFunctionCode(request)
                print i, result

    def scanUnit(self, rng, address):
        for i in range(rng):
                for l in range(6):
                    request = self.rq.readHoldingRegisters(i, address, (l+1)*8)
                    result = self.testFunctionCode(request, l+1)
                    if result and result[1] != 131:
                        print i, result


class Movidrive(object):
    def __init__(self, dfe33b, unit_id):
        self.dfe33b = dfe33b
        self.unit_id = unit_id
        self.lockPosition = None
        self.position = None
        self.sens = "avance"
        self.positionAtteinte = True
        self.valeurMinVariationVitesse = 0.2
        self.valeurMaxVariationVitesse = 0.8
        self.valeurMinMargeVitesse = 0.1
        self.valeurMaxMargeVitesse = 0.9
        self.distanceToLockPosition = 0
        self.isAutoParked = False

    def setLockPosition(self,lockPosition):
        self.lockPosition = lockPosition

    def getLockPosition(self):
        return self.lockPosition

    def getStatus(self, key='all'):
        return self.dfe33b.getStatus(self.unit_id, key)

    def setStatus(self, value=None, **kwargs):
        return self.dfe33b.setStatus(self.unit_id, value, **kwargs)

    def getSpeed(self):
        return self.dfe33b.getSpeed(self.unit_id)

    def setSpeed(self, speed=0):
        return self.dfe33b.setSpeed(self.unit_id, speed)


class ModbusBackend(object):

    def __init__(self):
        self.log = logging.getLogger('stage')
        self.dfe = DFE33B()
        self.movidrive = list()
        for i in range(3):
            self.movidrive.append(Movidrive(self.dfe, i))

    def setConfig(self, c):
        for k, l in c:
            if k in ('updateFrequency',):
                if k is 'updateFrequency':
                    self.updateFrequency = int(l)

    @property
    def ready(self):
        for mv in self.movidrive:
            mv.setStatus(enabled=True)
            mv.setStatus(lock=True)
        return self.dfe.ready


if __name__ == "__main__":
    dfe = DFE33B()
    dfe.ready
    mv1 = Movidrive(dfe, 0)
    mv2 = Movidrive(dfe, 1)
    mv3 = Movidrive(dfe, 2)
    #dfe.deviceInformation()
    #print(dfe.getPositions("positions"))
    #print(mv2.getStatus())
    print(dfe.scanAddress(4,4,"r",dfe.nbMovidrives * dfe.nbDataProcess))
    #print(dfe.scanUnit(100,dfe.nbMovidrives * dfe.nbDataProcess))
    #print(mv3.getStatus())
