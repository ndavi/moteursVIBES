#!/usr/bin/python2

import oscServer as osc
from liblo import make_method, Address, Message
import sys
import logging
import config
from collections import OrderedDict
import os.path as path
logging.basicConfig()


class MotherboardServerConfig(osc.OscServer):
    def __init__(self,workingdir, port=7969):
        workingDir = workingdir
        super(MotherboardServerConfig, self).__init__(port)
        self.log = logging.getLogger('motherboard.osc')
        self.feedback = False
        self.feedbackPort = 7376
        self.config = config.Conf(path.join(workingDir,'config.cfg'))

    def start(self):
        self.log.info('Le service de configuration des moteurs demarre.')
        super(MotherboardServerConfig, self).start()

    @make_method('/config/stage/setLockPosition', 'ffff')
    def configStageCallback(self, path, args, types, sender):
        if '/stage' in path:
            if '/setLockPosition' in path:
                motor, min, max,wtf = args
                self.log.info("Verouillage moteur")
                configToMod = self.config.loadLastConfig()
                configToMod["moteur" + str(int(motor))] = [min, max]
                self.config.config = configToMod
                self.config.save()


    @make_method(None, None)
    def defaultCallback(self, path, args, types, sender):
        self.log.warn('Unknown command: %s %s' % (path, ','.join([str(i) for i in args])))
