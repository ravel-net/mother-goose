DROP TABLE IF EXISTS clock CASCADE;
CREATE UNLOGGED TABLE clock (
       counts  	integer,
       PRIMARY key (counts)
);
INSERT into clock (counts) values (0) ; -- initialize clock


DROP TABLE IF EXISTS p_spv CASCADE;
CREATE UNLOGGED TABLE p_spv (
       counts  	integer,
       status 	text,
       PRIMARY key (counts)
);

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

DROP TABLE IF EXISTS switches CASCADE;
CREATE UNLOGGED TABLE switches (
       sid	integer
);

DROP TABLE IF EXISTS hosts CASCADE;
CREATE UNLOGGED TABLE hosts (
       hid	integer
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
       vol	integer
       -- PRIMARY KEY (fid)
);

DROP TABLE IF EXISTS tm_delta CASCADE;
CREATE UNLOGGED TABLE tm_delta (
       fid      integer,
       src	integer,
       dst	integer,
       vol	integer,
       isadd	integer
);

CREATE OR REPLACE RULE tm_ins AS
       ON INSERT TO tm
       DO ALSO
           INSERT INTO tm_delta values (NEW.fid, NEW.src, NEW.dst, NEW.vol, 1);

CREATE OR REPLACE RULE tm_del AS
       ON DELETE TO tm
       DO ALSO(
           INSERT INTO tm_delta values (OLD.fid, OLD.src, OLD.dst, OLD.vol, 0);
	   DELETE FROM tm_delta WHERE tm_delta.fid = OLD.fid AND isadd = 1;
	   );


----------------------------------------------------------------------
----------------------------------------------------------------------
----------------------------------------------------------------------
---------- traffic matrix facing user

DROP TABLE IF EXISTS utm CASCADE;
CREATE UNLOGGED TABLE utm (
       fid      integer,
       host1	integer,
       host2	integer
       -- PRIMARY KEY (fid)
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
----------------------------------------------------------------------
-- routing application


-- CREATE TRIGGER tm_in_trigger
--      AFTER INSERT ON tm
--      FOR EACH ROW
--    EXECUTE PROCEDURE protocol_fun();


DROP TABLE IF EXISTS rtm_clock CASCADE;
CREATE UNLOGGED TABLE rtm_clock (
       counts  	integer
);
INSERT into rtm_clock (counts) values (0) ;

CREATE TRIGGER rtm_clock_ins
     AFTER INSERT ON rtm_clock
     FOR EACH ROW
   EXECUTE PROCEDURE protocol_fun();


DROP TABLE IF EXISTS rtm CASCADE;
CREATE UNLOGGED TABLE rtm (
       fid      integer,
       host1	integer,
       host2	integer
);

CREATE OR REPLACE RULE rtm_ins AS
       ON INSERT TO rtm
       DO ALSO (
       	  INSERT INTO utm VALUES (NEW.fid, NEW.host1, NEW.host2);
	  INSERT INTO rtm_clock VALUES (1);
       );

CREATE OR REPLACE RULE rtm_del AS
       ON DELETE TO rtm
       DO ALSO (
       	  DELETE FROM utm WHERE fid = OLD.fid;
	  INSERT INTO rtm_clock VALUES (2);
       );

-- CREATE OR REPLACE FUNCTION rtm_del_fun() RETURNS TRIGGER AS
-- $$
-- plpy.notice ("rtm_del_fun")
-- f = TD["old"]["fid"]

-- plpy.execute ("DELETE FROM utm WHERE utm.fid = " + str (f) + ";")
-- plpy.execute ("INSERT INTO rtm_clock VALUES (2);")
-- return None;
-- $$
-- LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;

-- CREATE TRIGGER rtm_del_trigger
--      AFTER DELETE ON rtm
--      FOR EACH ROW
--    EXECUTE PROCEDURE rtm_del_fun ();



-- CREATE OR REPLACE RULE rtm_del AS
--        ON DELETE TO rtm
--        DO INSTEAD (
--           DELETE FROM utm WHERE utm.fid = OLD.fid;
--           INSERT INTO rtm_clock VALUES (2);
--        );

DROP TABLE IF EXISTS spv_tb_ins CASCADE;
CREATE UNLOGGED TABLE spv_tb_ins (
       fid  	integer,
       pid	integer,
       sid	integer,
       nid 	integer
);

DROP TABLE IF EXISTS spv_tb_del CASCADE;
CREATE UNLOGGED TABLE spv_tb_del (
       fid  	integer,
       pid	integer,
       sid	integer,
       nid 	integer
);

CREATE OR REPLACE FUNCTION spv_constraint1_fun ()
RETURNS TRIGGER
AS $$
plpy.notice ("hello")
if TD["new"]["status"] == 'on':
    tm = plpy.execute ("SELECT * FROM tm_delta;")

    for t in tm:
        if t["isadd"] == 1:
            f = t["fid"]	   
            s = t["src"]
            d = t["dst"]
            pv = plpy.execute("""SELECT array(SELECT id1 FROM pgr_dijkstra('SELECT 1 as id, sid as source, nid as target, 1.0::float8 as cost FROM tp WHERE isactive = 1',""" +str (s) + "," + str (d)  + ",FALSE, FALSE))""")[0]['array']
	   
            l = len (pv)
            for i in range (l):
                if i + 2 < l:
                    plpy.execute ("INSERT INTO cf (fid,pid,sid,nid) VALUES (" + str (f) + "," + str (pv[i]) + "," +str (pv[i+1]) +"," + str (pv[i+2])+  ");")

        elif t["isadd"] == 0:
            f = t["fid"]
            plpy.execute ("DELETE FROM cf WHERE fid =" +str (f) +";")

    plpy.execute ("DELETE FROM tm_delta;")
return None;
$$ LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;

CREATE TRIGGER spv_constraint1
     AFTER INSERT ON p_spv
     FOR EACH ROW
   EXECUTE PROCEDURE spv_constraint1_fun();

-- CREATE OR REPLACE FUNCTION tm_del2spv_fun ()
-- RETURNS TRIGGER
-- AS $$
-- f = TD["old"]["fid"]
-- plpy.notice (f)
-- plpy.execute("INSERT INTO spv_tb_del VALUES (fid) (" + str (f) + ");")
-- return None;
-- $$ LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;

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

CREATE TRIGGER tp_up_spv_trigger
     AFTER UPDATE ON tp
     FOR EACH ROW
   EXECUTE PROCEDURE tp2spv_fun();

CREATE OR REPLACE RULE spv_constaint2 AS
       ON INSERT TO p_spv
       WHERE NEW.status = 'on'
       DO ALSO
           (UPDATE p_spv SET status = 'off' WHERE counts = NEW.counts;
	   DELETE FROM cf WHERE (fid,pid,sid,nid) IN (SELECT * FROM spv_tb_del);
           INSERT INTO cf (fid,pid,sid,nid) (SELECT * FROM spv_tb_ins);
	   DELETE FROM spv_tb_del ;   
	   DELETE FROM spv_tb_ins ;   
	   );

CREATE OR REPLACE RULE tick_spv AS
       ON UPDATE TO p_spv
       WHERE (NEW.status = 'off')
       DO ALSO
           INSERT INTO clock values (NEW.counts);

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
    f.write(msg)

logfunc ('i')
logfunc ('i')

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
    f.write(msg)

logfunc ('d')

logfunc ('d')

fo.flush ()

return None;
$$ LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;


CREATE TRIGGER del_flow_trigger
     AFTER DELETE ON cf
     FOR EACH ROW
   EXECUTE PROCEDURE del_flow_fun();

-- ----------------------------------------------------------------------
-- -- obs application
-- ----------------------------------------------------------------------
-- DROP TABLE IF EXISTS selected_switches CASCADE;
-- CREATE UNLOGGED TABLE selected_switches (
--        sid    	
--        oid  	integer
-- );

-- CREATE TABLE obs_participants
-- AS (SELECT sid, 1 as isactive
--     FROM obs_participants);

-- CREATE OR REPLACE RULE wp_up AS
--        ON UPDATE TO wp
--        DO ALSO
--        	  UPDATE tp SET isactive = NEW.isactive WHERE sid = NEW.sid OR nid = NEW.sid;


-- def load_obs_schema (dbname, username, size):
--     conn = psycopg2.connect(database= dbname, user= username)
--     conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
--     cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

--     cur.execute ("SELECT * FROM switches;")
--     cs = cur.fetchall ()
--     selected_switches = [int (s['sid']) for s in cs]

--     cur.execute ("""

--     """)

----------------------------------------------------------------------
-- maintenance (mt) application
----------------------------------------------------------------------
-- DROP TABLE IF EXISTS mt CASCADE;
-- CREATE TABLE mt
-- AS (SELECT sid, 1 as isactive
--     FROM switches);

-- CREATE OR REPLACE RULE mt_up AS
--        ON UPDATE TO mt
--        DO ALSO
--        	  UPDATE tp SET isactive = NEW.isactive WHERE sid = NEW.sid OR nid = NEW.sid;

DROP TABLE IF EXISTS mt_tb CASCADE;
CREATE UNLOGGED TABLE mt_tb (
       sid	integer
);

CREATE OR REPLACE VIEW mt AS (
       SELECT mt_tb.sid,
	      sum (isactive) AS isactive 
       FROM mt_tb, tp
       WHERE mt_tb.sid = tp.sid
       GROUP BY mt_tb.sid 
);

CREATE OR REPLACE RULE mt2tp AS
       ON UPDATE TO mt
       DO INSTEAD
       	  UPDATE tp SET isactive = NEW.isactive WHERE sid = NEW.sid OR nid = NEW.sid;

----------------------------------------------------------------------
-- acl application
----------------------------------------------------------------------

DROP TABLE IF EXISTS acl_tb CASCADE;
CREATE UNLOGGED TABLE acl_tb (
       end1	      integer,
       end2 	      integer,
       inBlklist      integer
);

CREATE OR REPLACE VIEW acl AS(
       SELECT DISTINCT end1, end2, inBlklist, 1 as isViolated
       FROM acl_tb, utm
       WHERE acl_tb.end1 = utm.host1 and acl_tb.end2 = utm.host2 and inBlklist = 1);

CREATE OR REPLACE RULE acl2utm AS
       ON UPDATE TO acl
       DO INSTEAD
       	  DELETE FROM utm WHERE host1 = NEW.end1 AND host2 = NEW.end2;

-- CREATE OR REPLACE RULE acl2tm2 AS
--        ON UPDATE TO acl
--        WHERE NEW.inBlklist = 0
--        DO INSTEAD
--        	  UPDATE acl_tb SET inBlklist = 0 WHERE sid = NEW.sid AND nid = NEW.nid;

----------------------------------------------------------------------
-- load_balance application
----------------------------------------------------------------------

DROP TABLE IF EXISTS lb_tb CASCADE;
CREATE UNLOGGED TABLE lb_tb (
       sid	integer
       -- nid 	integer
);

CREATE OR REPLACE VIEW lb AS(
       SELECT sid, count (*) AS load 
       FROM lb_tb, utm
       WHERE lb_tb.sid = utm.host2
       GROUP BY sid
       );

CREATE OR REPLACE RULE lb2utm AS
       ON UPDATE TO lb
       DO INSTEAD
       	  DELETE FROM utm WHERE fid IN (SELECT fid FROM utm WHERE host2 = NEW.sid LIMIT (OLD.load - NEW.load));

----------------------------------------------------------------------
-- way point application
----------------------------------------------------------------------

DROP TABLE IF EXISTS wp_tb CASCADE;
CREATE UNLOGGED TABLE wp_tb (
       fid	integer,
       wid	integer
);

DROP VIEW IF EXISTS wp CASCADE;
CREATE OR REPLACE VIEW wp AS (
       SELECT DISTINCT wp_tb.fid, wp_tb.wid, 1 as isAbsent
       FROM wp_tb, cf
       WHERE wp_tb.fid = cf.fid
       	     AND wp_tb.wid NOT IN (SELECT sid FROM cf WHERE cf.fid = wp_tb.fid)
);
