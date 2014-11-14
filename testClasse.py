#!/usr/bin/env python2
"""
python utilities and wrappers for Torque.
"""

__version__ = "0.1"
__author__  = "Cedric Duprilot"

import sys, logging
import syslog
import getopt
import string,os,re,commands

try:
    opts, args = getopt.getopt(sys.argv[1:], "h:",["host="])
except getopt.GetoptError:
    # print help information and exit:
    emsg = "Error parsing command line: " + string.join(sys.argv)
    print emsg

hostname = None
for o, a in opts:
	if o in ("-h", "--host"):
		hostname = a
            
if hostname:
    schedhost = hostname
else:
	cmdhst = 'hostname -f'
	hostNameRes = os.popen(cmdhst)
	hostLines = hostNameRes.readlines()
	for host in hostLines :
		schedhost = host.strip('\n')
ldiffile = '/opt/lcg/var/gip/ldif/static-file-CE-pbs.ldif'
try:
    ldf = open('/opt/lcg/var/gip/ldif/static-file-CE-pbs.ldif','r')
except IOError:
    print "Error opening config file" + ldiffile

# gets the dns containing the keyword GlueVOViewLocalID or GlueCEUniqueID
# and put this dn in dn list
dn = []
ldflignes = ldf.readlines()
for ldfl in ldflignes:
	diagPattern = re.compile(r'dn:\s+GlueCEUniqueID=')
	if diagPattern.search(ldfl):
		dn.append(ldfl.strip('\n'))
ldf.close()

from diagParserTest import *
parser = diagParser(schedhost)
nbProc = parser.getNbProc()
#print nbProc
#Gives the name of each queue in a list
#diagQ = []
for line in dn:
	qParser = (string.split((string.split((string.split(line,':'))[2],','))[0],'-'))[2]
	nbProcQueue = parser.getNbProcPerQueue(qParser)
	print 'queue '+ qParser + ':' + str(nbProcQueue)
