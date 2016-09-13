#!/bin/bash

set -e
set -u

DN_THIS=`dirname $BASH_SOURCE`

pushd $DN_THIS/.. >/dev/null

DATETIME=`date +"%y%m%d-%H%M%S"`
DN_YCSB_LOG=$HOME"/work/mutants/log-volatile/ycsb"
mkdir -p $DN_YCSB_LOG
FN_YCSB_LOG=$DN_YCSB_LOG"/"$DATETIME"-d"

mutants/_run-d.sh 2>&1 | tee -a $FN_YCSB_LOG | grep --color=always -E "^|Mutants"

printf "Created %s %d\n" $FN_YCSB_LOG `wc -c < $FN_YCSB_LOG`

popd >/dev/null
