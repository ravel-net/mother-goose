execfile("script.py")
execfile("sigcomm_plot.py")
execfile("maintenance.py")

from sigcomm_plot import gen_dat
from sigcomm_plot import parse
from os import system
path = "/tmp/"

#10 means the interval of each percentage is 10%: 10%, 20%, ...
#for more sampling,
#change it to small numbers such as 2: 2%, 4%, 6%...
SAMPLE_PERCENTAGE = 10


def run_querytm(toy, logfile):

        f = open(logfile, 'a')

        #f.write("#querytime\n")
        #f.flush

	for i in range(1, 30):

		t1 = time.time()
                toy.cur.execute("SELECT count(*) FROM pga where sid1 = 17;")
		t2 = time.time()
                t = (t2-t1)

	
		f.write ('---pgatable---'+ str(i) + '---' + str (t*1000) + '\n')
                f.flush ()

		t1 = time.time()
                toy.cur.execute("SELECT count(*) FROM pga_v where sid1 = 17;")
                t2 = time.time()
                t = (t2-t1)


                f.write ('---pgaview---'+ str(i) + '---' + str (t*1000) + '\n')
                f.flush ()

        

	f.close()


def run_maintenance(logfile, percent):
	

        f = open(logfile, 'a')

        f.write("#maintain\n")
        f.flush
	
	rd = int(100/percent)

	delta = get_delta("/home/mininet/ravel/emergingthreats/emerging-Block-IPs.txt", "/home/mininet/ravel/today.txt")


        for i in range(rd):
		a = Toyt('fattree16', 4)
		a.protocol()	
		init_withsample(a, i*percent)	
                
		t1 = time.time()
		#apply delta
		apply_delta(a, delta)
                t2 = time.time()
                t = (t2-t1)
		
		a.cur.execute("select count(*) from pga;")
		size = a.cur.fetchall()[0]["count"]

                f.write ('---maintenance---'+ str(size)+ '---' + str (t*1000) + '\n')
                f.flush ()
        

        f.close()






def init_withsample(a, percent):
	

        #init pga_group
        a.cur.execute("select * from hosts;")
        res = a.cur.fetchall ()

        hosts = []

        for each in res:
                hosts.append(each["hid"])
                a.cur.execute("insert into addrid values ('goodaddr', "+ str(each["hid"]) + ")")

        a.cur.execute("select * from groupid where gname = 'good'")
        goodid = a.cur.fetchall()[0]["gid"]

	for each in hosts:
        	a.cur.execute("insert into pga_group values ("+ str(goodid)+ ", "+ str(each)+ ")")

        data = parse_emerging("/home/mininet/ravel/emergingthreats/emerging-Block-IPs.txt")
        init_emerging(data, a, percent)
        #test(data, a)

        #init pga_policy
        a.cur.execute("select * from groupid where gname = 'good'")
        goodid = a.cur.fetchall()[0]["gid"]

        a.cur.execute("select * from groupid;")
        group = a.cur.fetchall ()
        for each in group:
                if(each["gid"] != goodid):
                        a.cur.execute("insert into pga_policy values ("+ str(each["gid"])+ ", "+ str(goodid)+ ", 'FW')")

def init_threats(a):
	
	#a= Toyt('toyt',4)
	#a.protocol()
	
	#init pga_group
	a.cur.execute("select * from hosts;")
	res = a.cur.fetchall ()

	hosts = []
	
	for each in res:
		hosts.append(each["hid"])
		a.cur.execute("insert into addrid values ('goodaddr', "+ str(each["hid"]) + ")")	
	
	a.cur.execute("select * from groupid where gname = 'good'")
	goodid = a.cur.fetchall()[0]["gid"]
	
	a.cur.execute("insert into pga_group values ("+ str(goodid)+ ", ARRAY"+ str(hosts)+ ")")
	
	data = parse_emerging("/home/mininet/ravel/emergingthreats/emerging-Block-IPs.txt")
	init_emerging(data, a)
	#test(data, a)

	#init pga_policy
	a.cur.execute("select * from groupid where gname = 'good'")
        goodid = a.cur.fetchall()[0]["gid"]
	
	a.cur.execute("select * from groupid;")
        group = a.cur.fetchall ()
	for each in group:
		if(each["gid"] != goodid):
			a.cur.execute("insert into pga_policy values ("+ str(each["gid"])+ ", "+ str(goodid)+ ", 'FW')")
	



# a uses pga as view
# b uses pga as table
def figure10(keyword):
	logfile = path + keyword+ ".txt"	
	open(logfile, 'w').close()

        f = open(logfile, 'a')

        f.write("#querytime\n")
        f.flush
	f.close()

	a = Toyt('fattree16', 4)
        a.protocol()
	init_withsample(a, 100)

	run_querytm(a, logfile)	

	gen_dat(keyword)


def figure_m(keyword):
		
	logfile = path+ keyword +".txt"
	
	open(logfile, 'w').close()
	
	run_maintenance(logfile, SAMPLE_PERCENTAGE)
	
	gen_dat(keyword)


	

def main():
	figure_m("maintain")	
	figure10("querytm");
	print("hello")	

if __name__ == "__main__": main()

