#!/usr/bin/python2

import os
from collections import OrderedDict

import logging

class Conf(object):
    def __init__(self, basePath=None):
        logging.basicConfig(format='%(asctime)s %(message)s')
        self.log = logging.getLogger('conf')
        self.config = None
        self.path = basePath


    def loadLastConfig(self):
        self.log("lalalaal")
        if self.log:
            self.log.info('Loading last config.')
        self.config = self.parse()
        return self.config

    def format(self):
        if self.config:
            lines = list()
            for k, l in self.config.items():
                l = [str(i) for i in l]
                lines.append('%s=%s' % (k, ','.join(l),))
            rtn = '\n'.join(lines)
            return rtn
        else:
            return False

    def save(self):
        if self.config:
            c = self.format()
            print(c)
            if self.path:
                self.log.info('Saving config to %s.' % self.path)
                rtn = self._setLinesToFile(c)
            else:
                self.log.warning('No config file specified.')
                rtn = False
            return rtn
        else:
            return False

    def load(self, p=None):
        if self.config:
            if self.log:
                self.log.debug('Config loaded.')
            return True
        else:
            self.log.debug('Config not loaded.')
            return False

    def parse(self):
        raw = self._getLinesFromFile(self.path)
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
            lines = self.getLinesFromFile(path)
            if lines:
                self.log.debug('Lines readed from %s.' % path)
                return lines
            self.log.warn('Unable to read %s.' % path)
        return False

    def _setLinesToFile(self, lines):

        if self.setLinesToFile(lines):
            self.log.debug('Lines writed to %s.' % path)
            return True
        else:
            self.log.warn('Unable to write in %s.' % path)
            return False

    def setLinesToFile(self,lines):
        try:
            with open(self.path, 'w+') as f:
                f.write(str(lines))
            return True
        except:
            return False

    def getLinesFromFile(self,path):
        try:
            with open(path, 'r') as f:
                lines = list()
                for line in f:
                    lines.append(line.rstrip('\n\r'))
            return lines
        except Exception as e:
            self.log.info("Error when reading files : " + e.message)
            return False


import os.path as path

if __name__ == "__main__":
    workingDir = path.dirname(path.realpath(__file__))
    conf = Conf(path.join(workingDir,'config.cfg'))
    #print (conf.loadLastConfig())
    dict = OrderedDict([('apple', [1,6]), ('banana', [1,6]), ('orange', [1,6]), ('pear', [1,6])])
    conf.config = dict
    conf.save()
    print("passe")