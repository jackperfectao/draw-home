#!/home/tops/bin/python
# -*- coding: utf-8 -*-
import json

COLOR_DEFAULT = '\033[0m'
COLOR_RED = '\033[0;31m'
COLOR_BLUE = '\033[1;34m'
COLOR_YELLOW = '\033[0;33m'
COLOR_GREEN = '\033[0;32m'
COLOR_PURPLE = '\033[0;35m'

DEBUG_FLAG = True


def printRed(str1, str2=None):
    inner_print(COLOR_RED, str1, str2)


def printDefault(str1, str2=None):
    inner_print(COLOR_DEFAULT, str1, str2)


def printBlue(str1, str2=None):
    inner_print(COLOR_BLUE, str1, str2)


def printYellow(str1, str2=None):
    inner_print(COLOR_YELLOW, str1, str2)


def printGreen(str1, str2=None):
    inner_print(COLOR_GREEN, str1, str2)


def printPurple(str1, str2=None):
    inner_print(COLOR_PURPLE, str1, str2)


def printDebug(str1, str2=None):
    if DEBUG_FLAG:
        printYellow(str1, str2)


def printObj(str):
    print json.dumps(str, ensure_ascii=False)


def inner_print(color_flag, str1, str2=None):
    line = color_flag + str1 + COLOR_DEFAULT
    if str2 is not None:
        line = line + ' ' + str2
    print line
