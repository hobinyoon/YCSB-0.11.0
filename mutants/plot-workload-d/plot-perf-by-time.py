#!/usr/bin/env python

import datetime
import os
import re
import sys

sys.path.insert(0, "%s/work/mutants/ec2-tools/lib/util" % os.path.expanduser("~"))
import Cons
import Util

#import Stat

_dn_stat = "%s/.stat" % os.path.dirname(__file__)

_dn_ycsb_log = "%s/work/mutants/YCSB/mutants/log" % os.path.expanduser("~")


def main(argv):
	GenStat()
	# TODO
	#Plot()


def GenStat():
	Util.MkDirs(_dn_stat)

	log_id = "160912-234955-d"
	fn_log = "%s/%s" % (_dn_ycsb_log, log_id)
	sps = []

	with open(fn_log) as fo:
		# h0: header 0
		# h1: header 1
		# body : body
		loc = "h0"

		for line in fo.readlines():
			if loc == "h0":
				#Cons.P("%s" % line)
				if line.startswith("+ bin/ycsb run"):
					loc = "h1"
					continue
			elif loc == "h1":
				if line.startswith("DBWrapper: report latency for each error is false and specific error codes to track for latency are:"):
					loc = "body"
					continue
			elif loc == "body":
				sps.append(StatPerSec(line))
				
	fn_stat = "%s/%s" % (_dn_stat, log_id)
	with open(fn_stat, "w") as fo:
		StatPerSec.WriteHeader(fo)
		for s in sps:
			fo.write("%s\n" % s)
	Cons.P("Created %s %d" % (fn_stat, os.path.getsize(fn_stat)))


class StatPerSec:
	fmt = "%5d %5d %8.2f %5d %8.2f"

	def __init__(self, line):
		#Cons.P(line)
		# 2016-09-12 23:50:15:208 1 sec: 1950 operations; 1948.05 current ops/sec;
		# est completion in 14 hours 15 minutes [READ: Count=1842, Max=120063,
		# Min=6640, Avg=24343.08, 90=43007, 99=114687, 99.9=118527, 99.99=120063]
		# [INSERT: Count=112, Max=118655, Min=8216, Avg=25360.89, 90=43807,
		# 99=117951, 99.9=118655, 99.99=118655]
		mo = re.match(r"\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d:\d\d\d (?P<timestamp>\d+) sec: \d+ operations; (\d|\.)+ current ops/sec; .+" \
				"READ: Count=(?P<read_cnt>\d+).+ Avg=(?P<read_lat_avg>\S+) .+" \
				"INSERT: Count=(?P<ins_cnt>\d+).+ Avg=(?P<ins_lat_avg>\S+)"
				, line)
		if mo is None:
			raise RuntimeError("Unexpected [%s]" % line)

		self.timestamp = int(mo.group("timestamp"))
		self.read_cnt = int(mo.group("read_cnt"))
		if self.read_cnt == 0:
			self.read_lat_avg = 0
		else:
			self.read_lat_avg = float(mo.group("read_lat_avg")[:-1])
		self.ins_cnt = int(mo.group("ins_cnt"))
		if self.ins_cnt == 0:
			self.ins_lat_avg = 0
		else:
			self.ins_lat_avg = float(mo.group("ins_lat_avg")[:-1])
	
	@staticmethod
	def WriteHeader(fo):
		fo.write("%s\n" % Util.BuildHeader(StatPerSec.fmt,
			"timestamp"
			" read_cnt"
			" read_lat_avg"
			" ins_cnt"
			" ins_lat_avg"
			))

	def __str__(self):
		return StatPerSec.fmt % \
				(self.timestamp
						, self.read_cnt
						, self.read_lat_avg
						, self.ins_cnt
						, self.ins_lat_avg
						)


# TODO: clean up
class WriteStat():
	def __init__(self, logs):
		self.logs = logs
		for l in logs:
			self.GenStat(l.itervalues().next())
		self.PlotCDF()
		self.PlotByTime()

	def GenStat(self, fn):
		with Cons.MT(fn, print_time=False):
			thrp = []
			fn0 = "%s/result/%s" % (os.path.dirname(__file__), fn)
			with open(fn0) as fo:
				for line in fo.readlines():
					if line.startswith("1+0 records in"):
						continue
					if line.startswith("1+0 records out"):
						continue
					if line.startswith("real"):
						continue
					if line.startswith("user"):
						continue
					if line.startswith("sys"):
						continue

					# 134217728 bytes (134 MB) copied, 0.851289 s, 158 MB/s
					#m = re.match(r"\d+ bytes \(\d+ MB\) copied, (?P<lap_time>(\d|\.)+) s, .+", line)
					m = re.match(r"134217728 bytes \(134 MB\) copied, (?P<lap_time>(\d|\.)+) s, .+", line)
					if m:
						#Cons.P(m.group("lap_time"))
						thrp.append(128.0 / float(m.group("lap_time")))
						continue
					raise RuntimeError("Unexpected %s" % line)
			#Cons.P(len(thrp))
			Stat.GenStat(thrp, "%s/%s-cdf" % (_dn_stat, fn))

			# Throughput in the time order
			fn_time_order = "%s/%s-time-order" % (_dn_stat, fn)
			with open(fn_time_order, "w") as fo:
				for t in thrp:
					fo.write("%s\n" % t)
			Cons.P("Created %s %d" % (fn_time_order, os.path.getsize(fn_time_order)))

	def PlotCDF(self):
		with Cons.MT("Plotting 128mb write throughput CDF by storage ..."):
			fn_in = " ".join("%s/%s-cdf" % (_dn_stat, l.itervalues().next()) for l in self.logs)
			fn_out = "%s/128mb-write-thrp-cdf-by-storage.pdf" % _dn_stat

			env = os.environ.copy()
			env["FN_IN"] = fn_in
			env["FN_OUT"] = fn_out
			Util.RunSubp("gnuplot %s/seq-write-cdf-by-storages.gnuplot" % os.path.dirname(__file__), env=env)
			Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))

	def PlotByTime(self):
		with Cons.MT("Plotting 128mb write throughput by time by storage ..."):
			fn_in = " ".join("%s/%s-time-order" % (_dn_stat, l.itervalues().next()) for l in self.logs)
			fn_out = "%s/128mb-write-thrp-by-time-by-storage.pdf" % _dn_stat

			env = os.environ.copy()
			env["FN_IN"] = fn_in
			env["FN_OUT"] = fn_out
			Util.RunSubp("gnuplot %s/seq-write-by-time-by-storages.gnuplot" % os.path.dirname(__file__), env=env)
			Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


class ReadStat():
	def __init__(self, logs):
		with Cons.MT("Read stat:", print_time=False):
			self.logs = logs
			for l in logs:
				self.GenStat(l.itervalues().next())
			self.PlotCDF()
			# Hard to interprete with 4 different types
			#self.PlotByTimeByStorage()
			self.PlotByTime()

	def GenStat(self, fn):
		with Cons.MT(fn, print_time=False):
			lap_times = []
			fn0 = "%s/result/%s" % (os.path.dirname(__file__), fn)
			with open(fn0) as fo:
				for line in fo.readlines():
					line = line.rstrip()
					if len(line) == 0:
						continue

					# 4 KiB from /mnt/local-ssd0/ioping-test-data (ext4 /dev/xvdb): request=1 time=219.1 us
					# 4 KiB from /mnt/local-ssd0/ioping-test-data (ext4 /dev/xvdb): request=394 time=1.51 ms
					m = re.match(r"4 KiB from /mnt/.+/ioping-test-data \(ext4 /dev/xvd.\): request=\d+ time=(?P<lap_time>(\d|\.)+ (us|ms))", line)
					if m:
						lt = m.group("lap_time")
						if lt.endswith(" us"):
							lt = float(lt[:-3])
						elif lt.endswith(" ms"):
							lt = (float(lt[:-3]) * 1000)
						lap_times.append(lt)
						continue

					# --- /mnt/local-ssd0/ioping-test-data (ext4 /dev/xvdb) ioping statistics ---
					if re.match(r"--- /mnt/.+/ioping-test-data \(ext4 /dev/xvd.\) ioping statistics ---", line):
						continue

					# 1 k requests completed in 175.1 ms, 3.91 MiB read, 5.71 k iops, 22.3 MiB/s
					# 1 k requests completed in 6.06 s, 3.91 MiB read, 164 iops, 659.8 KiB/s
					if re.match(r"\d+ k requests completed in .+ (min|s|ms|), .+ MiB read, .+ iops, .+ (K|M)iB/s", line):
						continue

					# min/avg/max/mdev = 146.9 us / 175.1 us / 1.77 ms / 79.6 us
					if re.match(r"min/avg/max/mdev = .+ (u|m)s / .+ (u|m)s / .+ (u|m)s / .+ (u|m)s", line):
						continue

					raise RuntimeError("Unexpected [%s]" % line)
			#Cons.P(len(lap_times))
			Stat.GenStat(lap_times, "%s/%s-cdf" % (_dn_stat, fn))

			# Throughput in the time order
			fn_time_order = "%s/%s-time-order" % (_dn_stat, fn)
			with open(fn_time_order, "w") as fo:
				for t in lap_times:
					fo.write("%s\n" % t)
			Cons.P("Created %s %d" % (fn_time_order, os.path.getsize(fn_time_order)))

	def PlotCDF(self):
		with Cons.MT("Plotting CDF by storage ..."):
			fn_in = " ".join("%s/%s-cdf" % (_dn_stat, l.itervalues().next()) for l in self.logs)
			fn_out = "%s/4kb-read-latency-cdf-by-storage.pdf" % _dn_stat

			env = os.environ.copy()
			env["FN_IN"] = fn_in
			env["FN_OUT"] = fn_out
			Util.RunSubp("gnuplot %s/rand-read-cdf-by-storages.gnuplot" % os.path.dirname(__file__), env=env)
			Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))

	def PlotByTimeByStorage(self):
		with Cons.MT("Plotting by time by storage ..."):
			fn_in = " ".join("%s/%s-time-order" % (_dn_stat, l.itervalues().next()) for l in self.logs)
			keys = " ".join(l.iterkeys().next().replace("_", "\\_") for l in self.logs)
			fn_out = "%s/4kb-read-latency-by-time-by-storages.pdf" % _dn_stat

			env = os.environ.copy()
			env["FN_IN"] = fn_in
			env["KEYS"] = keys
			env["FN_OUT"] = fn_out
			Util.RunSubp("gnuplot %s/rand-read-by-time-by-storages.gnuplot" % os.path.dirname(__file__), env=env)
			Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))

	def PlotByTime(self):
		with Cons.MT("Plotting by time by storage ..."):
			i = 0
			for l in self.logs:
				i += 1
				fn_in = "%s/%s-time-order" % (_dn_stat, l.itervalues().next())
				key = l.iterkeys().next()
				fn_out = "%s/4kb-read-latency-by-time-%s.pdf" % (_dn_stat, key.replace(" ", "-"))

				env = os.environ.copy()
				env["FN_IN"] = fn_in
				env["KEY"] = key
				env["FN_OUT"] = fn_out
				env["KEY_IDX"] = str(i)
				env["Y_LABEL_COLOR"] = "black" if key == "Local SSD" else "white"
				Util.RunSubp("gnuplot %s/rand-read-by-time-single-storage.gnuplot" % os.path.dirname(__file__), env=env)
				Cons.P("Created %s %d" % (fn_out, os.path.getsize(fn_out)))


if __name__ == "__main__":
	sys.exit(main(sys.argv))
