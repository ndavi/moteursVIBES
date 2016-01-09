#!/usr/bin/python2
#
# Basic operations for 2D vectors

from __future__ import division
import math

def diff(Va, Vb):
    if len(Va) != len(Vb):
        raise ValueError

    V = list()
    for i, Ca in enumerate(Va):
        V.append(Ca - Vb[i])

    return tuple(V)

def sum(Va, Vb):
    if len(Va) != len(Vb):
        raise ValueError

    Vs = list()
    for i, Ca in enumerate(Va):
        Vs.append(Ca - Vb[i])

    return tuple(Vs)

def mul(Va, n):
    Vm = list()
    for Ca in Va:
        Vm.append(Ca * n)

    return tuple(Vm)

def div(Va, n):
    Vd = list()
    for Ca in Va:
        Vd.append(Ca / n)

    return tuple(Vd)

def norm(Va):
    normSq = 0
    for Ca in Va:
        normSq += math.pow(Ca, 2)

    return math.sqrt(normSq)

def dot(Va, Vb):
    dot = 0
    for i, Ca in enumerate(Va):
        dot += Ca * Vb[i]

    return dot

def cross2D(Va, Vb):
    V = list((0, 0,))
    V[0] = Va[0] * Vb[1] - Va[1] * Vb[0]
    V[1] = Va[1] * Vb[0] - Va[0] * Vb[1]
    return V

def cross3D(Va, Vb):
    V = list((0, 0, 0,))
    V[0] = Va[1] * Vb[2] - Va[2] * Vb[1]
    V[1] = Va[2] * Vb[0] - Va[0] * Vb[2]
    V[2] = Va[0] * Vb[1] - Va[1] * Vb[0]
    return V
