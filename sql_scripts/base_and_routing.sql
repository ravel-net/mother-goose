DROP TABLE IF EXISTS pox_tp CASCADE;
CREATE UNLOGGED TABLE pox_tp (
       in_switch  integer,
       in_port	  integer,
       out_switch integer,
       out_port   integer
);

DROP TABLE IF EXISTS pox_switches CASCADE;
CREATE UNLOGGED TABLE pox_switches (
       switch 	integer,
       port	integer
);

DROP TABLE IF EXISTS pox_hosts CASCADE;
CREATE UNLOGGED TABLE pox_hosts (
       host_id 	integer,
       switch	integer,
       port	integer
);

------------------------------------------------------------
------------------------------------------------------------
------------------------------------------------------------
------------------------------------------------------------

DROP TABLE IF EXISTS clock CASCADE;
CREATE UNLOGGED TABLE clock (
       counts  	integer,
       PRIMARY key (counts)
);
INSERT into clock (counts) values (0) ; -- initialize clock

DROP TABLE IF EXISTS p1 CASCADE;
CREATE UNLOGGED TABLE p1 (
       counts  	integer,
       -- priority	integer,
       status 	text,
       PRIMARY key (counts)
);

DROP TABLE IF EXISTS p2 CASCADE;
CREATE UNLOGGED TABLE p2 (
       counts  	integer,
       -- priority	integer,
       status 	text,
       PRIMARY key (counts)
);
-- INSERT into p2 (counts) values (0) ;

DROP TABLE IF EXISTS p3 CASCADE;
CREATE UNLOGGED TABLE p3 (
       counts  	integer,
       status 	text,
       PRIMARY key (counts)
);
-- INSERT into p3 (counts) values (0) ;

-- CREATE OR REPLACE RULE clock_ins AS 
--        ON INSERT TO clock
--        WHERE NEW.counts = 0
--        DO ALSO
--        (
--        	  INSERT INTO p1 VALUES (NEW.counts, 'clock');
--        	  INSERT INTO p2 VALUES (NEW.counts, 'clock');
--        	  INSERT INTO p3 VALUES (NEW.counts, 'clock'););

CREATE OR REPLACE RULE tick1 AS
       ON UPDATE TO p1
       WHERE (NEW.status = 'off')
       DO ALSO
           INSERT INTO p2 values (NEW.counts, 'on');

CREATE OR REPLACE RULE tick2 AS
       ON UPDATE TO p2
       WHERE (NEW.status = 'off')
       DO ALSO
           INSERT INTO p3 values (NEW.counts, 'on');

CREATE OR REPLACE RULE tick3 AS
       ON UPDATE TO p3
       WHERE (NEW.status = 'off')
       DO ALSO
           INSERT INTO clock values (NEW.counts);

------------------------------------------------------------
------------------------------------------------------------
------------------------------------------------------------
---------- base tables 

DROP TABLE IF EXISTS tp CASCADE;
CREATE UNLOGGED TABLE tp (
       sid	integer,
       nid	integer,
       ishost   integer,
       isactive integer,
       PRIMARY KEY (sid, nid)
);
CREATE INDEX ON tp(sid);

CREATE OR REPLACE FUNCTION protocol_fun() RETURNS TRIGGER AS
$$
plpy.notice ("engage ravel protocol")

ct = plpy.execute("""select max (counts) from p1""")[0]['max']
plpy.execute ("INSERT INTO p1 VALUES (" + str (ct+1) + ", 'on');")
return None;
$$
LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;

CREATE TRIGGER tp_up_trigger
     AFTER UPDATE ON tp
     FOR EACH ROW
   EXECUTE PROCEDURE protocol_fun();

-- DROP VIEW IF EXISTS tp CASCADE;
-- CREATE OR REPLACE VIEW tp AS (
--        SELECT DISTINCT
--               in_switch AS sid,
--        	      out_switch AS nid
--        FROM pox_tp
--        ORDER BY sid, nid
-- );

DROP TABLE IF EXISTS switches CASCADE;
CREATE UNLOGGED TABLE switches (
       sid	integer
);

-- DROP VIEW IF EXISTS switches CASCADE;
-- CREATE OR REPLACE VIEW switches AS (
--        SELECT DISTINCT
--               in_switch AS sid
--        FROM pox_tp
--        ORDER BY sid
-- );

DROP TABLE IF EXISTS hosts CASCADE;
CREATE UNLOGGED TABLE hosts (
       hid	integer
       -- h_uid	integer
);


CREATE OR REPLACE VIEW uhosts AS (
       SELECT hid, 
       	      row_number () OVER () as u_hid
       FROM hosts
);


DROP TABLE IF EXISTS cf CASCADE;
CREATE UNLOGGED TABLE cf (
       fid	integer,
       pid	integer,
       sid	integer,
       nid	integer,
       PRIMARY KEY (fid, sid)
);
CREATE INDEX ON cf(fid,sid);

DROP TABLE IF EXISTS tm CASCADE;
CREATE UNLOGGED TABLE tm (
       fid      integer,
       src	integer,
       dst	integer,
       vol	integer,
       PRIMARY KEY (fid)
);

-- uh1 = TD["new"]["src"]
-- uh2 = TD["new"]["dst"]
-- h1 = plpy.execute ("select hid from uhosts where u_hid =" + str (uh1))[0]['u_hid']
-- h2 = plpy.execute ("select hid from uhosts where u_hid =" + str (uh2))[0]['u_hid']
-- plpy.notice ("h1 is:" + str (h1))
-- plpy.notice ("h2 is:" + str (h2))
-- plpy.notice ("insert into tm values (" + str (TD["new"]["fid"]) + "),(" + str (h1) + '),(' + str (h2)+ '),('+ str (TD["new"]["vol"]) + ')')

-- plpy.execute ("insert into tm values (" + str (TD["new"]["fid"]) + "),(" + str (h1) + '),(' + str (h2)+ '),('+ str (TD["new"]["vol"]) + ')')

CREATE OR REPLACE FUNCTION tm_fun() RETURNS TRIGGER AS
$$
plpy.notice ("tm_fun")

ct = plpy.execute("""select max (counts) from p1""")[0]['max']
plpy.execute ("INSERT INTO p1 VALUES (" + str (ct+1) + ", 'on');")
return None;
$$
LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;

CREATE TRIGGER tm_in_trigger
     AFTER INSERT ON tm
     FOR EACH ROW
   EXECUTE PROCEDURE tm_fun();

CREATE TRIGGER tm_del_trigger
     AFTER DELETE ON tm
     FOR EACH ROW
   EXECUTE PROCEDURE tm_fun();

----------------------------------------------------------------------
----------------------------------------------------------------------
----------------------------------------------------------------------
---------- traffic matrix facing user

DROP TABLE IF EXISTS utm CASCADE;
CREATE UNLOGGED TABLE utm (
       fid      integer,
       host1	integer,
       host2	integer,
       PRIMARY KEY (fid)
);

CREATE OR REPLACE RULE utm_in_rule AS 
       ON INSERT TO utm
       DO ALSO
       INSERT INTO tm VALUES (NEW.fid,
       	      	      	     (SELECT hid FROM uhosts WHERE u_hid = NEW.host1),
			     (SELECT hid FROM uhosts WHERE u_hid = NEW.host2),
			     1);

CREATE OR REPLACE RULE utm_del_rule AS 
       ON DELETE TO utm
       DO ALSO DELETE FROM tm WHERE tm.fid = OLD.fid;

----------------------------------------------------------------------
-- routing application
----------------------------------------------------------------------

DROP VIEW IF EXISTS spv CASCADE;
CREATE OR REPLACE VIEW spv AS (
       SELECT fid,
       	      src,
	      dst,
	      (SELECT array(SELECT id1 FROM pgr_dijkstra('SELECT 1 as id,
	      	      	     	       	             sid as source,
						     nid as target,
						     1.0::float8 as cost
			                             FROM tp
						     WHERE isactive = 1', src, dst,FALSE, FALSE))) as pv
       FROM tm
);

-- DROP VIEW IF EXISTS spv2 CASCADE;
-- CREATE OR REPLACE VIEW spv2 AS (
--        SELECT fid,
--        	      src,
-- 	      dst,
-- 	      (SELECT array(SELECT id1 FROM pgr_dijkstra('SELECT 1 as id,
-- 	      	      	     	       	             sid as source,
-- 						     nid as target,
-- 						     1.0::float8 as cost
-- 			                             FROM cf c
-- 						     WHERE fid = c.fid', src, dst,FALSE, FALSE))) as pv
--        FROM tm
-- );

DROP VIEW IF EXISTS spv_edge CASCADE;
CREATE OR REPLACE VIEW spv_edge AS (
       WITH num_list AS (
       SELECT UNNEST (ARRAY[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]) AS num
       )
       SELECT DISTINCT fid, num, ARRAY[pv[num], pv[num+1], pv[num+2]] as edge
       FROM spv, num_list
       WHERE pv != '{}' AND num < array_length (pv, 1) - 1
       ORDER BY fid, num
);

DROP VIEW IF EXISTS spv_switch CASCADE;
CREATE OR REPLACE VIEW spv_switch AS (
       SELECT DISTINCT fid,
       	      edge[1] as pid,
	      edge[2] as sid,
       	      edge[3] as nid
       FROM spv_edge
       ORDER BY fid
);

-- DROP VIEW IF EXISTS spv_delta CASCADE;
-- CREATE OR REPLACE VIEW spv_delta AS (
--        (SELECT *, 'ins' as flag FROM 
--        (SELECT * FROM spv_switch
-- 	EXCEPT (SELECT * FROM cf)
-- 	ORDER BY fid) AS foo1)
-- 	UNION	
--        (SELECT *, 'del' as flag FROM 
--        (SELECT * FROM cf
-- 	EXCEPT (SELECT * FROM spv_switch)
-- 	ORDER BY fid) AS foo2)
-- );

DROP VIEW IF EXISTS spv_ins CASCADE;
CREATE OR REPLACE VIEW spv_ins AS (
       SELECT * FROM spv_switch
       EXCEPT (SELECT * FROM cf)
       ORDER BY fid
);

DROP VIEW IF EXISTS spv_del CASCADE;
CREATE OR REPLACE VIEW spv_del AS (
       SELECT * FROM cf
       EXCEPT (SELECT * FROM spv_switch)
       ORDER BY fid
);

CREATE OR REPLACE RULE spv_constaint AS
       ON INSERT TO p3
       WHERE NEW.status = 'on'
       DO ALSO
           (DELETE FROM cf WHERE (fid,pid,sid,nid) IN (SELECT * FROM spv_del);
	    INSERT INTO cf (fid,pid,sid,nid) (SELECT * FROM spv_ins);
            UPDATE p3 SET status = 'off' WHERE counts = NEW.counts;
	    );

------------------------------------------------------------
-- auxiliary function
------------------------------------------------------------

CREATE OR REPLACE FUNCTION get_port(s integer)
RETURNS TABLE (sid integer, nid integer, port bigint) AS 
$$

WITH TMP AS (
SELECT tp.sid, tp.nid, row_number () OVER () as port FROM tp
WHERE tp.sid = s OR tp.nid = s
)
(SELECT * 
FROM TMP
WHERE TMP.sid = s)
UNION
(SELECT TMP.nid as sid, TMP.sid as nid, TMP.port as port
FROM TMP
WHERE TMP.nid = s);
$$ LANGUAGE SQL;


------------------------------------------------------------
-- add_flow triggers
------------------------------------------------------------

CREATE OR REPLACE FUNCTION add_flow_fun ()
RETURNS TRIGGER
AS $$
f = TD["new"]["pid"]
s = TD["new"]["sid"]
n = TD["new"]["nid"]

u = plpy.execute("""select port from get_port (""" +str (s)+""") where nid = """ +str (n))
outport = str(u[0]['port'])
v = plpy.execute("""select port from get_port (""" +str (s)+""") where nid = """ +str (f))
inport = str (v[0]['port'])
tran_num = str (plpy.execute ("""select max(counts) from p1""")[0]['max']) 

cmd1 = '/usr/bin/sudo /usr/bin/ovs-ofctl add-flow s' + str (s) + ' in_port=' + inport + ',actions=output:' + outport
cmd2 = '/usr/bin/sudo /usr/bin/ovs-ofctl add-flow s' + str (s) + ' in_port=' + outport + ',actions=output:' + inport

import os
import sys
import time

fo = open ('/home/mininet/ravel/log.txt', 'a')
def logfunc(msg,f=fo):
    f.write(msg+'\n')

t1 = time.time ()
x1 = os.system (cmd1)
t2 = time.time ()
logfunc ('add-flow s' + str (s) + '(ms): ' + str ((t2-t1)*1000))

t1 = time.time ()
x2 = os.system (cmd2)
t2 = time.time ()
logfunc ('add-flow s' + str (s) + '(ms): ' + str ((t2-t1)*1000))

fo.flush ()

return None;
$$ LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;

CREATE TRIGGER add_flow_trigger
     AFTER INSERT ON cf
     FOR EACH ROW
   EXECUTE PROCEDURE add_flow_fun();

-- plpy.notice (cmd1 + ' via os.system returns ' + str (x1) )
-- plpy.notice (cmd2 + ' via os.system returns ' + str (x2) )

-- import subprocess
-- x1 = subprocess.call(mnstring,shell=True)
-- x2 = subprocess.call(mnstring2,shell=True)
-- plpy.notice ("start ------------------------------")
-- plpy.notice (mnstring)
-- plpy.notice (x1)
-- plpy.notice (mnstring2)
-- plpy.notice (x2)


-- p1 = subprocess.Popen(mnstring, shell=True, stdin=subprocess.PIPE)

-- p1 = subprocess.Popen(mnstring,
--                         shell=True, stdin=subprocess.PIPE,
--                         stdout=subprocess.PIPE,
--                         stderr=subprocess.PIPE)
-- x1 = p1.communicate()

-- p = subprocess.Popen(["echo", "hello world"], stdout=subprocess.PIPE)
-- ss = p.communicate()
-- plpy.notice (ss) 

-- import os
-- import sys
-- x1 = os.system(mnstring)
-- plpy.notice (mnstring + ' returns: ' + str (x1))

-- x2 = os.system(mnstring2)
-- plpy.notice (mnstring2 + ' returns: ' + str (x2))

------------------------------------------------------------
-- del_flow triggers
------------------------------------------------------------

CREATE OR REPLACE FUNCTION del_flow_fun ()
RETURNS TRIGGER
AS $$
f = TD["old"]["pid"]
s = TD["old"]["sid"]
n = TD["old"]["nid"]

u = plpy.execute("""\
         select port
         from get_port (""" +str (s)+""")  
         where nid = """ +str (n))
outport = str(u[0]['port'])

v = plpy.execute("""\
         select port
         from get_port (""" +str (s)+""")
         where nid = """ +str (f))
inport = str (v[0]['port'])

cmd1 = '/usr/bin/sudo /usr/bin/ovs-ofctl del-flows s' + str (s) + ' in_port=' + inport
cmd2 = '/usr/bin/sudo /usr/bin/ovs-ofctl del-flows s' + str (s) + ' in_port=' + outport

import os
import sys
import time

fo = open ('/home/mininet/ravel/log.txt', 'a')
def logfunc(msg,f=fo):
    f.write(msg+'\n')

t1 = time.time ()
x1 = os.system (cmd1)
t2 = time.time ()
logfunc ('del-flows s' + str (s) + '(ms): ' + str ((t2-t1)*1000))

t1 = time.time ()
x1 = os.system (cmd2)
t2 = time.time ()
logfunc ('del-flows s' + str (s) + '(ms): ' + str ((t2-t1)*1000))

fo.flush ()

return None;
$$ LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;

-- plpy.notice (cmd1 + ' via os.system returns ' + str (x1) )
-- plpy.notice (cmd2 + ' via os.system returns ' + str (x2) )
-- plpy.notice("remove sid = "+ str (s) + ", nid = " +str (n) + ", out_port =" + outport + ", in_port = "+ inport)

CREATE TRIGGER del_flow_trigger
     AFTER DELETE ON cf
     FOR EACH ROW
   EXECUTE PROCEDURE del_flow_fun();


------------------------------------------------------------
-- test triggers
------------------------------------------------------------

CREATE OR REPLACE FUNCTION cf_notify_trigger()
     RETURNS TRIGGER AS $$
   BEGIN
       RAISE NOTICE 'Hi, I got % invoked FOR % % % on %',
                                  TG_NAME,
                                  TG_LEVEL,
                                  TG_WHEN,
                                  TG_OP,
                                  TG_TABLE_NAME;
       RAISE NOTICE 'contents: fid %, sid %, nid %', NEW.fid, NEW.sid, NEW.nid;
       RETURN NEW;					
   END;
   $$ LANGUAGE plpgsql;

-- CREATE TRIGGER ins_cf_trigger
--      AFTER INSERT ON cf
--      FOR EACH ROW
--    EXECUTE PROCEDURE cf_notify_trigger();

CREATE OR REPLACE FUNCTION tp_notify_trigger()
     RETURNS TRIGGER AS $$
   BEGIN
       RAISE NOTICE 'Hi, I got % invoked FOR % % % on %',
                                  TG_NAME,
                                  TG_LEVEL,
                                  TG_WHEN,
                                  TG_OP,
                                  TG_TABLE_NAME;
       RAISE NOTICE 'contents: sid %, nid %', NEW.sid, NEW.nid;
       RETURN NEW;					
   END;
   $$ LANGUAGE plpgsql;

-- CREATE TRIGGER ins_tp_trigger
--      AFTER INSERT ON tp
--      FOR EACH ROW
--    EXECUTE PROCEDURE tp_notify_trigger();

CREATE OR REPLACE FUNCTION py_tp_notify_trigger ()
RETURNS TRIGGER
AS $$
import os
import sys
x = os.system("ls")
plpy.notice ('ls returns ' + str(x))

msg = 'sudo ovs-ofctl add-flow s6 in_port=2,actions=output:1'
y = os.system (msg)
plpy.notice (msg + ' via os.system returns ' + str (y) )

import subprocess
p = subprocess.Popen(msg, shell=True, stdin=subprocess.PIPE)
z = p.communicate()
plpy.notice (msg + ' via subprocess returns ' + str (z))

return None;
$$ LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;

-- CREATE TRIGGER py_ins_tp_trigger
--      AFTER INSERT ON tp
--      FOR EACH ROW
--    EXECUTE PROCEDURE py_tp_notify_trigger();

------------------------------------------------------------
-- useful debugging function
------------------------------------------------------------

CREATE OR REPLACE FUNCTION fun() RETURNS SETOF text AS
$$
import os
import sys

ct = plpy.execute("""\
         select max (counts)
         from p1""")[0]['max']
plpy.notice (ct)

plpy.execute ("INSERT INTO p1 VALUES (" + str (ct+1) + ", 'on');")

return os.listdir('/home/mininet/ravel')
$$
LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;

CREATE OR REPLACE FUNCTION fun2() RETURNS text AS
$$
plpy.notice ('fun2 begins')

fo = open ('/home/mininet/ravel/log.txt', 'a')
def logfunc(msg,f=fo):
    f.write(msg+'\n')
logfunc ('fun2 write log')
return str ('fun2 return')
$$
LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;

-- f = open('/tmp/log2.txt', 'w')
    -- f.flush()


CREATE OR REPLACE FUNCTION log() RETURNS text AS
$$
import time
plpy.notice ('log begins')
plpy.log ('hello log')
t = time.time ()
plpy.log ('log time: ' + str (t))

t = time.time ()
plpy.debug ('debug time: ' + str (t))

t = time.time ()
plpy.info ('info time: ' + str (t))

return str ('log ends')
$$
LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;


-- msg = '/usr/bin/sudo /usr/bin/ovs-ofctl add-flow s6 in_port=2,actions=output:1'
-- x = os.system (msg)
-- plpy.notice (msg + ' via os.system returns ' + str (x) )

-- y = os.system (msg)
-- plpy.notice (msg + ' via os.system returns ' + str (y) )
-- import subprocess
-- y = subprocess.call(msg,shell=True)
-- plpy.notice (msg + ' via subprocess returns ' + str (y) )

CREATE OR REPLACE FUNCTION concat(text, text) RETURNS text AS '
#!/bin/sh
echo "$1$2"
ls
' LANGUAGE plsh;


CREATE OR REPLACE FUNCTION hello() RETURNS text AS '
#!/bin/sh
echo "$1$2"
ls
' LANGUAGE plsh;


CREATE OR REPLACE FUNCTION test() RETURNS text AS '
#!/bin/sh
/usr/bin/sudo /usr/bin/ovs-ofctl add-flow s6 in_port=2,actions=output:1
' LANGUAGE plsh;


----------------------------------------------------------------------
-- common to all
----------------------------------------------------------------------

INSERT into p1 values (0,'on') ;
