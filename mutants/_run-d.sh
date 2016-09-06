#!/bin/bash

set -e
set -u
set -x

DN_THIS=`dirname $BASH_SOURCE`

time -p $DN_THIS/recreate-cassandra-table.sh
echo
sleep 1

time -p $DN_THIS/load.sh
echo
sleep 0.1

# Throttle op/s
#   -target 100 \

# With p fieldcount=10 fieldlength=100 -threads 100, server CPU is the
# bottleneck. Network around 52 MB/s.

time -p bin/ycsb run cassandra-cql \
-P workloads/workloadd \
-s \
-p hosts=`cat ~/work/mutants/.run/cassandra-server-ips` \
-p recordcount=1000 \
-p operationcount=100000000 \
-p status.interval=1 \
-p fieldcount=10 \
-p fieldlength=100 \
-threads 100
