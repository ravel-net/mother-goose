from os import system
from collections import defaultdict
path = "/tmp/"

gnuplot_script = '''
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
set ytics nomirror'''

def filepath_gen(keytext):
	path_list = []
	path_list.append(path+ keytext+ ".txt")
	path_list.append(path+ keytext+ ".dat")
	path_list.append(path+ keytext+ ".plt")
	path_list.append(path+ keytext+ ".pdf")
	return path_list


def parse(logfile):
	form = defaultdict(list)
	
	f = open(logfile, "r")
	cdf = False
	
	for l in f.readlines():
		if l[0] == '#':
			if(l[1:10] == 'querytime'):
				cdf = True
			else:
				pass
		else:
			if(cdf):
				e = l.split('---')
				dbname = e[1]
				val = float(e[3][:-1])
				form[dbname].append(val)
					
			else:
				e = l.split('---')
				val = float(e[3][:-1])
				form[int(e[2])].append(val)
	
	result = []
	result.append(cdf)
	result.append(form)

	return result





def gen_dat(keyword):
	
        pl = filepath_gen(keyword)

	logfile = pl[0]
        datfile = pl[1]
        pltfile = pl[2]
        pdffile = pl[3]

        res = parse(logfile)
	cdf = res[0]
	form = res[1]

	open(datfile, 'w').close()
	f = open(datfile, "a")
	
	labellist = []
	print(cdf)
	if(cdf):
		for k,v in form.items():
			form[k] = sorted(v)
			labellist.append(k)
		
		size = len(v)
		for i in range(size):
			percent = str((float)(i+1)/size)
			string = percent
			for k in labellist:
				value = form[k][i]
				string = string + '\t' + str(value)
			f.write(string+'\n')
	else:
		for k in sorted(form):
			size = k
			value = form[k][0]
			print(value)
			f.write(str(size)+ '\t'+ str(value)+'\n')
			f.flush
	f.close()

	open(pltfile, 'w').close()
	pf = open(pltfile, "wr")
	pf.write(gnuplot_script)
        pf.write('''
# set ylabel "CDF"
# set xlabel "Per-update overhead (ms)"
# set title "'''+ keyword +'''"
set ylabel "'''+ keyword +'''"
set output "''' + pdffile + '''"
set terminal pdfcairo size 10,5 font "Gill Sans,9" linewidth 2 rounded fontscale 1 
# default 5 by 3 (inches)
set logscale x
plot ''')


	if(cdf):
		#string = ""
		#for i in range(len(labellist)):
		#	string = string + '''"'''+ datfile + '''" using 1:'''+ str(i+2)+''' title "'''+ labellist[i] + '''" with lp ls '''+ str(i+1)+''',\ \n\t'''
		#pf.write(string[:-5])
		pf.write('''"'''+ datfile + '''" using 2:1 title "'''+ labellist[0] +'''" with lp ls 1,\
 '' using 3:1 title "'''+ labellist[1]+'''" with lp ls 2
''')
 
	else:
		pf.write('''"'''+ datfile + '''" using 1:2 title "'''+ keyword + '''" with lp ls 1
''')

        pf.flush ()
        pf.close ()

	system('gnuplot '+ pltfile)

	



		
