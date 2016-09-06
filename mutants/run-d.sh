#!/bin/bash

set -e
set -u

DN_THIS=`dirname $BASH_SOURCE`

pushd $DN_THIS/.. >/dev/null

DATETIME=`date +"%y%m%d-%H%M%S"`
YCSB_LOG="mutants/.log/"$DATETIME"-d"

mkdir -p "mutants/.log"

mutants/_run-d.sh 2>&1 | tee -a $YCSB_LOG | grep --color=always -E "^|Mutants"

printf "Created %s %d\n" $YCSB_LOG `wc -c < $YCSB_LOG`

popd >/dev/null
