#!/bin/bash

set -e
set -u

DN_THIS=`dirname $BASH_SOURCE`

pushd $DN_THIS/.. >/dev/null

mvn -pl com.yahoo.ycsb:cassandra-binding -am clean package -DskipTests

popd >/dev/null
