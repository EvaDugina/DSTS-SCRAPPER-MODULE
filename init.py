#!/usr/bin/env python

from HANDLERS import FILEHandler as fHandler, LOGHandler


def init():
    fHandler.createLOGSDir()
    LOGHandler.init()