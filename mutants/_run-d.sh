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

# Without limiting memory, p fieldcount=10 fieldlength=100 -threads 100, server CPU is the
# bottleneck. Network around 52 MB/s.

# With a 2GB memory,
#   -p fieldlength=10000, network
#     becomes the bottleneck. 125 MB/sec
#   -p fieldlength=400
#     In 6 mins, network IO drops below 40 MB/sec
#   -p fieldlength=1000. the record size is 10 KB
#     the same. But, in 3 mins, the bottleneck becomes the disk IO.
#   -p fieldlength=2000. the record size is 20 KB
#     the same. But, in 230 secs, the bottleneck becomes the disk IO.
#     TODO: SSTables are growing so fast. Looks like the total will be around 20 GB. Good!

echo "Running the YCSB workload ..."
time -p bin/ycsb run cassandra-cql \
-P workloads/workloadd \
-s \
-p hosts=`cat ~/work/mutants/.run/cassandra-server-ips` \
-p recordcount=1000 \
-p operationcount=50000000 \
-p status.interval=1 \
-p fieldcount=10 \
-p fieldlength=2000 \
-threads 100