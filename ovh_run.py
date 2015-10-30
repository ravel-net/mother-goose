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
username = 'mininet'

path = '/tmp/'
db_list = ['fattree4','fattree8', 'fattree16']

'''
this function runs overhead on utm
'''
def ovh(db, dbname, logfile):

	f = open(logfile, 'a')

	f.write("#overhead_utm\n")
	f.flush

	for i in range(30):
        	f.write("#round "+ str(i) + "\n")
        	f.flush
	
		db.cur.execute("select min(host2) from utm;")
		mi = int (db.cur.fetchall()[0][0])	
		db.cur.execute("select max(host2) from utm;") 
		m= int (db.cur.fetchall()[0][0])
		
        	host1 = random.randrange(mi, m)
       	 	host2 = random.randrange(mi, m)

        	t1 = time.time()
        	db.cur.execute("insert into utm values (1808, "+ str(host1)+ ", "+ str(host2) + ");")
        	t2 = time.time()
        	ins_w = (t2-t1)

                t1 = time.time()
                db.cur.execute("delete from utm where fid = 1808;")
                t2 = time.time()
		del_w = (t2-t1)


		db.cur.execute("DROP TABLE IF EXISTS lb_m CASCADE;")
		db.cur.execute("DROP TRIGGER IF EXISTS utm_1 ON utm;")
		db.cur.execute("DROP TRIGGER IF EXISTS lb_tb_1 ON lb_tb;")
		
		
		t1 = time.time()
                db.cur.execute("insert into utm values (1808, "+ str(host1)+ ", "+ str(host2) + ");")
                t2 = time.time()
                ins_wo = (t2-t1)
	

		#f.write('#inserted'+ str(host1)+ ', ' + str(host2) + '\n')
		
        	f.write ('----'+dbname + 'ins----' + str ((ins_w-ins_wo)*1000) + '\n')
        	f.flush ()


        	t1 = time.time()
        	db.cur.execute("delete from utm where fid = 1808;")
        	t2 = time.time()

        	del_wo = (t2-t1)

        	f.write ('----'+dbname + 'del----' + str ((del_w-del_wo)*1000) +'\n')
        	f.flush ()
		db.cur.execute(open("/home/mininet/ravel/sql_scripts/tgs_lb.sql", "r").read())
		
	f.close()



def main():
	logfile = path+ "ovh.txt"
	pltfile = path + "ovh.plt"

	for dbname in db_list:
		b = Batch_fattree(dbname, 30)
		
		#try large number
		size = 1000
		b.rtm_ins (size)
        	b.init_acl ()
        	b.init_lb ()

        	b.op_primitive ()
		
		ovh(b, dbname, logfile)
	
	gen_dat(logfile, 'ovh')
	system('gnuplot '+ pltfile)
	

if __name__ == "__main__": main()




	
	



