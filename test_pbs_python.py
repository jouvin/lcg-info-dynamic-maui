#!/usr/bin/python

from PBSQuery import PBSQuery, PBSError
server = 'grid63.lal.in2p3.fr'

try:
    p=PBSQuery(server)
    pbs=p.get_serverinfo()
    nodes=p.getnodes()
    jobs=p.getjobs()
    queues=p.getqueues()
except PBSError, e:
    print "<h3>Error connecting to PBS server:</h3><tt>",e,"</tt>"
    sys.exit(1)


print ""
print "Server info:"
print pbs

print ""
print "Nodes:"
for node in nodes.keys():
  print "********** %s *********" % node
  print nodes[node]

print ""
print "Jobs:"
for job in jobs.keys():
  print "********** Job %s *********" % job
  print jobs[job]

print ""
print "Queues:"
for queue in queues.keys():
  print "********** Queue %s *********" % queue
  print queues[queue]
