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
    def __init__(self, port=7969):
        workingDir = path.dirname(path.realpath(__file__))
        super(MotherboardServerConfig, self).__init__(port)
        self.log = logging.getLogger('motherboard.osc')
        self.feedback = False
        self.feedbackPort = 7376
        self.config = config.Conf(path.join(workingDir,'config.cfg'))

    def start(self):
        self.log.info('Le service de configuration des moteurs demarre.')
        super(MotherboardServerConfig, self).start()

    @make_method('/config/stage/lockMotor', 'iff')
    def configStageCallback(self, path, args, types, sender):
        if '/stage' in path:
            if '/lockMotor' in path:
                motor, min, max = args
                configToMod = self.config.loadLastConfig()
                configToMod["moteur" + str(motor)] = [min, max]
                self.config.config = configToMod
                self.config.save()


@make_method(None, None)
def defaultCallback(self, path, args, types, sender):
    self.log.warn('Unknown command: %s %s' % (path, ','.join([str(i) for i in args])))
