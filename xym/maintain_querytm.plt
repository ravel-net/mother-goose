reset
set termoption dash

set style line 80 lt -1 lc rgb "#808080"
set style line 81 lt 0 # dashed
set style line 81 lt rgb "#808080"
set style line 1 lt 1 lc rgb "#a50f15" lw 2 pt 2
set style line 2 lt 1 lc rgb "#fb6a4a" lw 5 pt 0
set style line 3 lt 1 lc rgb "#92c5de" lw 5 pt 0
set grid back linestyle 81
set border 3 back linestyle 80

set output 'maintain_querytm.pdf'
set terminal pdfcairo size 5,2 font "Gill Sans, 9.5" linewidth 2 rounded fontscale 1

set ytics nomirror
set ytics nomirror

unset key

set multiplot

top=0.80
bot=0.32

# maintain plot
set tmargin at screen top
set bmargin at screen bot
set lmargin at screen 0.11
set rmargin at screen 0.46
set xtics font "Gill Sans, 8" rotate by -20
set ytics 5
set logscale x
set ylabel "time (sec)" offset 1.6,0
set label "policy size (# service chains)" font "Gill Sans, 9.5" at graph -0.15,-0.54
plot 'maintain.dat' using 1:($2/1000) title "maintain" with p ls 1 #with lp ls 1

unset label
unset ylabel
unset xtics

# querytm plot
set tmargin at screen top
set bmargin at screen bot
set lmargin at screen 0.61
set rmargin at screen 0.96
set logscale x
set xtics font "Gill Sans, 9.5"
set ytics 0.2
set ylabel "CDF" offset 2,0
set label "time (ms)" font "Gill Sans, 9.5" at graph 0.35,-0.54
plot 'querytm.dat' using 2:1 title "pgatable" with lp ls 2, \
     '' using 3:1 title "pgaview" with lp ls 3


# maintain key
set tmargin at screen 0.935
set bmargin at screen 0.85
set lmargin at screen 0
set rmargin at screen 0.50

set nologscale x
unset xtics
unset tics
unset xlabel
unset ylabel
unset label
set border 0

set key horiz
set key samplen 1 spacing 0.75 font "Gill Sans, 9.5" maxcols 3
set yrange[0:1]
set style data histogram
plot 2 t "maintain" lw 6 lc rgb "#a50f15"


# query tm key
set tmargin at screen 1
set bmargin at screen 0.87
set lmargin at screen 0.45
set rmargin at screen 1

set nologscale x
unset xtics
unset tics
unset xlabel
unset ylabel
unset label
set border 0

set key horiz
set key samplen 1 spacing 0.75 font "Gill Sans, 9.5" maxcols 3
set yrange[0:1]
set style data histogram
plot 2 t "view" lw 6 lc rgb "#92c5de", \
     2 t "materialized view" lw 6 lc rgb "#fb6a4a"

