#!/usr/bin/python

from PBSQuery import PBSQuery, PBSError
server = 'grid10.lal.in2p3.fr'

try:
    p=PBSQuery(server)
    pbs=p.get_serverinfo()
    nodes=p.getnodes()
    jobs=p.getjobs()
    queues=p.getqueues()
except PBSError, e:
    print "<h3>Error connecting to PBS server:</h3><tt>",e,"</tt>"
    sys.exit(1)


nbRunningJobs = 0
for node in nodes:
  if 'jobs' in nodes[node]:
    nodeJobCount = len(nodes[node]['jobs'].split())
    print "Node %s: %d running jobs" % (node,nodeJobCount)
    nbRunningJobs += nodeJobCount

print ""
print "Torque server running job counter = %s" % pbs[server]['state_count']
print "Computed number of running jobs = %d" % nbRunningJobs
