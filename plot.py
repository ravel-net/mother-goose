from __future__ import division
import os

gnuplot_script = '''
reset

set termoption dash

set style line 80 lt -1 lc rgb "#808080"
set style line 81 lt 0  # dashed
set style line 81 lt rgb "#808080"
set grid back linestyle 81
set border 3 back linestyle 80

set style line 1 lt rgb "#A00000" lw 1 pt 1 ps 1
set style line 2 lt rgb "#00A000" lw 1 pt 6 ps 1
set style line 3 lt rgb "#5060D0" lw 1 pt 2 ps 1
set style line 4 lt rgb "#F25900" lw 1 pt 9 ps 1

set style line 11 lt -1 lc rgb "#A00000" lw 3 
set style line 12 lt -1 lc rgb "#00A000" lw 3
set style line 13 lt -1 lc rgb "#5060D0" lw 3
set style line 14 lt 1 lc rgb "#F25900" lw 3

set key top left

set xtics nomirror
set ytics nomirror'''

def get_k (logfile):
    # if logfile[:3]
    t = logfile.split ('/')[-1] # .split ('.').split ('_')
    t2 = str (t.split ('_')[0][7:]) 
    return t2

def parse_log (logfile, keytext):

    s = []

    f = open(logfile, "r")
    for l in f.readlines():
        if l[0] == '#':
            pass
        else: 
            e = l.split ('----')
            if e[1] == keytext:
                if len (e[0]) != 0:
                    # s.append ([e[1], len (e[0]), float (e[2][:-1])/len (e[0])])
                    s.append (float (e[2][:-1])/len (e[0]))
                elif len (e[0]) == 0:
                    # s.append ([e[1], 0, float (e[2][:-1])])
                    s.append (float (e[2][:-1]))
    return s

def gen_dat (logfile, keytext, dir_name):

    xlabel = keytext
    nametext = xlabel.replace (' ', '_').replace (':', '').replace ('(','_').replace (')','_').replace ('+','_').replace ('*','_')

    datfile = dir_name + nametext + '.dat'

    o0 = sorted (parse_log (logfile[0], keytext))
    o1 = sorted (parse_log (logfile[1], keytext)) 
    o2 = sorted (parse_log (logfile[2], keytext))

    l0 = len (o0)
    l1 = len (o1)
    l2 = len (o2)
    l = max ([l0,l1,l2])

    def t_o (i, li, o):
        if i < li:
            return o[i]
        else:
            return o[li-1]

    f = open (datfile, "wr")
    for i in range (0,l):
        line = str ((i+1)/l0) + '\t' + str (t_o (i, l0, o0) ) + '\t' + str ((i+1)/l1)+'\t' + str (t_o (i, l1, o1)) + '\t' +str ((i+1)/l2)+'\t' + str (t_o (i, l2, o2)) + '\n'
        f.write (line)
        f.flush ()
    f.close ()

def gen_plt (logfile, keytext, dir_name):
    print "gen_plt ************************************************************************************"

    xlabel = keytext
    nametext = xlabel.replace (' ', '_').replace (':', '').replace ('(','_').replace (')','_').replace ('+','_').replace ('*','_')

    pltfile = dir_name + '/dat/' + nametext + '.plt'
    print pltfile
    pdffile = '/Users/anduo/share/ravel_plot/' + (dir_name.split ('/')[-1]) + '/' + nametext + '.pdf'

    pf = open(pltfile, "wr")
    pf.write (gnuplot_script)
    pf.write ('''
# set ylabel "CDF"
# set xlabel "Per-update overhead (ms)"
# set title "''' +keytext+ '''"
set xlabel "''' +xlabel+ '''"
set yrange [0:1]

set output "''' + pdffile + '''"
set terminal pdfcairo size 2,2 font "Gill Sans,9" linewidth 2 rounded fontscale 1 
# default 5 by 3 (inches)

set logscale x
plot "'''+ nametext +'''.dat" using 2:1 title "k='''+ get_k (logfile[0])+'''" with lp ls 13,\
 '' using 4:3 title "k='''+get_k (logfile[1])+ '''" with lp ls 12,\
 '' using 6:5 title "k='''+get_k (logfile[2])+ '''" with lp ls 11
''')

    pf.flush ()
    pf.close ()


class rPlot ():

    # subdir == isp_3sizes, isp2914_3ribs, fattree, profile    
    def __init__ (self, subdir, loglist, keylist):
        self.log_file_list = loglist
        self.key_list = keylist

        d = '/media/sf_share/ravel_plot/'
        self.log_dir = d + subdir + '/log/'
        self.dat_dir = d + subdir + '/dat/'
        self.pdf_dir = d + subdir

    def add_log (self,filename):
        self.log_file_list.append (self.log_dir + filename)

    def add_key (self,key):
        self.key_list.append (key)

    def parse_log (self):
        s = parse_log (self.log_file_list[0], self.key_list[0])
        return s

    def gen_dat (self):
        for key in self.key_list:
            gen_dat (self.log_file_list, key, self.dat_dir)

    def gen_plt (self):
        for key in self.key_list:
            gen_plt (self.log_file_list, key, self.pdf_dir)
            print self.pdf_dir

class rPlot_primitive (rPlot):

    def __init__ (self, subdir):

        lblist = ['lb: check max load', 'lb: re-balance (absolute)', 'lb+rt: re-balance (absolute)', 'lb+rt: re-balance (per rule)']
        acllist = ['acl: check violation', 'acl: fix violation', 'acl+rt: fix violation (absolute)', 'acl+rt: fix violation (per rule)']
        rtlist = ['rt: route ins']
        link = ['rt: linkdown', 'rt: linkup']
        acllbrt = ['acl+lb+rt: route ins']

        key_primitive = lblist + acllist + acllbrt + rtlist # + link

        rPlot.__init__ (self, subdir, [], key_primitive)

class rPlot_tenant (rPlot):

    def __init__ (self, subdir):

        tenantlist = ['rt*tenant: route ins', 'lb*tenant: check max load', '(lb+rt)*tenant: re-balance', 'lb*tenant: re-balance', 'acl*tenant: check violation', 'acl*tenant: fix violation', 'acl+rt*tenant: fix violation', '(acl+lb+rt)*tenant: route ins']

        key_tenant = tenantlist

        rPlot.__init__ (self, subdir, [], key_tenant)

# class rPlot_profile (rPlot):
#     keys = ['test']

#     def __int__ (self):
#         rPlot.__int__ (self, 'profile', [], keys)
        
#     def profile_dat ():
#         datfile = dir_name + nametext + '.dat'        

def profile_dat (logfile, rounds):

    logfilename = logfile.split ('/')[-1]    
    temp = len (logfilename)
    datfile_rti = logfile[:-temp - 4] + 'dat/'+ logfilename.split ('.')[0] + '_rti.dat'
    datfile_rtd = logfile[:-temp - 4] + 'dat/'+ logfilename.split ('.')[0] + '_rtd.dat'
    pdffile_rti = logfile[:-temp - 4] + logfilename.split ('.')[0] + '_rti.pdf'
    pdffile_rtd = logfile[:-temp - 4] + logfilename.split ('.')[0] + '_rtd.pdf'
    pltfile = logfile[:-temp - 4] + 'dat/' + logfilename.split ('.')[0] + '.plt'

    rti_dat = []
    rtd_dat = []
    
    f = open(logfile, "r")
    for l in f.readlines():
        if l[:2] != '#p':
            pass
        elif l[:3] == '#pi': 
            e = l.split ('----')
            rti_dat.append ({e[1]: e[2][:-1]})
        elif l[:3] == '#pd': 
            e = l.split ('----')
            rtd_dat.append ({e[1]: e[2][:-1]})

    fi = open (datfile_rti, "wr")
    for i in range (0,rounds):
        for j in range (0, int (len (rti_dat) / rounds)):
            num = int (i* len (rti_dat) / rounds + j)
            if rti_dat[num].keys ()[0] == 'insert_compute_port':
                tval = rti_dat[num].values ()[0].split (' ')[:-1]
                cf_l = len (tval)
                fi.write (str (rti_dat[num].keys ()[0]) + ' | ' + str (cf_l) + ' | ' +  str (sum([float(c) for c in tval])) + ' | ')
            else:
                fi.write (str (rti_dat[num].keys ()[0]) + ' | ' + str (rti_dat[num].values ()[0]) + ' | ')
        fi.write ('\n')
    fi.close ()

    fd = open (datfile_rtd, "wr")
    for i in range (0,rounds):
        for j in range (0, int (len (rtd_dat) / rounds) ):
            num = int (i* len (rtd_dat) / rounds + j)
            if rtd_dat[num].keys ()[0] == 'del_compute_port':
                tval = rtd_dat[num].values ()[0].split (' ')[:-1]
                cf_l = len (tval)
                fd.write (str (rtd_dat[num].keys ()[0]) + ' | ' + str (cf_l) + ' | ' +  str (sum([float(c) for c in tval])) + ' | ')
            else:
                fd.write (str (rtd_dat[num].keys ()[0]) + ' | ' + str (rtd_dat[num].values ()[0]) + ' | ')
        fd.write ('\n')
    fd.close ()

    f = open (pltfile, "wr")
    f.write (""" 
reset
set termoption dash
set style line 80 lt -1 lc rgb "#808080"
set style line 81 lt 0  # dashed
set style line 81 lt rgb "#808080"
set grid back linestyle 81
set border 3 back linestyle 80
set key top left
set xtics nomirror
set ytics nomirror
set style data histograms
set style histogram rowstacked
set boxwidth 1 relative
set style fill solid 1.0 border -1
set datafile separator "|"
""")

    f.write ("""
set output "/Users/anduo/share/"""+ pdffile_rti[16:] +""""
set terminal pdfcairo size 2,2 font "Gill Sans,9" linewidth 2 rounded fontscale 1
plot '/Users/anduo/share/"""+ datfile_rti[16:] +"""' using 2, '' using 5, '' using 7, '' using 9
""")

    f.write ("""
set output "/Users/anduo/share/"""+ pdffile_rtd[16:] +""""
set terminal pdfcairo size 2,2 font "Gill Sans,9" linewidth 2 rounded fontscale 1
plot "/Users/anduo/share/"""+ datfile_rtd[16:] +"""" using 3, '' using 5, '' using 7
""")
