DROP TABLE IF EXISTS clock CASCADE;
CREATE UNLOGGED TABLE clock (
       counts  	integer,
       PRIMARY key (counts)
);
INSERT into clock (counts) values (0) ; -- initialize clock


CREATE OR REPLACE FUNCTION protocol_fun() RETURNS TRIGGER AS
$$
plpy.notice ("engage ravel protocol")

ct = plpy.execute("""select max (counts) from clock""")[0]['max']
plpy.execute ("INSERT INTO p_spv VALUES (" + str (ct+1) + ", 'on');")
return None;
$$
LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;

------------------------------------------------------------
------------------------------------------------------------
------------------------------------------------------------
------------------------------------------------------------

DROP TABLE IF EXISTS pox_tp CASCADE;
CREATE UNLOGGED TABLE pox_tp (
       in_switch  integer,
       in_port	  integer,
       out_switch integer,
       out_port   integer
);

-- CREATE OR REPLACE FUNCTION pox_tp_fun() RETURNS TRIGGER AS
-- $$
-- plpy.notice ("pox monitors mininet switch-switch links")

-- ct = plpy.execute("""select max (counts) from clock""")[0]['max']
-- plpy.execute ("INSERT INTO p1 VALUES (" + str (ct+1) + ", 'on');")
-- return None;
-- $$
-- LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;

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

CREATE TRIGGER tp_up_trigger
     AFTER UPDATE ON tp
     FOR EACH ROW
   EXECUTE PROCEDURE protocol_fun();

CREATE OR REPLACE RULE pox_tp_ins_rule AS
       ON INSERT TO pox_tp
       DO ALSO
           UPDATE tp SET isactive = 1 WHERE sid = NEW.out_switch AND nid = NEW.in_switch;

CREATE OR REPLACE RULE pox_tp_del_rule AS
       ON DELETE TO pox_tp
       DO ALSO
           UPDATE tp SET isactive = 0 WHERE sid = OLD.out_switch AND nid = OLD.in_switch;


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


CREATE TRIGGER tm_in_trigger
     AFTER INSERT ON tm
     FOR EACH ROW
   EXECUTE PROCEDURE protocol_fun();

CREATE TRIGGER tm_del_trigger
     AFTER DELETE ON tm
     FOR EACH ROW
   EXECUTE PROCEDURE protocol_fun();

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
------------------------------------------------------------

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


------------------------------------------------------------
------------------------------------------------------------
-- priority

DROP TABLE IF EXISTS p_spv CASCADE;
CREATE UNLOGGED TABLE p_spv (
       counts  	integer,
       status 	text,
       PRIMARY key (counts)
);

CREATE OR REPLACE RULE spv_constaint AS
       ON INSERT TO p_spv
       WHERE NEW.status = 'on'
       DO ALSO
           (DELETE FROM cf WHERE (fid,pid,sid,nid) IN (SELECT * FROM spv_del);
	    INSERT INTO cf (fid,pid,sid,nid) (SELECT * FROM spv_ins);
            UPDATE p_spv SET status = 'off' WHERE counts = NEW.counts;
	    );

CREATE OR REPLACE RULE tick_spv AS
       ON UPDATE TO p_spv
       WHERE (NEW.status = 'off')
       DO ALSO
           INSERT INTO clock values (NEW.counts);

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

-- CREATE OR REPLACE FUNCTION add_flow_fun ()
-- RETURNS TRIGGER
-- AS $$
-- f = TD["new"]["pid"]
-- s = TD["new"]["sid"]
-- n = TD["new"]["nid"]

-- u = plpy.execute("""select port from get_port (""" +str (s)+""") where nid = """ +str (n))
-- outport = str(u[0]['port'])
-- v = plpy.execute("""select port from get_port (""" +str (s)+""") where nid = """ +str (f))
-- inport = str (v[0]['port'])

-- cmd1 = '/usr/bin/sudo /usr/bin/ovs-ofctl add-flow s' + str (s) + ' in_port=' + inport + ',actions=output:' + outport
-- cmd2 = '/usr/bin/sudo /usr/bin/ovs-ofctl add-flow s' + str (s) + ' in_port=' + outport + ',actions=output:' + inport

-- import os
-- import sys
-- import time

-- fo = open ('/home/mininet/ravel/log.txt', 'a')
-- def logfunc(msg,f=fo):
--     f.write(msg+'\n')

-- t1 = time.time ()
-- x1 = os.system (cmd1)
-- t2 = time.time ()
-- logfunc ('add-flow s' + str (s) + '(ms): ' + str ((t2-t1)*1000))

-- t1 = time.time ()
-- x2 = os.system (cmd2)
-- t2 = time.time ()
-- logfunc ('add-flow s' + str (s) + '(ms): ' + str ((t2-t1)*1000))

-- fo.flush ()

-- return None;
-- $$ LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;

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

cmd1 = '/usr/bin/sudo /usr/bin/ovs-ofctl add-flow s' + str (s) + ' in_port=' + inport + ',actions=output:' + outport
cmd2 = '/usr/bin/sudo /usr/bin/ovs-ofctl add-flow s' + str (s) + ' in_port=' + outport + ',actions=output:' + inport

fo = open ('/home/mininet/ravel/log.txt', 'a')
def logfunc(msg,f=fo):
    f.write(msg+'\n')

logfunc ('addflow')
logfunc ('addflow')

fo.flush ()

return None;
$$ LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;

CREATE TRIGGER add_flow_trigger
     AFTER INSERT ON cf
     FOR EACH ROW
   EXECUTE PROCEDURE add_flow_fun();

------------------------------------------------------------
-- del_flow triggers
------------------------------------------------------------

-- CREATE OR REPLACE FUNCTION del_flow_fun ()
-- RETURNS TRIGGER
-- AS $$
-- f = TD["old"]["pid"]
-- s = TD["old"]["sid"]
-- n = TD["old"]["nid"]

-- u = plpy.execute("""\
--          select port
--          from get_port (""" +str (s)+""")  
--          where nid = """ +str (n))
-- outport = str(u[0]['port'])

-- v = plpy.execute("""\
--          select port
--          from get_port (""" +str (s)+""")
--          where nid = """ +str (f))
-- inport = str (v[0]['port'])

-- cmd1 = '/usr/bin/sudo /usr/bin/ovs-ofctl del-flows s' + str (s) + ' in_port=' + inport
-- cmd2 = '/usr/bin/sudo /usr/bin/ovs-ofctl del-flows s' + str (s) + ' in_port=' + outport

-- import os
-- import sys
-- import time

-- fo = open ('/home/mininet/ravel/log.txt', 'a')
-- def logfunc(msg,f=fo):
--     f.write(msg+'\n')

-- t1 = time.time ()
-- x1 = os.system (cmd1)
-- t2 = time.time ()
-- logfunc ('del-flows s' + str (s) + '(ms): ' + str ((t2-t1)*1000))

-- t1 = time.time ()
-- x1 = os.system (cmd2)
-- t2 = time.time ()
-- logfunc ('del-flows s' + str (s) + '(ms): ' + str ((t2-t1)*1000))

-- fo.flush ()

-- return None;
-- $$ LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;

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

fo = open ('/home/mininet/ravel/log.txt', 'a')
def logfunc(msg,f=fo):
    f.write(msg+'\n')

logfunc ('delflow')

logfunc ('delflow')

fo.flush ()

return None;
$$ LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;


CREATE TRIGGER del_flow_trigger
     AFTER DELETE ON cf
     FOR EACH ROW
   EXECUTE PROCEDURE del_flow_fun();
