
reset
set termoption dash
set style line 80 lt -1 lc rgb "#808080"
set style line 81 lt 0  # dashed
set style line 81 lt rgb "#808080"
set grid back linestyle 81
set border 3 back linestyle 80
set style line 3 lt 1 lc rgb "#a50f15" lw 5 pt 0
set style line 2 lt 1 lc rgb "#fb6a4a" lw 5 pt 0
set style line 1 lt 1 lc rgb "#fcbba1" lw 5 pt 0
set style line 4 lt 1 lc rgb "#8B008B" lw 5 pt 0
set style line 13 lt 1 lc rgb "#08519c" lw 5 pt 0 
set style line 12 lt 1 lc rgb "#6baed6" lw 5 pt 0
set style line 11 lt 1 lc rgb "#c6dbef" lw 5 pt 0
set style line 14 lt 1 lc rgb "#F25900" lw 5 pt 0
set key top left
set xtics nomirror
set ytics nomirror
# set ylabel "CDF"
# set xlabel "Per-update overhead (ms)"
# set title "maintain"
set ylabel "maintain"
set output "/tmp/maintain.pdf"
set terminal pdfcairo size 10,5 font "Gill Sans,9" linewidth 2 rounded fontscale 1 
# default 5 by 3 (inches)
set logscale x
plot "/tmp/maintain.dat" using 1:2 title "maintain" with lp ls 1
