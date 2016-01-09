#!/usr/bin/python2

import os
from collections import OrderedDict

import logging
logging.basicConfig()
log = logging.getLogger(__name__)


class Conf(object):
    def __init__(self, toClasses, basePath=None, p=None):
        self.log = logging.getLogger('conf')

        self.basePath = basePath
        self.path = p
        self.lastPath = 'last'
        self.toClasses = list(toClasses)
        self.toClasses.append(self)
        self.config = None

        self.autoSave = False

    def setConfig(self, c):
        for k, l in c:
            if k in ('autosave', 'config',):
                if k == 'autosave':
                    autoSave, = l
                    self.autoSave = bool(autoSave)
                elif k == 'config':
                    self.path, = l

    @property
    def hasLastConfig(self):
        if self._pathExist(self.lastPath):
            return True
        else:
            return False

    def loadLastConfig(self):
            if self.log:
                self.log.info('Loading last config.')
            return self.load(last=True)

    def mergeConfig(self, cToMerge):
        if self.config:
            self.config.update(cToMerge)
        else:
            self.config = cToMerge
        if self.autoSave:
            self.save()

    def load(self, p=None, last=False):
        if p:
            self.path = p
        self.config = self.parse(last)
        print self.config
        if self.config:
            for cl in self.toClasses:
                cl.setConfig(self.config.items())
            if self.log:
                self.log.debug('Config loaded.')
            return True
        else:
            self.log.debug('Config not loaded.')
            return False

    def save(self, p=None):
        if not p:
            p = self.path
        if self.config:
            c = self.format()

            if self.lastPath:
                self.log.info('Saving config to %s.' % self.lastPath)
                self._setLinesToFile(self.lastPath, c)

            if self.path:
                self.log.info('Saving config to %s.' % self.path)
                rtn = self._setLinesToFile(p, c)
            else:
                self.log.warning('No config file specified.')
                rtn = False
            return rtn
        else:
            return False

    def saveAs(self, p):
        return self.save(p)

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

    def parse(self, last=False):
        if last:
            path = self.lastPath
        elif self.path:
            path = self.path
        else:
            self.log.warning('No config file specified.')
            return False
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
                self.log.debug('Config line %s parsed' % pair)

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
        if self.basePath:
            path = os.path.join(self.basePath, path)

        if self._pathExist(path):
            lines = getLinesFromFile(path)
            if lines:
                self.log.debug('Lines readed from %s.' % path)
                return lines
            self.log.warn('Unable to read %s.' % path)
        return False

    def _setLinesToFile(self, path, l):
        if self.basePath:
            path = os.path.join(self.basePath, path)

        if setLinesToFile(path, l):
            self.log.debug('Lines writed to %s.' % path)
            return True
        else:
            self.log.warn('Unable to write in %s.' % path)
            return False

def getLinesFromFile(path):
    print path
    try:
        with open(path, 'r') as f:
            lines = f.readlines()
        return lines
    except:
        return False

def setLinesToFile(path, l):
    try:
        with open(path, 'w+') as f:
            f.write(str(l))
        return True
    except:
        return False

if __name__ == "__main__":
    c = Conf([None, ], '/home/willykaze/repos/loeil/code/motherboard/', 'venissieux.mconf')
    c.load()
