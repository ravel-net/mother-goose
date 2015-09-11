CREATE OR REPLACE FUNCTION spv_constraint1_fun ()
RETURNS TRIGGER
AS $$
plpy.notice ("spv_constraint1_fun")

import os
import sys
import time
fo = open ('/home/mininet/ravel/log.txt', 'a')
def logfunc(msg,f=fo):
    f.write(msg+'\n')

if TD["new"]["status"] == 'on':
    tm = plpy.execute ("SELECT * FROM tm_delta;")

    for t in tm:
        if t["isadd"] == 1:
            f = t["fid"]	   
            s = t["src"]
            d = t["dst"]
	    
	    t1 = time.time ()
            pv = plpy.execute("""SELECT array(SELECT id1 FROM pgr_dijkstra('SELECT 1 as id, sid as source, nid as target, 1.0::float8 as cost FROM tp WHERE isactive = 1',""" +str (s) + "," + str (d)  + ",FALSE, FALSE))""")[0]['array']
	    t2 = time.time ()
	    logfunc ('#p----pgr_dijkstra_(ms)----' + str ((t2-t1)*1000))
	    fo.flush ()

            l = len (pv)
	    fo.write('#p----insert_compute_port----')
	    fo.flush ()

	    r1 = time.time ()
            for i in range (l):
                if i + 2 < l:
                    plpy.execute ("INSERT INTO cf (fid,pid,sid,nid) VALUES (" + str (f) + "," + str (pv[i]) + "," +str (pv[i+1]) +"," + str (pv[i+2])+  ");")
	    r2 = time.time ()
	    logfunc ('\n#p----insert_into_cf_(ms)----' + str ((r2-r1)*1000))
	    fo.flush ()
					
        elif t["isadd"] == 0:
	    r1 = time.time ()				
            f = t["fid"]
	    fo.write('#p----del_compute_port----')
	    fo.flush ()
            plpy.execute ("DELETE FROM cf WHERE fid =" +str (f) +";")
	    r2 = time.time ()
	    logfunc ('\n----delete_from_cf_(ms)----' + str ((r2-r1)*1000))
	    fo.flush ()

    plpy.execute ("DELETE FROM tm_delta;")

fo.close ()
return None;
$$ LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;


CREATE OR REPLACE FUNCTION tp2spv_fun () RETURNS TRIGGER
AS $$
isactive = TD["new"]["isactive"]
sid = TD["new"]["sid"]
nid = TD["new"]["nid"]

plpy.notice ("tp2spv_fun executed")

if isactive == 0:
   fid_delta = plpy.execute ("SELECT fid FROM cf where (sid =" + str (sid) + "and nid =" + str (nid) +") or (sid = "+str (nid)+" and nid = "+str (sid)+");")
   if len (fid_delta) != 0:
      for fid in fid_delta:
          plpy.execute ("INSERT INTO spv_tb_del (SELECT * FROM cf WHERE fid = "+str (fid["fid"])+");")

          s = plpy.execute ("SELECT * FROM tm WHERE fid =" +str (fid["fid"]))[0]["src"]
          d = plpy.execute ("SELECT * FROM tm WHERE fid =" +str (fid["fid"]))[0]["dst"]

          pv = plpy.execute("""SELECT array(SELECT id1 FROM pgr_dijkstra('SELECT 1 as id, sid as source, nid as target, 1.0::float8 as cost FROM tp WHERE isactive = 1',""" +str (s) + "," + str (d)  + ",FALSE, FALSE))""")[0]['array']
	     
          for i in range (len (pv)):	   		     
              if i + 2 < len (pv):
                  plpy.execute ("INSERT INTO spv_tb_ins (fid,pid,sid,nid) VALUES (" + str (fid["fid"]) + "," + str (pv[i]) + "," +str (pv[i+1]) +"," + str (pv[i+2])+  ");")
	      
return None;
$$ LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;

CREATE OR REPLACE FUNCTION add_flow_fun ()
RETURNS TRIGGER
AS $$
f = TD["new"]["pid"]
s = TD["new"]["sid"]
n = TD["new"]["nid"]

import os
import sys
import time
fo = open ('/home/mininet/ravel/log.txt', 'a')
def logfunc(msg,f=fo):
    f.write(msg)

t1 = time.time ()
u = plpy.execute("""select port from ports where sid = """ + str (s) + """ and nid = """ +str (n))
outport = str (u[0]['port'])
t2 = time.time ()
logfunc (str ((t2-t1)*1000) + ' ')
fo.flush ()

t1 = time.time ()
v = plpy.execute("""select port from ports where sid = """ + str (s) + """ and nid = """ +str (f))
inport = str (v[0]['port'])
t2 = time.time ()
logfunc (str ((t2-t1)*1000) + ' ')
fo.flush ()

return None;
$$ LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;




CREATE OR REPLACE FUNCTION del_flow_fun ()
RETURNS TRIGGER
AS $$
f = TD["old"]["pid"]
s = TD["old"]["sid"]
n = TD["old"]["nid"]

import os
import sys
import time
fo = open ('/home/mininet/ravel/log.txt', 'a')
def logfunc(msg,f=fo):
    f.write(msg)

t1 = time.time ()
u = plpy.execute("""\
         select port
         from ports where sid = """ +str (s)+"""   
         and nid = """ +str (n))
outport = str(u[0]['port'])
t2 = time.time ()
logfunc (str ((t2-t1)*1000) + ' ')

t1 = time.time ()
v = plpy.execute("""\
         select port
         from ports where sid = """ +str (s)+"""
         and nid = """ +str (f))
inport = str (v[0]['port'])
t2 = time.time ()
logfunc (str ((t2-t1)*1000) + ' ')
fo.flush ()

cmd1 = '/usr/bin/sudo /usr/bin/ovs-ofctl del-flows s' + str (s) + ' in_port=' + inport
cmd2 = '/usr/bin/sudo /usr/bin/ovs-ofctl del-flows s' + str (s) + ' in_port=' + outport

return None;
$$ LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;


