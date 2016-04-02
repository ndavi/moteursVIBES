#!/usr/bin/python2

import os
from collections import OrderedDict

import logging


class Conf(object):
    def __init__(self, basePath=None):
        self.log = logging.getLogger('conf')

        self.path = basePath


    def loadLastConfig(self):
            if self.log:
                self.log.info('Loading last config.')
            return self.parse(self.path)

    def load(self, p=None):
        if self.config:
            if self.log:
                self.log.debug('Config loaded.')
            return True
        else:
            self.log.debug('Config not loaded.')
            return False

    def parse(self, path):
        raw = self._getLinesFromFile(path)
        if not raw or raw == '':
            if self.log:
                self.log.warning('Config file empty.')
            return False
        parsed = OrderedDict()
        for l in raw:
            pair = l.split('\n')[0].split('=')
            pair = {pair[0]: pair[1].split(',')}
            parsed.update(pair)
            if self.log:
                self.log.info('Config line %s parsed' % pair)

        return parsed

    def _pathExist(self, path):
        if os.path.exists(path):
            if self.log:
                self.log.debug('%s exist.' % path)
            return True
        else:
            if self.log:
                self.log.warn('%s doesn\'t exist.' % path)
            return False

    def _getLinesFromFile(self, path):
        if self._pathExist(path):
            lines = getLinesFromFile(path)
            if lines:
                self.log.debug('Lines readed from %s.' % path)
                return lines
            self.log.warn('Unable to read %s.' % path)
        return False

def getLinesFromFile(path):
    try:
        with open(path, 'r') as f:
            lines = f.readlines()
        return lines
    except:
        return False

import os.path as path

if __name__ == "__main__":
    workingDir = path.dirname(path.realpath(__file__))
    conf = Conf(path.join(workingDir,'config.cfg'))
    print (conf.loadLastConfig())
