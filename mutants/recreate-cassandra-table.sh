DN_THIS=`dirname $BASH_SOURCE`

echo "(Re)creating the cassandra YCSB table ..."
cqlsh -f $DN_THIS/recreate-cassandra-table.cql `cat ~/work/mutants/.run/cassandra-server-ips`
