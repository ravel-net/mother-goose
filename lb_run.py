execfile("batch_fattree.py")
from plot_gen import gen_dat
from plot_gen import parse
from os import system
import psycopg2
import psycopg2.extras
import psycopg2.extensions
import time
from batch import Batch
import batch_fattree
from math import log,exp

'''
global variables:
change db_list to experiment on different fattree size
change size_list to experiment on different policy size
'''
username = 'mininet'
db_list = ['fattree16','fattree32', 'fattree64']
file_list = ['acc', 'max', 'ovh1', 'ovh2']
size_list = [10, 100, 1000]
path = "/tmp/"
'''
This function runs "select * from lb"
and "select * from lb_m" 30 times,
and writes the timing into lblog.txt
'''
def acc_1(db, dbname, logfile):
	f = open(logfile, 'a')

	f.write("#" +dbname +"\n#access time\n")
	f.flush

	for i in range(30):
        	f.write("#round "+ str(i) + "\n")
        	f.flush

        	t1 = time.time()
        	db.cur.execute("select * from lb")
        	t2 = time.time()
        	db.cur.execute("select count(*) from lb")
        	num = int (db.cur.fetchall()[0][0])
        	t =(t2-t1)/num

        	f.write ('----'+dbname +'view----' + str(t*1000) + '\n')
        	f.flush ()

        	t1 = time.time()
       	 	db.cur.execute("select * from lb_m")
        	t2 = time.time()

        	db.cur.execute("select count(*) from lb_m")
        	num = int (db.cur.fetchall ()[0][0])
        	t = (t2-t1)/num

        	f.write ('----'+ dbname+ 'table----' + str(t*1000) +'\n')
        	f.flush ()
	f.close()


'''
this function runs select max(load) from lb and lb_m
for 30 times  and writes the time results into logfile
'''
def acc_2(db, dbname, logfile):
        f = open(logfile, 'a')

        f.write("#"+ dbname+"\n#access time\n")
        f.flush

        for i in range(30):
                f.write("#round "+ str(i) + "\n")
                f.flush

                t1 = time.time()
                db.cur.execute("select max(load) from lb")
                t2 = time.time()
                t = (t2-t1)

                f.write ('----'+dbname +'view----' + str (t*1000) + '\n')
                f.flush ()

                t1 = time.time()
                db.cur.execute("select max(load) from lb_m")
                t2 = time.time()

                t = t2- t1

                f.write ('----'+ dbname+ 'table----' + str (t*1000) +'\n')
                f.flush ()
        f.close()

'''
this function runs overhead on utm
'''
def ovh_1(db, dbname, logfile):

	f = open(logfile, 'a')

	f.write("#fattree16\n#overhead_utm\n")
	f.flush

	for i in range(30):
        	f.write("#round "+ str(i) + "\n")
        	f.flush

        	host1 = 1000*random.random()
       	 	host2 = 1000*random.random()

        	t1 = time.time()
        	db.cur.execute("insert into utm values (1808, "+ str(host1)+ ", "+ str(host2) + ");")
        	t2 = time.time()
        	t = (t2-t1)

        	f.write ('----'+dbname + 'ins----' + str (t*1000) + '\n')
        	f.flush ()

        	t1 = time.time()
        	db.cur.execute("delete from utm where fid = 1808;")
        	t2 = time.time()

        	t = (t2-t1)

        	f.write ('----'+dbname + 'del----' + str (t*1000) +'\n')
        	f.flush ()
	f.close()

'''
this funtion runs overhead on lbtb
'''
def ovh_2(db, dbname, logfile):
	f = open(logfile, 'a')

	f.write("#fattree16\n#overhead_lbtb\n")
	f.flush

	for i in range(30):
        	f.write("#round "+ str(i) + "\n")
        	f.flush

		db.cur.execute("select sid from lb_tb;")
		sid_list = db.cur.fetchall()
		size = len(sid_list)
		idx = int((size-1)*random.random())
       	 	sid = str(sid_list[idx])[1]

        	t1 = time.time()
		db.cur.execute("delete from lb_tb where sid = "+ str(sid)+ ";")
        	t2 = time.time()
        	t = (t2-t1)

        	f.write ('----'+dbname+ 'del----' + str (t*1000) + '\n')
        	f.flush ()

        	t1 = time.time()
		db.cur.execute("insert into lb_tb values ("+ str(sid)+ ");")
        	t2 = time.time()

        	t = (t2-t1)

        	f.write ('----'+ dbname + 'ins----' + str (t*1000) +'\n')
        	f.flush ()

	f.close()

'''
4 experiments:
1. acc: access lb and lb_m using query:"select * from" compare time against different policy size
2. max: query lb and lb_m using query: "select max(load)" -- against different policy size
3. ovh1 : measure the overhead of maintanence: insert and delete on table utm -- against different fattree size
4. ovh2 : measure the overhead of inserting and deleting on table lb_tb -- against different fattree size
'''
def main():
	logfile = {}
	pltfile = {}
	for tp in file_list:
		logfile[tp] = path + tp + ".txt"
		system('touch '+ logfile[tp])
		open(logfile[tp], 'w').close()
		pltfile[tp] = path + tp + ".plt"
	
	
	dbname = 'fattree16'
	for k in size_list:
		b = Batch_fattree(dbname, 30)
		b.rtm_ins(k)
		b.init_acl()
		b.init_lb()
		b.op_primitive()
		b.cur.execute(open("/home/mininet/ravel/sql_scripts/tgs_lb.sql", "r").read())
		acc_1(b, str(k), logfile['acc'])
		acc_2(b, str(k), logfile['max'])

	
	#for dbname in db_list:
	#	system('dropdb '+ dbname)
	'''
	logfile_ovh1 = "/tmp/ovh1.txt"
        system('touch '+logfile_ovh1)
        open(logfile_ovh1, 'w').close()
        pltfile_ovh1 = "/tmp/ovh1.plt"

        logfile_ovh2 = "/tmp/ovh2.txt"
        system('touch '+logfile_ovh2)
        open(logfile_ovh2, 'w').close()
        pltfile_ovh2 = "/tmp/ovh2.plt"
	'''
	
	for dbname in db_list:
		b = Batch_fattree(dbname, 30)
		
		#try large number
		size = 1000
		b.rtm_ins (size)
        	b.init_acl ()
        	b.init_lb ()

        	b.op_primitive ()
		b.cur.execute(open("/home/mininet/ravel/sql_scripts/tgs_lb.sql", "r").read())
		
		ovh_1(b, dbname, logfile['ovh1'])
		ovh_2(b, dbname, logfile['ovh2'])
	
	for i in range(4):
		tp = file_list[i]
		gen_dat(logfile[tp], tp)
		system('gnuplot '+ pltfile[tp])

'''
	gen_dat(logfile[acc], "acc")
	gen_dat(logfile[max], "max")
	gen_dat(logfile[ovh1], "ovh1")
	gen_dat(logfile[ovh2], "ovh2")	
	
	system('gnuplot '+ pltfile_acc)
	system('gnuplot ' + pltfile_max)	
	system('gnuplot '+ pltfile_ovh1)
	system('gnuplot '+ pltfile_ovh2)

'''	
		
		

if __name__ == "__main__": main()




	
	



