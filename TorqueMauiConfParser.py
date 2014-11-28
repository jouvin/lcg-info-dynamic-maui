"""
python utilities for querying Torque/MAUI configuration and statistics

Rely on pbs_python module (https://subtrac.sara.nl/oss/pbs_python) to access Torque configuration.
"""

__version__ = "2.1.0-2"
__author__  = "Michel Jouvin <jouvin@lal.in2p3.fr>, Cedric Duprilot <duprilot@lal.in2p3.fr>"


import string
import os
import re
import sys
try:
  from PBSQuery import PBSQuery,PBSError
except:
  sys.stderr.write("Failed to load  pbs_python module. Check it is installed.")
  sys.exit(1)

class TorqueMauiConfParser:

  # RE patterns used during parsing of MAUI standing reservations.
  # 'diagnose -r' is used to get information about existing reservations (both reservations
  # for running jobs and standing reservations). Each reservation is described on several lines.
  # The line starting a reservation description has the reservation id at the very beginning of the line
  # (no space before) and ends with 3 numbers (number of Node, Task, Proc used in the reservation). Each other
  # line containing the reservation description is idented.
  __ResStartPattern = re.compile(r'^(?P<resid>[\w\.\-]+).*\d+\s+\d+\s+\d+')
  # __SRAttrsPatterns contains a list of patterns parsing each attribute line we are
  # interested in. Use a dictionnary indexed by __SRStates.
  __SRAttrsPatterns = {'flags' : re.compile(r'^\s+Flags:\s*STANDINGR(?:ES|SV)'),
                       'acl' : re.compile(r'^\s+ACL:.*CLASS==(?P<classes>[\w\-\+\.:=]+).*'),
                       'cl' : re.compile(r'^\s+CL:\s+(?:RES|RSV)=='),
                       'resources' : re.compile(r'^\s+Task Resources:\s*PROCS:\s*(?P<nbprocs>\d+)'),
                       'attributes' : re.compile(r'^\s+Attributes\s+\(Host(?:List|Exp)=\'(?P<hostlist>.+)\''),
                      }
  __SRClassPattern = re.compile(r'([\w\-\.]+)')
  __SRWarningPattern = re.compile(r'^WARNING:\s+reservation\s+\'(?P<resid>.*)\'.*(?P<total>\d+)\s+proc.*allocated.*(?P<free>\d+)\s+detected$')

  # __SRStates : list containing the pattern name to look for in the expected order.
  # Values must be keys in __SRAttrsPatterns
  __SRStates = ('flags',
                'acl',
                'cl',
                'resources',
                'attributes',
               )

  
  def __init__(self, server, verbosity=0, diagOutputFile=None):
    self.SRList = {}
    self.activeNodes = {}
    self.verbosity = verbosity
    self.server = server

    # Load Torque configuration
    
    try:
        torqueConfig=PBSQuery(server)
        self.server_info=torqueConfig.get_serverinfo()[server]
        self.nodes=torqueConfig.getnodes()
        self.queues=torqueConfig.getqueues()
    except PBSError, e:
        self.__debug(0,"Error connecting to PBS server: %s" % e)
        sys.exit(1)

    # Define number of active processors and if node is active based on node status
    # to ease further computations. Node active status is maintained in a separate
    # dictionary for faster access.
    # A node is considered active if node state is not 'offline' or 'down'. But if a node is
    # offline and still running jobs (draining node), set the number of processors
    # to the number of running jobs and mark it as active. A node down is no longer
    # reachable and is unconditionally set inactive (a node down may still have a
    # list a assigned jobs as Torque clear it only when the node restarts).
    # Because of the specific processing of offline nodes, the count of active node
    # reported here may differ from 'diagnose -n' but this is consistent with further
    # calculations as long as 'activeNP' is used instead of 'np'.
    for node in self.nodes.keys():
      params = self.nodes[node]
      nodeState = {}
      # A node can be both offline and down: 'state' is a comma-separated list (string)
      for state in params['state']:
        nodeState[state] = None
      if 'offline' in nodeState or 'down' in nodeState:
        self.__debug(2,'Node %s state: %s' % (node,nodeState.keys().__str__()))
        if 'jobs' in  self.nodes[node] and not 'down' in nodeState:
          activeProcs = len(self.nodes[node]['jobs'])
          self.__debug(1,'Node %s inactive but %d procs still active' % (node,activeProcs))
          self.nodes[node]['activeNP'] = activeProcs
          self.activeNodes[node] = None
        else:
          self.nodes[node]['activeNP'] = 0
      else:
        self.activeNodes[node] = None
        self.nodes[node]['activeNP'] = int(self.nodes[node]['np'][0])

    if verbosity:
      self.__debug(1,'Number of Torque nodes detected: %d (active=%d)' % (len(self.nodes),len(self.activeNodes)))
      self.__debug(3,'Torque nodes: %s' % (self.nodes.__str__()))
      self.__debug(1,'Number of Torque queues detected: %d' % (len(self.queues)))
      self.__debug(3,'Torque queues: %s' % (self.queues.__str__()))

    # Parse configuration of MAUI SRs as returned by 'diagnose -r'
    self.__createSRList(diagOutputFile)


  # Private method to parse 'daignose -r' command.
  # The parser try to be very strict with the format expected, this may need
  # to be reviewed if diagnose output formt is evolving.
  # Called by constructor.
  def __createSRList(self,diagOutputFile=None):
    if diagOutputFile:
      diagnoseOutput = open(diagOutputFile)
    else:
      diagnoseOutput = os.popen('diagnose -r --host='+self.server)

    # nextState contains the next pattern to look for.
    # Value is used as an index in __SRStates.
    # Value -1 means we are looking for the start of a reservation description. 
    nextState = -1
    
    # For debugging: the line number in diagnose output being processed.
    i = 0
        
    resid = None
    for line in diagnoseOutput:
      i += 1
      line.rstrip('\n')
      if nextState >= 0 and nextState < len(TorqueMauiConfParser.__SRStates):
        nextStateStr = TorqueMauiConfParser.__SRStates[nextState]
        self.__debug(2,'Looking for line matching state %d (%s)' % (nextState,nextStateStr))
        matcher = TorqueMauiConfParser.__SRAttrsPatterns[nextStateStr].match(line)
        if matcher:
          self.__debug(3,'Match found for state %s' % (nextStateStr))
          if nextStateStr == 'flags':
            self.SRList[resid] = {}
            self.SRList[resid]['usedSlots'] = 0
          elif nextStateStr == 'acl':
            # Create queue list as a dictionnary for faster access later, value is unused
            self.SRList[resid]['queues'] = {}
            self.__debug(3,'queues=>>>%s<<<' % (matcher.group('classes')))
            for queue in TorqueMauiConfParser.__SRClassPattern.findall(matcher.group('classes')):
              self.SRList[resid]['queues'][queue] = None
          elif nextStateStr == 'resources':
            self.SRList[resid]['nbprocs'] = int(matcher.group('nbprocs'))
          elif nextStateStr == 'attributes':
            # If host listed in a SR is inactive, remove it. Also ensure 'nbprocs' for the SR
            # is not greater than the number of procs for the active nodes in the SR.
            self.__debug(3,'Hostlist=>>>%s<<<' % (matcher.group('hostlist')))
            self.SRList[resid]['hostlist'] = []
            for node in matcher.group('hostlist').split(','):
              node = node.strip()
              if node in self.activeNodes:
                self.SRList[resid]['hostlist'].append(node)
              else:
                self.__debug(1,'Reservation %s: inactive node %s removed' % (resid,node))
            srActiveProcs = 0
            for node in self.SRList[resid]['hostlist']:
              srActiveProcs += self.nodes[node]['activeNP']
            if srActiveProcs < self.SRList[resid]['nbprocs']:
              self.__debug(1,'Reservation %s: number of procs reduced to total number of procs on active nodes (%d)' % \
                                                                                        (resid,srActiveProcs))
              self.SRList[resid]['nbprocs'] = srActiveProcs

          nextState += 1
          continue

      # There should be no blank line and no unexpected line in a reservation description block.
      # Every line until the final state (=len(__SRStates)) must be expected, ie. described by a
      # pattern in ResAttrsPatterns.
      # If we come here before the final state, it means the next line encountered is not the
      # expected one and the description is considered incomplete. In this case discard the reservation.
      if nextState > 0:
        if nextState < len(TorqueMauiConfParser.__SRStates):
          if resid in self.SRList:
            self.__debug(1,"Reservation %s incomplete and discared" % resid)
            del self.SRList[resid]
          nextState = -1
        
      # After the final state has been encountered (and before the start of a new reservation),
      # look for any WARNING line related to the current reservation : it may contain information about
      # the current usage of the reservation.
        else:
          matcher = TorqueMauiConfParser.__SRWarningPattern.match(line)
          if matcher:
            if matcher.group('resid') == resid:
              self.SRList[resid]['usedSlots'] = int(matcher.group('total')) - int(matcher.group('free'))
              self.__debug(1,'Reservation %s: %d slots used over a total of %s slots' % (resid,self.SRList[resid]['usedSlots'],matcher.group('total')))
            else:
              self.__debug(1,'WARNING line found (%d) but for a reservation (%s) different from current one (%s)' % \
                                                                                          (i,matcher.group('resid'),resid))
                
      # If line is not a "valid" line in a SR context, check if it it the start of a new
      # reservation description. Else ignore
      matcher = TorqueMauiConfParser.__ResStartPattern.match(line)
      if matcher:
        nextState = 0
        resid = matcher.group('resid')
        self.__debug(2,"Line %d: start of reservation '%s' description" % (i,resid))
      else:
          self.__debug(2,"Line %d ignored: >>>%s<<<" % (i,line))

    if self.verbosity:
      if len(self.SRList) > 0:
        self.__debug(3,"Information collected about %d SRs:" % (len(self.SRList)))
        for resid in self.SRList.keys():
          self.__debug(3,'SR %s: %s' % (resid,self.SRList[resid].__str__()))
      else:
        self.__debug(1,"No SR information collected")
  

  # Print debugging messages on stderr according to verbosity level
  def __debug(self,level,msg):
    if level <= self.verbosity:
      sys.stderr.write("%s\n" % msg)
      

  # Returns Torque version
  def getTorqueVersion(self):
    return self.server_info['pbs_version'][0]


  # Returns list of configured queues
  def getQueueList(self):
    return self.queues.keys()

  
  # Returns list of configured nodes
  def getNodeList(self):
    return self.nodes.keys()

  
  # Return parameters for a given queue.
  # Returns None if the queue specified doesn't exist.
  def getQueueParams(self,queue):
    if queue in self.queues:
      return self.queues[queue]
    else:
      self.__debug(1,"getQueueParams: queue %s doesn't exist" % (queue))
      None

  
  # Return parameters for a given node
  # Returns None if the node specified doesn't exist.
  def getNodeParams(self,node):
    if node in self.nodes:
      return self.nodes[node]
    else:
      self.__debug(1,"getNodeParams: node %s doesn't exist" % (node))
      None
  
  # Returns total number of used job slots
  # This is done by iterating over activeNodes and counting the number of entries in
  # 'jobs' attribute (there is one entry per proc allocated to a job).
  def getTotalUsedSlots(self):
    usedSlots = 0
    for node in self.activeNodes.keys():
      if 'jobs' in self.nodes[node]:
        usedSlots += len(self.nodes[node]['jobs'])
    return usedSlots
  
  
  # Returns a dictionary containing the subset of nodes considered active
  # (not offline and not down). Value is meaningless. A dictionary is used
  # for faster use.
  # A drained node is considered active if it is still running jobs.
  # The nodes to consider can be either passed as an argument (a string can be used
  # for one node) or all the nodes configured otherwise.
  def getActiveNodes(self,nodes=None):
    if nodes:
      if type(nodes) == type('string'):
        nodeList = [ nodes ]
      else:
        nodeList = nodes
      activeNodes = {}
      nodeList = self.nodes.keys()
      for node in nodeList:
        if node in self.activeNodes:
          activeNodes[node] = None
      return activeNodes
    else:
      return self.activeNodes


  # Return total number of processors configured in Torque for the list of
  # nodes passed (a string can be used for one node) or all configured nodes otherwise.
  # If only active nodes must be taken into account (activeOnly=true), take into
  # accounts active nodes and drained nodes still running jobs.
  # Active state is not taken into account by default.
  def getProcNum(self,nodes=None,activeOnly=False):
    totalProcNumber = 0
    if nodes:
      if type(nodes) == type('string'):
        nodeList = [ nodes ]
      else:
        nodeList = nodes
    else:
      nodeList = self.nodes.keys()
    for node in nodeList:
      # 'activeNP' is set to 0 for inactive nodes in the constructor
      totalProcNumber += int(self.nodes[node]['activeNP'])
    return totalProcNumber

  
  # Returns the number of SDJ job slots accessible for a given queue taking into account
  # host state.
  # The return value is a dictionary with 3 entries: 'total', 'used', 'free'.
  # If 'queue' is not defined, return the total number of SDJ slots used.
  def getQueueSDJSlots(self,queue=None):
    queueSDJTotalSlots = 0
    queueSDJUsedSlots = 0
    for resid in self.SRList.keys():
      SR = self.SRList[resid]
      if not queue or queue in SR['queues']:
        for host in SR['hostlist']:
          queueSDJTotalSlots += SR['nbprocs']
          queueSDJUsedSlots += SR['usedSlots']
    if queue:
      self.__debug(1,'Queue %s: SDJ slots total=%d, used=%d' % (queue,queueSDJTotalSlots,queueSDJUsedSlots))
    else:
      self.__debug(1,'Configured SDJ slots: total=%d, used=%d' % (queueSDJTotalSlots,queueSDJUsedSlots))
    return { 'total':queueSDJTotalSlots, 'used':queueSDJUsedSlots, 'free':queueSDJTotalSlots-queueSDJUsedSlots }


