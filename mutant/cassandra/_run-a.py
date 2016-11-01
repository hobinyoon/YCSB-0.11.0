#!/usr/bin/env python

import os
import sys
import time

sys.path.insert(0, "%s/work/mutant/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util


def main(argv):
	# No recreation of the keyspace. Use the pre-populated one.

	ycsb_params = ""
	if False:
		ycsb_params = " ".join(argv[i] for i in range(1, len(argv)))
		# -p recordcount=1000 -p operationcount=1 -p status.interval=1 -p fieldcount=10 -p fieldlength=100
	else:
		ycsb_params += " -threads 100"
		ycsb_params += " -target 1700"
		ycsb_params += " -p recordcount=20000000"
		ycsb_params += " -p operationcount=10000"
		ycsb_params += " -p status.interval=1"
		ycsb_params += " -p fieldcount=10"
		ycsb_params += " -p fieldlength=100"
	Cons.P(ycsb_params)

	Cons.P("Running the YCSB workload ...")
	cmd = "cd %s/../.." \
			" && bin/ycsb run cassandra-cql" \
			" -P workloads/workloada" \
			" -s" \
			" -p hosts=`cat ~/work/mutant/.run/cassandra-server-ips`" \
			" %s" \
			% (os.path.dirname(__file__), ycsb_params)
	Util.RunSubp(cmd, measure_time=True)


if __name__ == "__main__":
	sys.exit(main(sys.argv))
