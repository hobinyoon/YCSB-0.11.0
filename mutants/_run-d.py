#!/usr/bin/env python

import os
import sys
import time

sys.path.insert(0, "%s/work/mutants/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util


def main(argv):
	Util.RunSubp("%s/recreate-cassandra-table.sh" % os.path.dirname(__file__))
	time.sleep(0.1)

	Util.RunSubp("%s/load.sh" % os.path.dirname(__file__))
	time.sleep(0.1)

	# Without limiting memory, p fieldcount=10 fieldlength=100 -threads 100, server CPU is the
	# bottleneck. Network around 52 MB/s.

	# With a 2GB memory,
	#   -p fieldlength=10000, network
	#     becomes the bottleneck. 125 MB/sec
	#   -p fieldlength=400
	#     In 6 mins, network IO drops below 40 MB/sec
	#   -p fieldlength=1000. record size is 10 KB
	#     the same. But, in 3 mins, the bottleneck becomes the disk IO.
	#   -p fieldlength=2000. record size is 20 kb
	#     the same. but, in 230 secs, the bottleneck becomes the disk io.
	#     todo: sstables are growing so fast. looks like the total will be around 20 gb. good!
	#   -p fieldlength=100. record size is 1 kb
	#     the same. but, in 230 secs, the bottleneck becomes the disk io.

	Cons.P("Running the YCSB workload ...")
	cmd = "cd %s/.." \
			" && bin/ycsb run cassandra-cql" \
			" -P workloads/workloadd" \
			" -s" \
			" -p hosts=`cat ~/work/mutants/.run/cassandra-server-ips`" \
			" %s" \
			% (os.path.dirname(__file__)
					, " ".join(argv[i] for i in range(1, len(argv))))
	Util.RunSubp(cmd, measure_time=True)


if __name__ == "__main__":
	sys.exit(main(sys.argv))
