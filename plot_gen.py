from os import system
from collections import defaultdict
path = "/tmp/"
debug = "/tmp/debug.txt"

gnuplot_script = '''
reset
set termoption dash
set style line 80 lt -1 lc rgb "#808080"
set style line 81 lt 0  # dashed
set style line 81 lt rgb "#808080"
set grid back linestyle 81
set border 3 back linestyle 80
set style line 1 lt 1 lc rgb "#DC143C" lw 3 pt 0
set style line 2 lt 1 lc rgb "#008B8B" lw 3 pt 0
set style line 3 lt 1 lc rgb "#1E90FF" lw 3 pt 0
set style line 4 lt 1 lc rgb "#8B008B" lw 3 pt 0
set style line 11 lt 1 lc rgb "#A00000" lw 3 pt 0 
set style line 12 lt 1 lc rgb "#00A000" lw 3 pt 0
set style line 13 lt 1 lc rgb "#5060D0" lw 3 pt 0
set style line 14 lt 1 lc rgb "#F25900" lw 3 pt 0
set key top left
set xtics nomirror
set ytics nomirror'''

def filepath_gen(keytext):
	path_list = []
	path_list.append(path+ keytext+ ".txt")
	path_list.append(path+ keytext+ ".dat")
	path_list.append(path+ keytext+ ".plt")
	path_list.append(path+ keytext+ ".pdf")
	return path_list

def parse(logfile):
	result = defaultdict(list)
	f = open(logfile, "r")
	for l in f.readlines():
		if l[0] == '#':
			pass
		else:
			e = l.split('----')
			result[e[1]].append(float(e[2][:-1]))
	return result

def gen_dat(logfile,title):
	pl = filepath_gen(title)
	
	datfile = pl[1]
	pltfile = pl[2]
	pdffile = pl[3]
	
	data = parse(logfile)
	size = 30
	label_list = []
	flag = 1
	

	df = open(debug, "a")
	
	for k,v in data.iteritems():
		data[k] = sorted(v)
		df.write(k + '\n')
		df.write(str(data[k]))	
	
	f = open(datfile, "wr")
	
	for i in range(size):
		percent = str((float)(i+1)/size)
		line = ""
		for k,v in data.iteritems():
			#v[i] = v[i][:-1]
			line += percent + '\t' + str(v[i]) + '\t'
			if(flag):
				label_list.append(k)
		line = line[:-1] + '\n'
		f.write(line)
		f.flush
		flag = 0
	df.close()
	f.close()
	#print(sorted(data['fattree4lblog_m']))
	#print(label_list)	
	pf = open(pltfile, "wr")
	pf.write(gnuplot_script)
	pf.write('''
# set ylabel "CDF"
# set xlabel "Per-update overhead (ms)"
# set title "'''+ title +'''"
set xlabel "'''+ title +'''"
set yrange [0:1]
set output "''' + pdffile + '''"
set terminal pdfcairo size 10,5 font "Gill Sans,9" linewidth 2 rounded fontscale 1 
# default 5 by 3 (inches)
set logscale x
plot "'''+ datfile + '''" using 2:1 title "'''+ label_list[0] +'''" with lp ls 13,\
 '' using 4:3 title "'''+ label_list[1]+'''" with lp ls 12,\
 '' using 6:5 title "'''+ label_list[2] + '''" with lp ls 11,\
 '' using 8:7 title "'''+ label_list[3] + '''" with lp ls 14,\
 '' using 10:9 title "'''+ label_list[4] + '''" with lp ls 1,\
 '' using 12:11 title "'''+ label_list[5] + '''" with lp ls 2
''')

    	pf.flush ()
    	pf.close ()






		
