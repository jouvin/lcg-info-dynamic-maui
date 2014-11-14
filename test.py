#!/usr/bin/env python2
"""
python utilities and wrappers for Torque.
"""
from __future__ import generators # only needed in Python 2.2
import string,os,re,commands
import sys

# convert triplet hours:minutes:seconds into seconds
def convertHhMmSs(time):
	diagPattern = re.compile(r'(\d+):(\d+):(\d+)')
	if diagPattern.search(time):
		hours = (diagPattern.search(time).groups())[0]
		minutes = (diagPattern.search(time).groups())[1]
		secondes = (diagPattern.search(time).groups())[2]
		timeModif = int(hours) * 3600 + int(minutes) * 60 + int(secondes)
		return timeModif
		
	if time != "-":
		timeModif = 0
		return timeModif
timeModif = convertHhMmSs("06:12:54")
print timeModif+"s"
