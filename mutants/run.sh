#!/bin/bash

set -e
set -u

DN_THIS=`dirname $BASH_SOURCE`

pushd $DN_THIS/.. >/dev/null

DATETIME=`date +"%y%m%d-%H%M%S"`

mkdir -p "mutants/.log"

YCSB_LOG="mutants/.log/ycsb-"$DATETIME

bin/ycsb run cassandra-cql \
-P workloads/workloadd \
-s \
-threads 1 \
-p hosts=`cat ~/work/mutants/.run/cassandra-server-ips` \
-p recordcount=1000 \
-p operationcount=1000 \
2>&1 \
| tee -a $YCSB_LOG | grep --color=always -E "^|Mutants"

printf "Created %s %d\n" $YCSB_LOG `wc -c < $YCSB_LOG`

popd >/dev/null
