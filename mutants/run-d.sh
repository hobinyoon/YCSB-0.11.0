#!/bin/bash

set -e
set -u

DN_THIS=`dirname $BASH_SOURCE`

pushd $DN_THIS/.. >/dev/null

DATETIME=`date +"%y%m%d-%H%M%S"`

mkdir -p "mutants/.log"

YCSB_LOG="mutants/.log/"$DATETIME"-d"

time -p mutants/recreate-cassandra-table.sh
echo
sleep 1

time -p mutants/load.sh
echo
sleep 0.1

time -p bin/ycsb run cassandra-cql \
-P workloads/workloadd \
-s \
-p hosts=`cat ~/work/mutants/.run/cassandra-server-ips` \
-p recordcount=1000 \
-p operationcount=10000000 \
-p status.interval=1 \
-p fieldcount=10 \
-p fieldlength=2000 \
-threads 50 \
2>&1 \
| tee -a $YCSB_LOG | grep --color=always -E "^|Mutants"

printf "Created %s %d\n" $YCSB_LOG `wc -c < $YCSB_LOG`

popd >/dev/null
