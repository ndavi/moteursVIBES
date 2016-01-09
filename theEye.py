#!/usr/bin/python2
# All measures in millimeters
import logging
from liblo import *


class TheEye(object):
    def __init__(self):
        self.log = logging.getLogger('theEye')
        self.config = False

        self.diameter = 350

        self.ledLevel = 0
        self.panValue = 0
        self.motorsEnabled = None
        self.motorsPidm = (0, 0, 0, 0)

        self.oscTarget = Address('192.168.0.10', 7970)

    @property
    def ready(self):
        return True

    def send(self, msg):
        send(self.oscTarget, msg)
        return True

    def auth(self):
        authMsg = Bundle(0, '/theEye/config/auth');
        self.send(authMsg);
        self.wifi()
        return self.oscTarget

    def wifi(self):
        wifiMsg = Bundle(0, '/theEye/config/wifi');
        return self.send(wifiMsg);

    def reset(self):
        resetMsg = Bundle(0, '/theEye/config/reset');
        return self.send(resetMsg);

    def led(self, level=0):
        if 0 <= level:
            if level > 255:
                level = 255
            self.ledLevel = level
            ledBundle = Bundle()
            ledMsg = Message('/theEye/led/level');
            ledMsg.add(self.ledLevel)
            ledBundle.add(ledMsg);
            self.send(ledBundle)
            return True
        return False

    def ledFlash(self, flash=0):
        ledFlashBundle = Bundle()
        ledFlashMsg = Message('/theEye/led/flash');
        ledFlashMsg.add(flash)
        ledFlashBundle.add(ledFlashMsg);
        self.send(ledFlashBundle)
        return True

    def pan(self, orientation=None):
        if orientation:
            self.panValue = orientation
            panBundle = Bundle()
            panMsg = Message('/theEye/pan/cap')
            panMsg.add(self.panValue)
            panBundle.add(panMsg)
            self.send(panBundle)
        return True

    def absCmd(self, cmd=None):
        if cmd:
            self.absoluteCmd = cmd
            absCmdBundle = Bundle()
            absCmdMsg = Message('/theEye/motors/absCmd')
            absCmdMsg.add(self.absoluteCmd)
            absCmdBundle.add(absCmdMsg)
            self.send(absCmdBundle)
        return True

    def absZero(self, offset=None):
        if offset is not None:
            self.absoluteZero = offset
            absZeroBundle = Bundle()
            absZeroMsg = Message('/theEye/motors/absZero')
            absZeroMsg.add(self.absoluteZero)
            absZeroBundle.add(absZeroMsg)
            self.send(absZeroBundle)
        return True

    def setZero(self):
        toTheEye = Bundle(0, '/theEye/pan/setZero')
        self.send(toTheEye)
        return True

    def motors(self, **kwargs):
        #for key, value in kwargs.items():
        #    if key in ('enable', 'pidm',):
        #        if key == 'enable':
        #            if value == False or value == True:
        #                self.motorsEnabled = value
        #                motorMsg = Message('/theEye/motors/enable')
        #                motorMsg.add(value)
        #                toTheEye = Bundle(0, motorMsg)
        #                self.send(toTheEye)
        #                return True
        #        elif key == 'pidm':
        #            if len(value) == 4:
        #                self.motorsPidm = value
        #               pidmMsg = Message('/theEye/motors/PIDM')
        #                for vl in value:
        #                    pidmMsg.add(vl)
        #                toTheEye = Bundle(0, pidmMsg)
        #                self.send(toTheEye)
        #                return True
        #return False
        self.mo

    def capCalibrate(self, path):
        if '/calibrate' in path:
            calibMsg = Message('/theEye/cap/calibrate')
            toTheEye = Bundle(0, calibMsg)
            self.send(toTheEye)
            return True
        else:
            calibMsg = Message('/theEye/cap/end')
            toTheEye = Bundle(0, calibMsg)
            self.send(toTheEye)
            return True

