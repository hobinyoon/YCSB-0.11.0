#!/bin/bash

set -e
set -u

DN_THIS=`dirname $BASH_SOURCE`

pushd $DN_THIS/.. >/dev/null

bin/ycsb run cassandra-cql \
-P workloads/workloada \
-s \
-threads 1 \
-p hosts=`cat ~/work/mutants/.run/cassandra-server-ips` \
-p recordcount=1000 \
-p operationcount=10000

popd >/dev/null
