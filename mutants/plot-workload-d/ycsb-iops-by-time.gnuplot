# Tested with gnuplot 4.6 patchlevel 6

FN_IN = system("echo $FN_IN")
FN_OUT = system("echo $FN_OUT")

set print "-"
#print sprintf(KEY)

set terminal pdfcairo enhanced size 2.3in, (2.3*0.85)in
set output FN_OUT

set border front lc rgb "#808080"
set grid xtics mxtics ytics mytics front lc rgb "#808080"
set xtics nomirror tc rgb "black"
set mxtics 2
set ytics nomirror tc rgb "black"
#(\
#  "10^1"     10 \
#, "10^2"    100 \
#, "10^3"   1000 \
#, "10^4"  10000 \
#, "10^5" 100000 \
#)
set mytics
set tics front

# http://www.gnuplot.info/docs_4.2/gnuplot.html#x1-18600043.21.2
set format y '10^{%T}'

set xlabel "Time (hour)" offset 0,0.3
set ylabel "IOPS" offset -0.2,0

set xrange[0:]
set yrange[40:40000]

set logscale y

plot \
FN_IN u (-1):(1) w p pt 1 pointsize 0.6 lc rgb "blue" t "Read", \
FN_IN u (-1):(1) w p pt 2 pointsize 0.6 lc rgb "red"  t "Insert", \
FN_IN u ($1/3600):($2 == -1 ? 1/0 : $2) w p pt 1 pointsize 0.3 lc rgb "blue" not , \
FN_IN u ($1/3600):($4 == -1 ? 1/0 : $4) w p pt 2 pointsize 0.3 lc rgb "red"  not
