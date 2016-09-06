DN_THIS=`dirname $BASH_SOURCE`

cqlsh -f $DN_THIS/recreate-cassandra-table.cql `cat ~/work/mutants/.run/cassandra-server-ips`
