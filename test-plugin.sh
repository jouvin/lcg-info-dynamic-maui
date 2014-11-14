#!/bin/sh
# Script to run lcg-info-dynamic-maui with the appropriate arguments.
#
# hostname to use for the CE can be passed as first argument. Default to
# local machine host name

debug=''

usage () {
  echo "usage: $(basename $0) [-d] [--diagnose_output file] [--ce CE_host_name] [--local]"
  echo ""
  echo "    -d: debug messages, multiple -d to increase verbosity"
  echo "    --diagnose_output: file containing output of 'diagnose -r' to parse (for debugging)"
  echo "   --ce: host name of the Torque/MAUI server"
  echo "   --local: use local host name as Torque/MAUI server"
}

if [ -n "$1" ]
then
  while [ -n "$(echo $1 | grep '^-')" ]
  do
    case $1 in
      -d)
        debug="$debug --debug"
        ;;
      --diag*)
        diag_file="$1 $2"
        shift
        ;;
      --local)
        ce_host_name="--server $(hostname)"
        ;;
      --ce)
        ce_host_name="--server $2"
        shift
        ;;
      *)
        echo "Unsupported option ($1)"
        usage
        exit 1
    esac
    shift
  done
fi

./lcg-info-dynamic-maui ${debug} -l /opt/glite/etc/gip/ldif/static-file-CE-pbs.ldif -s /opt/glite/etc/gip/ldif/static-file-Cluster.ldif ${ce_host_name} ${diag_file}
