#!/usr/bin/python2
#
# Trilateration class
# Algo based on http://en.wikipedia.org/wiki/Talk:Trilateration

from __future__ import division
import math
import vectors as vect

class Trilateration(object):
    def __init__(self, M0, M1, M2):
        self.motors = (M0[0:3], M1[0:3], M2[0:3],)
        self.offset = None
        if min(len(M0), len(M1), len(M2)) > 3:
            self.offset = (M0[3], M1[3], M2[3],)
        self.maxError = 0.0

    def trilateration(self, cableLenghts, debug=False):
        m0, m1, m2 = self.motors
        r0, r1, r2 = cableLenghts
        if self.offset:
            r0 -= self.offset[0]
            r1 -= self.offset[1]
            r2 -= self.offset[2]

        eX = vect.diff(m1, m0)
        normEx = vect.norm(eX)
        if normEx <= self.maxError:
            print 'maxErrorEx', normEx
            return False
        eX = vect.div(eX, normEx)

        t1 = vect.diff(m2, m0)
        i = vect.dot(eX, t1)
        t2 = vect.mul(eX, i)

        eY = vect.diff(t1, t2);
        normEy = vect.norm(eY)
        if normEy > self.maxError:
            eY = vect.div(eY, normEy)
            j = vect.dot(eY, t1)
        else:
            j = 0

        if math.fabs(j) <= self.maxError:
            t2 = vect.sum(m0, vect.mul(eX, r0))
            if math.fabs(vect.norm(vect.diff(m1, r1)) - \
                r1) <= self.maxError and \
                math.fabs(vect.norm(vect.diff(m2, r2)) - \
                r2) <= self.maxError:

                return (t2, t2,)

            t2 = vect.sum(m0, vect.mul(eX, -r0))
            if math.fabs(vect.norm(vect.diff(m1, r1)) - \
                r1) <= self.maxError and \
                math.fabs(vect.norm(vect.diff(m2, r2)) - \
                r2) <= self.maxError:

                return (t2, t2,)

            print 'maxErrorJ', math.fabs(j)
            return False

        eZ = vect.cross3D(eX, eY)

        x = (math.pow(r0, 2) - math.pow(r1, 2)) / (2*normEx) + normEx/2
        y = (math.pow(r0, 2) - math.pow(r2, 2) + math.pow(i, 2)) / (2*j) + j/2 - x * i / j
        z = math.pow(r0, 2) - math.pow(x, 2) - math.pow(y, 2)
        if z < -self.maxError:
            print 'maxErrorZ', math.fabs(z)
            return False
        else:
            if z > 0:
                z = math.sqrt(z)
            else:
                z = 0

        t2 = vect.sum(m0, vect.mul(eX, x))
        t2 = vect.sum(t2, vect.mul(eY, y))

        s1 = vect.sum(t2, vect.mul(eZ, z))
        s2 = vect.sum(t2, vect.mul(eZ, -z))

        #print s1, s2
        if s1[2] > s2[2]:
            s = s2
        else:
            s = s1

        X, Y, Z = s
        D0 = vect.norm(vect.diff(s, m0))
        D1 = vect.norm(vect.diff(s, m1))
        D2 = vect.norm(vect.diff(s, m2))

        if debug:
            return math.fabs(X), math.fabs(Y), math.fabs(Z), D0, D1, D2
        return math.fabs(X), math.fabs(Y), math.fabs(Z)

if __name__ == "__main__":
    motors = ((0, 0, 7190, 450,), (6350, 11100, 6810, 450,), (14950, 0, 7190, 450,),)
    startCoords = (14950/2, 11100/2, 700,)
    t = Trilateration(*motors)
    def pythagore3D(x, y, z, *args):
        cables = list()
        for i, motor in enumerate(motors):
            Xm, Ym, Zm, Om = motor
            cables.append(math.sqrt(
                math.pow(Xm - x, 2) +
                math.pow(Ym - y, 2) +
                math.pow(Zm - z, 2)) +
                Om)

        return cables

    Xn, Yn, Zn = startCoords
    for i in range(10):
        print '--', i
        Xp, Yp, Zp = Xn, Yn, Zn
        print 'O:', Xp, Yp, Zp
        Xn, Yn, Zn, D0, D1, D2 = t.trilateration((Xp, Yp, Zp,))
        print 'T:', Xn, Yn, Zn
        Xn, Yn, Zn = pythagore3D(Xn, Yn, Zn)
        print 'P:', Xn, Yn, Zn
        print 'Delta:', Xp-Xn, Yp-Yn, Zp-Zn

    cl = pythagore3D(*startCoords)
    print cl
    print t.trilateration(cl)
