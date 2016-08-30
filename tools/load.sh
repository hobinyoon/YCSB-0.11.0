#!/bin/bash

set -e
set -u

bin/ycsb load cassandra-cql \
-P workloads/workloada \
-s \
-threads 10 \
-p hosts=`cat ~/work/mutants/.run/cassandra-server-ips`
