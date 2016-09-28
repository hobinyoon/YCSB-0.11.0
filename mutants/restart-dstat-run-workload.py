#!/usr/bin/env python

import datetime
import os
import re
import subprocess
import sys

sys.path.insert(0, "%s/work/mutants/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

sys.path.insert(0, "%s/work/mutants/ec2-tools/lib" % os.path.expanduser("~"))
import BotoClient


_cur_datetime = datetime.datetime.now().strftime("%y%m%d-%H%M%S")

def main(argv):
	if len(argv) >= 3:
		workload_type = argv[1]
		ycsb_params = " ".join(argv[i] for i in range(2, len(argv)))
	else:
		workload_type = "d"
		ycsb_params = \
				" -threads 100" \
				" -p recordcount=1000" \
				" -p status.interval=1" \
				" -p fieldcount=10" \
				" -p fieldlength=100"

		# 20 M, 1KB, 50% write requests = 10 GB
		# 400 M, 1KB, 5% write requests = 20 GB
		# TODO: It will take a long time. May want to keep a snapshot of the data
		# and the commit log directories for later.
		ycsb_params += " -p operationcount=400000000"

		# Generate SSTables a bit faster. The default was 95% read.
		#ycsb_params += " -p readproportion=0.50 -p insertproportion=0.50"
		#
		# 30% writes to reduce the pending compactions. With a 50% write, network
		# BW was less than 15 MB/sec. Still pending compactions. Max network
		# bandwidth recv/send: 26 MB/13 MB
		#
		# With 20% write, up to 4 after 500 secs. Max network bandwidth 38 / 20 MB
		# But, the number goes down.
		#ycsb_params += " -p readproportion=0.80 -p insertproportion=0.20"
		#
		# 15% writes. Unthrottling is still not very realistic. The average server
		# load at Google is less than 30%. Max network 43 / 10. Up to 3.
		# I don't see any intra-L0 compactions.
		#ycsb_params += " -p readproportion=0.85 -p insertproportion=0.15"

		ycsb_params += " -p readproportion=0.95 -p insertproportion=0.05"

		# Throttle
		# With 10K, server CPU load less than 20%. It spikes to 40% when
		# compacting.
		# With 12K, about the same.
		# 20K. About 40%
		# 17K.
		#   About 31 - 32%. Good. 37% at 1000 secs. 50% at 2000 secs. 50 - 60% at
		#   8000 secs.
		#   Took 33974804 ms = 9 h 26 m
		#   Data and commit log directory sizes:
		#     13596    /home/ubuntu/work/mutants/cassandra/data/commitlog
		#     4        /home/ubuntu/work/mutants/cassandra/data/hints
		#     58596    /home/ubuntu/work/mutants/cassandra/data/saved_caches
		#     21240284 /mnt/local-ssd1/cassandra-data
		#   Number of SSTables in /mnt/local-ssd1/cassandra-data/ycsb/usertable-488da08084bf11e6ad9963c053f92bbd:
		#     146
		ycsb_params += " -target 17000"

		#" -p operationcount=50000000" \
		#" -threads 100"

		# Can you skip the loading phase? Probably by starting from 0 record?
		# Not progressing. A CPU seems to be stalled. Let's not do this. With 1
		# record loaded, it shows the READ-FAILED stat.
		#"-p recordcount=0" \

		# 16 GB. Makes sense. Raw data is about 10 GB.
		#" -p operationcount=10,000,000" \
		#" -p fieldcount=10" \
		#" -p fieldlength=100" \

	RestartDstat()

	# Start workload
	dn_ycsb_log = "%s/work/mutants/log/%s/%s/ycsb" \
			% (os.path.expanduser("~")
					, GetEc2Tags()["job_id"]
					, GetEc2Tags()["name"].replace("server", "s").replace("client", "c"))
	Util.MkDirs(dn_ycsb_log)

	fn_log = "%s/%s-%s" % (dn_ycsb_log, _cur_datetime, workload_type)

	cmd = "%s/_run-%s.py %s 2>&1 | tee -a %s | grep --color=always -E \"^|Mutants\"" \
			% (os.path.dirname(__file__), workload_type, ycsb_params, fn_log)
	Util.RunSubp(cmd)
	Cons.P("Created %s %d" % (fn_log, os.path.getsize(fn_log)))


_tags = None
def GetEc2Tags():
	global _tags
	if _tags is not None:
		return _tags

	r = BotoClient.Get(GetRegion()).describe_tags()
	#Cons.P(pprint.pformat(r, indent=2, width=100))
	_tags = {}
	for r0 in r["Tags"]:
		res_id = r0["ResourceId"]
		if InstId() != res_id:
			continue
		_tags[r0["Key"]] = r0["Value"]
	return _tags


_region = None
def GetRegion():
	global _region
	if _region is not None:
		return _region

	# http://stackoverflow.com/questions/4249488/find-region-from-within-ec2-instance
	doc       = Util.RunSubp("curl -s http://169.254.169.254/latest/dynamic/instance-identity/document", print_cmd = False, print_output = False)
	for line in doc.split("\n"):
		# "region" : "us-west-1"
		tokens = filter(None, re.split(":| |,|\"", line))
		#Cons.P(tokens)
		if len(tokens) == 2 and tokens[0] == "region":
			_region = tokens[1]
			return _region


_inst_id = None
def InstId():
	global _inst_id
	if _inst_id is not None:
		return _inst_id

	_inst_id  = Util.RunSubp("curl -s http://169.254.169.254/latest/meta-data/instance-id", print_cmd = False, print_output = False)
	return _inst_id


def RestartDstat():
	with Cons.MT("Restarting dstat ...", print_time=False):
		cmd = "ps -e -o pid,ppid,user,args"
		lines = Util.RunSubp(cmd, print_cmd=False, print_output=False)
		#Cons.P(lines)
		pids = []
		for line in lines.split("\n"):
			line = line.strip()
			if "dstat" not in line:
				continue
			if "csv" not in line:
				continue

			# Get the second-level processes, skipping the root-level ones.
			t = re.split(" +", line)
			if t[1] == "1":
				continue
			pids.append(t[0])
			#Cons.P("[%s]" % line)

		if len(pids) > 0:
			#Cons.P("[%s]" % " ".join(pids))
			Util.RunSubp("kill %s" % " ".join(pids))

			# Make sure each of the processes has terminated
			for pid in pids:
				cmd = "kill -0 %s" % pid
				while True:
					r = 0
					with open(os.devnull, "w") as devnull:
						r = subprocess.Popen(cmd, shell=True, stdin=devnull, stdout=devnull, stderr=devnull)
					if r != 0:
						Cons.P("Process %s has terminated" % pid)
						break
					time.sleep(0.1)

		# Run dstat as a daemon
		dn = "%s/work/mutants/log/%s/%s/dstat" \
				% (os.path.expanduser("~")
						, GetEc2Tags()["job_id"]
						, GetEc2Tags()["name"].replace("server", "s").replace("client", "c"))
		Util.MkDirs(dn)

		fn_out = "%s/%s.csv" % (dn, _cur_datetime)
		cmd = "dstat -tcdn -C total -D xvda,xvdb,xvdd,xvde,xvdf -r --output %s" % fn_out
		Util.RunDaemon(cmd)


if __name__ == "__main__":
	sys.exit(main(sys.argv))
