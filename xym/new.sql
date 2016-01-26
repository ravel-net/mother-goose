----------------------------------------------------------------------
-- merlin (bandwidth requirement)
----------------------------------------------------------------------

DROP TABLE IF EXISTS Merlin_policy CASCADE;
CREATE UNLOGGED TABLE MERLIN_policy (
       fid	      integer,
       rate 	      integer,
       PRIMARY key (fid)
);

CREATE OR REPLACE VIEW MERLIN_violation AS (
       SELECT tm.fid, rate AS req, vol AS asgn
       FROM tm, Merlin_policy
       WHERE tm.fid = Merlin_policy.fid AND rate > vol
);

CREATE OR REPLACE RULE Merlin_repair AS
       ON DELETE TO Merlin_violation
       DO INSTEAD
              UPDATE tm SET vol = OLD.req WHERE fid = OLD.fid;

----------------------------------------------------------------------
-- PGA (endpoints, service chain)
----------------------------------------------------------------------

DROP TABLE IF EXISTS PGA_policy CASCADE;
CREATE UNLOGGED TABLE PGA_policy (
       gid1	      integer,
       gid2 	      integer,
       MB	      text,
       PRIMARY key (gid1, gid2)		
);
CREATE INDEX ON PGA_policy (gid1, gid2);

DROP TABLE IF EXISTS PGA_group CASCADE;
CREATE UNLOGGED TABLE PGA_group(
       gid	      integer,
       sid	      integer
);
CREATE INDEX ON PGA_group (gid);

DROP TABLE IF EXISTS PGA CASCADE;
CREATE TABLE PGA AS(
	WITH tmp AS(
        	SELECT p1.sid as sid1, p2.sid as sid2, MB
        	FROM PGA_group p1, PGA_group p2, PGA_policy
        	WHERE p1.gid = gid1 AND p2.gid = gid2)
	SELECT sid1, sid2, MB, count(*) AS n
        FROM tmp
        GROUP BY sid1, sid2, MB	
);
CREATE INDEX ON PGA (sid1, sid2);


DROP VIEW IF EXISTS PGA_v CASCADE;
CREATE OR REPLACE VIEW PGA_v AS(
	SELECT DISTINCT p1.sid as sid1, p2.sid as sid2, MB
	FROM PGA_group p1, PGA_group p2, PGA_policy
	WHERE p1.gid = gid1 AND p2.gid = gid2
);



CREATE OR REPLACE VIEW PGA_violation AS (
       SELECT fid, MB
       FROM tm, PGA       
       WHERE src = sid1 AND dst = sid2 AND
       ((MB = 'FW' AND FW=0) OR (MB='LB' AND LB=0)) 
);

CREATE OR REPLACE RULE PGA_repair AS
       ON DELETE TO PGA_violation
       DO INSTEAD
       (
       UPDATE tm SET FW = 1 WHERE fid = OLD.fid AND OLD.MB = 'FW';
       UPDATE tm SET LB = 1 WHERE fid = OLD.fid AND OLD.MB = 'LB';
       );

---emergingthreats---
DROP TABLE IF EXISTS groupid CASCADE;
CREATE TABLE groupid (
        gname           varchar(20),
        gid             integer,
        PRIMARY key (gid)
);

DROP TABLE IF EXISTS addrid CASCADE;
CREATE TABLE addrid (
        addr            varchar(30),
        aid             integer,
        PRIMARY key (aid)
);

DROP TABLE IF EXISTS group_str CASCADE;
CREATE TABLE group_str (
        gname           varchar(20),
        aid_array       integer[]
);











----triggers------

CREATE OR REPLACE FUNCTION f_policy()
RETURNS TRIGGER AS
$$
if(TD["event"] == "INSERT"):
        new_gid1 = TD["new"]["gid1"]
        new_gid2 = TD["new"]["gid2"]
        new_MB = TD["new"]["mb"]
	sa1 = plpy.execute("SELECT sid FROM PGA_group WHERE gid = "+ str(new_gid1))
	sa2 = plpy.execute("SELECT sid FROM PGA_group WHERE gid = "+ str(new_gid2))
	if(sa1.nrows()!=0 and sa2.nrows()!=0):
		for s1 in sa1:
			for s2 in sa2:
				sa1_str = str(s1["sid"])
				sa2_str = str(s2["sid"])
				find = plpy.execute("SELECT * FROM PGA WHERE sid1="+sa1_str+" and sid2="+ sa2_str+" and mb = '"+ str(new_MB)+ "'")
				if(find.nrows()!=0):
					plpy.execute("UPDATE PGA_table SET n = n+1 WHERE sid1 = "+sa1_str + " and sid2 = "+ sa2_str+" and mb='" + str(new_MB)+"'")
				else:
					plpy.execute("INSERT INTO PGA VALUES("+ sa1_str+ ", "+ sa2_str+ ", '"+ str(new_MB)+ "', 1);")
	
if(TD["event"] == "DELETE"):
	old_gid1 = TD["old"]["gid1"]
        old_gid2 = TD["old"]["gid2"]
        old_MB = TD["old"]["mb"]
	sa1 = plpy.execute("SELECT sid FROM PGA_group WHERE gid = "+ str(old_gid1))
        sa2 = plpy.execute("SELECT sid FROM PGA_group WHERE gid = "+ str(old_gid2))
	if(sa1.nrows()!=0 and sa2.nrows()!=0):
                for s1 in sa1:
                        for s2 in sa2:
				sa1_str = str(s1["sid"])
                                sa2_str = str(s2["sid"])
				plpy.execute("UPDATE PGA SET n = n - 1 WHERE sid1 = "+sa1_str + " and sid2 = "+sa2_str+" and mb='" + str(old_MB)+"'")
	plpy.execute("DELETE FROM PGA WHERE n = 0")

if(TD["event"] == "UPDATE"):
        new_gid1 = TD["new"]["gid1"]
        new_gid2 = TD["new"]["gid2"]
        new_MB = TD["new"]["mb"]
        sa1 = plpy.execute("SELECT sid FROM PGA_group WHERE gid = "+ str(new_gid1))
        sa2 = plpy.execute("SELECT sid FROM PGA_group WHERE gid = "+ str(new_gid2))
        if(sa1.nrows()!=0 and sa2.nrows()!=0):
                for s1 in sa1:
                        for s2 in sa2:
                                sa1_str = str(s1["sid"])
                                sa2_str = str(s2["sid"])
                                find = plpy.execute("SELECT * FROM PGA WHERE sid1="+sa1_str+" and sid2="+ sa2_str+" and  mb = '"+ str(new_MB)+ "'")
                                if(find.nrows()!=0):                                        
					plpy.execute("UPDATE PGA SET n = n+1 WHERE sid1 = "+sa1_str + " and sid2 = "+ sa2_str+" and mb='" + str(new_MB)+"'")
                                else:
                                        plpy.execute("INSERT INTO PGA VALUES("+ sa1_str+ ", "+ sa2_str+ ", '"+ str(new_MB)+ "', 1);")


        old_gid1 = TD["old"]["gid1"]
        old_gid2 = TD["old"]["gid2"]
        old_MB = TD["old"]["mb"]
        sa1 = plpy.execute("SELECT sid FROM PGA_group WHERE gid = "+ str(old_gid1))
        sa2 = plpy.execute("SELECT sid FROM PGA_group WHERE gid = "+ str(old_gid2))
        if(sa1.nrows()!=0 and sa2.nrows()!=0):
                for s1 in sa1:
                        for s2 in sa2:
                                sa1_str = str(s1["sid"])
                                sa2_str = str(s2["sid"])                                
				plpy.execute("UPDATE PGA SET n = n-1 WHERE sid1 = "+sa1_str + " and sid2 = "+sa2_str+" and mb='" + str(old_MB)+"'")
        plpy.execute("DELETE FROM pga WHERE n = 0")

return None;
$$
LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;

CREATE TRIGGER t_policy
        BEFORE INSERT OR DELETE OR UPDATE ON PGA_policy
        FOR EACH ROW
EXECUTE PROCEDURE f_policy();


CREATE OR REPLACE FUNCTION f_group()
RETURNS TRIGGER AS
$$
if(TD["event"] == "INSERT"):
        new_gid = TD["new"]["gid"]
        new_sid = TD["new"]["sid"]
	gid_find = plpy.execute("SELECT * FROM pga_policy where gid1= "+ str(new_gid))
	if(gid_find.nrows()!=0):
		for i in gid_find:
			mbi = i["mb"]
			other = plpy.execute("SELECT * FROM pga_group where gid = "+ str(i["gid2"]) )
			for j in other:	
				f = plpy.execute("SELECT * FROM pga WHERE sid1 = "+ str(new_sid)+ " and sid2 = "+ str(j["sid"])+ " and mb = '"+ str(mbi)+"'")
				if(f.nrows()!=0):
					plpy.execute("UPDATE PGA SET n = n + 1 WHERE sid1 = "+ str(new_sid) + " and sid2 = "+ str(j["sid"])+" and mb='" + str(mbi)+"'")
				else:
					plpy.execute("INSERT INTO pga VALUES("+ str(new_sid) +", "+ str(j["sid"])+ ", '"+ str(mbi)+ "', 1)")
	
	gid_find = plpy.execute("SELECT * FROM pga_policy where gid2= "+ str(new_gid))
        if(gid_find.nrows()!=0):
                for i in gid_find:
			mbi = i["mb"]
                        other = plpy.execute("SELECT * FROM pga_group where gid = "+ str(i["gid1"]) )
                        for j in other:
                                f = plpy.execute("SELECT * FROM pga WHERE sid1 = "+ str(j["sid"])+ " and sid2 = "+ str(new_sid)+ " and mb = '"+ str(mbi)+"'")
                                if(f.nrows()!=0):
                                        plpy.execute("UPDATE PGA SET n = n + 1 WHERE sid1 = "+ str(j["sid"]) + " and sid2 = "+ str(new_sid)+" and mb='" + str(mbi)+"'")
                                else:
                                        plpy.execute("INSERT INTO pga VALUES("+ str(j["sid"]) +", "+ str(new_sid) + ", '"+ str(mbi)+ "', 1)")

if(TD["event"] == "DELETE"):
	old_gid = TD["old"]["gid"]
	old_sid = TD["old"]["sid"]
	gid_find = plpy.execute("SELECT * FROM pga_policy where gid1= "+ str(old_gid))
	if(gid_find.nrows()!=0):
		for i in gid_find:
			mbi = i["mb"]
			other = plpy.execute("SELECT * FROM pga_group where gid = "+ str(i["gid2"]) )
			for j in other:
				plpy.execute("UPDATE PGA SET n = n - 1 WHERE sid1 = "+ str(old_sid) + " and sid2 = "+ str(j["sid"])+" and mb='" + str(mbi)+"'")	
	gid_find = plpy.execute("SELECT * FROM pga_policy where gid2= "+ str(old_gid))
	if(gid_find.nrows()!=0):
                for i in gid_find:
			mbi = i["mb"]
                        other = plpy.execute("SELECT * FROM pga_group where gid = "+ str(i["gid1"]) )
                        for j in other:
				plpy.execute("UPDATE PGA SET n = n - 1 WHERE sid1 = "+ str(j["sid"]) + " and sid2 = "+ str(old_sid)+" and mb='" + str(mbi)+"'")
			
	plpy.execute("DELETE FROM PGA WHERE n = 0")


if(TD["event"] == "UPDATE"):
        new_gid = TD["new"]["gid"]
        new_sid = TD["new"]["sid"]
        gid_find = plpy.execute("SELECT * FROM pga_policy where gid1= "+ str(new_gid))
        if(gid_find.nrows()!=0):
                mbi = gid_find[0]["mb"]
                for i in gid_find:
                        other = plpy.execute("SELECT * FROM pga_group where gid = "+ str(i["gid2"]) )
                        for j in other:
                                f = plpy.execute("SELECT * FROM pga WHERE sid1 = "+ str(new_sid)+ " and sid2 = "+ str(j["sid"])+ " and mb='"+ str(mbi)+"'")
                                if(f.nrows()!=0):
                                        plpy.execute("UPDATE PGA SET n = n + 1 WHERE sid1 = "+ str(new_sid) + " and sid2 = "+ str(j["sid"])+" and mb='" + str(mbi)+"'")
                                else:
                                        plpy.execute("INSERT INTO pga VALUES("+ str(new_sid) +", "+ str(j["sid"])+ ", '"+ mbi+ "', 1)")

        gid_find = plpy.execute("SELECT * FROM pga_policy where gid2= "+ str(new_gid))
        if(gid_find.nrows()!=0):
                mbi = gid_find[0]["mb"]
                for i in gid_find:
                        other = plpy.execute("SELECT * FROM pga_group where gid = "+ str(i["gid1"]) )
                        for j in other:
                                f = plpy.execute("SELECT * FROM pga WHERE sid1 = "+ str(j["sid"])+ " and sid2 = "+ str(new_sid)+ " and mb='"+ str(mbi)+"'")
                                if(f.nrows()!=0):
                                        plpy.execute("UPDATE PGA SET n = n + 1 WHERE sid1 = "+ str(j["sid"]) + " and sid2 = "+ str(new_sid)+" and mb='" + str(mbi)+"'")
                                else:
                                        plpy.execute("INSERT INTO pga VALUES("+ str(j["sid"]) +", "+ str(new_sid) + ", '"+ str(mbi)+ "', 1)")

        old_gid = TD["old"]["gid"]
        old_sid = TD["old"]["sid"]
        gid_find = plpy.execute("SELECT * FROM pga_policy where gid1= "+ str(old_gid))
        if(gid_find.nrows()!=0):
                mbi = gid_find[0]["mb"]
                for i in gid_find:
                        other = plpy.execute("SELECT * FROM pga_group where gid = "+ str(i["gid2"]) )
                        for j in other:
                                plpy.execute("UPDATE PGA SET n = n - 1 WHERE sid1 = "+ str(old_sid) + " and sid2 = "+ str(j["sid"])+" and mb='" + str(mbi)+"'")
        gid_find = plpy.execute("SELECT * FROM pga_policy where gid2= "+ str(old_gid))
        if(gid_find.nrows()!=0):
                mbi = gid_find[0]["mb"]
                for i in gid_find:
                        other = plpy.execute("SELECT * FROM pga_group where gid = "+ str(i["gid1"]) )
                        for j in other:
                                plpy.execute("UPDATE PGA SET n = n - 1 WHERE sid1 = "+ str(j["sid"]) + " and sid2 = "+ str(old_sid)+" and mb='" + str(mbi)+"'")

        plpy.execute("DELETE FROM PGA WHERE n = 0")



return None;
$$
LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;

CREATE TRIGGER t_group
        BEFORE INSERT OR DELETE OR UPDATE ON PGA_group
        FOR EACH ROW
EXECUTE PROCEDURE f_group();


----------------------------------------------------------------------
-- kinetic (stateful firewall)
----------------------------------------------------------------------
DROP TABLE IF EXISTS FW_policy_acl CASCADE;
CREATE UNLOGGED TABLE FW_policy_acl (
       end1	      integer,
       end2 	      integer,
       allow	      integer,
       PRIMARY key (end1, end2)		
);
CREATE INDEX ON FW_policy_acl (end1,end2);

DROP TABLE IF EXISTS FW_policy_user CASCADE;
CREATE UNLOGGED TABLE FW_policy_user (
       uid	      integer
);

CREATE OR REPLACE RULE FW1 AS
       ON INSERT TO tm
       WHERE ((NEW.src, NEW.dst) NOT IN (SELECT end2, end1 FROM FW_policy_acl)) AND 
       	      (NEW.src IN (SELECT * FROM FW_policy_user))
       DO ALSO (
       	  INSERT INTO FW_policy_acl VALUES (NEW.dst, NEW.src, 1);
       );

CREATE OR REPLACE RULE FW2 AS
       ON DELETE TO tm
       WHERE (SELECT count(*) FROM tm WHERE src = OLD.src AND dst = OLD.dst) = 1
       DO ALSO 
       	  DELETE FROM FW_policy_acl WHERE end2 = OLD.src AND end1 = OLD.dst;

CREATE OR REPLACE VIEW FW_violation AS (
       SELECT fid
       FROM tm 
       WHERE FW = 1  AND (src, dst) NOT IN (SELECT end1, end2 FROM FW_policy_acl)
);

CREATE OR REPLACE RULE FW_repair AS
       ON DELETE TO FW_violation
       DO INSTEAD
       	  DELETE FROM tm WHERE fid = OLD.fid;

----------------------------------------------------------------------
-- Merlin
----------------------------------------------------------------------
-- 
-- DROP TABLE IF EXISTS tm_delta CASCADE;
-- CREATE UNLOGGED TABLE tm_delta (
--        fid      integer,
--        src	integer,
--        dst	integer,
--        vol	integer,
--        FW	integer,
--        LB	integer,       
--        isadd	integer
-- );
-- CREATE INDEX ON tm_delta (fid,src,dst);

-- CREATE OR REPLACE FUNCTION protocol_fun() RETURNS TRIGGER AS
-- $$
-- plpy.notice ("engage ravel protocol")

-- ct = plpy.execute("""select max (counts) from clock""")[0]['max']
-- plpy.execute ("INSERT INTO p_spv VALUES (" + str (ct+1) + ", 'on');")
-- return None;
-- $$
-- LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;

-- CREATE TRIGGER tp_up_trigger
--      AFTER UPDATE ON tp
--      FOR EACH ROW
--    EXECUTE PROCEDURE protocol_fun();

-- CREATE OR REPLACE VIEW acl AS(
--        -- SELECT DISTINCT fid, end1, end2, allow
--        SELECT DISTINCT fid, allow
--        FROM acl_policy, tm
--        WHERE  src = end1 AND dst = end2 and allow = 0
-- );

----------------------------------------------------------------------
-- orchestrating Merlin, Kinetic, PGA
----------------------------------------------------------------------

DROP TABLE IF EXISTS p_PGA CASCADE;
CREATE UNLOGGED TABLE p_PGA (
       counts  	integer,
       status 	text,
       PRIMARY key (counts)
);

CREATE OR REPLACE RULE run_PGA AS
       ON INSERT TO p_PGA
       WHERE (NEW.status = 'on')
       DO ALSO (
           DELETE FROM PGA_violation;
	   UPDATE p_PGA SET status = 'off' WHERE counts = NEW.counts;
	  );


DROP TABLE IF EXISTS p_FW CASCADE;
CREATE UNLOGGED TABLE p_FW (
       counts  	integer,
       status 	text,
       PRIMARY key (counts)
);

CREATE OR REPLACE RULE run_FW AS
       ON INSERT TO p_FW
       WHERE (NEW.status = 'on')
       DO ALSO (
           DELETE FROM FW_violation;
	   UPDATE p_FW SET status = 'off' WHERE counts = NEW.counts;
	  );


DROP TABLE IF EXISTS p_Merlin CASCADE;
CREATE UNLOGGED TABLE p_Merlin (
       counts  	integer,
       status 	text,
       PRIMARY key (counts)
);

CREATE OR REPLACE RULE run_Merlin AS
       ON INSERT TO p_Merlin
       WHERE (NEW.status = 'on')
       DO ALSO (
           DELETE FROM FW_violation;
	   UPDATE p_Merlin SET status = 'off' WHERE counts = NEW.counts;
	  );


----------------------------------------------------------------------
-- hook up with routing (existing code)
----------------------------------------------------------------------

DROP TABLE IF EXISTS p_RT CASCADE;
CREATE UNLOGGED TABLE p_RT (
       counts  	integer,
       status 	text,
       PRIMARY key (counts)
);

-- run_RT_trigger instead is analogous to
-- DELETE FROM rt_violation;
CREATE TRIGGER run_RT_trigger
     AFTER INSERT ON p_RT
     FOR EACH ROW
   EXECUTE PROCEDURE spv_constraint1_fun();

CREATE OR REPLACE RULE run_RT AS
       ON INSERT TO p_RT
       WHERE (NEW.status = 'on')
       DO ALSO (
	   UPDATE p_RT SET status = 'off' WHERE counts = NEW.counts;
	  );

-- CREATE OR REPLACE RULE rt2c AS
--        ON UPDATE TO p_spv
--        WHERE (NEW.status = 'off')
--        DO ALSO
--            INSERT INTO clock values (NEW.counts);

----------------------------------------------------------------------
-- implement a total order
----------------------------------------------------------------------

CREATE OR REPLACE RULE PGA2FW AS
       ON UPDATE TO p_PGA
       WHERE (NEW.status = 'off')
       DO ALSO
           INSERT INTO p_FW values (NEW.counts, 'on');

CREATE OR REPLACE RULE FW2Merlin AS
       ON UPDATE TO p_FW
       WHERE (NEW.status = 'off')
       DO ALSO
           INSERT INTO p_Merlin values (NEW.counts, 'on');

-- CREATE OR REPLACE RULE Merlin2c AS
--        ON UPDATE TO p_Merlin
--        WHERE (NEW.status = 'off')
--        DO ALSO
--            INSERT INTO clock values (NEW.counts);

CREATE OR REPLACE RULE Merlin2c AS
       ON UPDATE TO p_Merlin
       WHERE (NEW.status = 'off')
       DO ALSO
           INSERT INTO p_RT values (NEW.counts, 'on');

CREATE OR REPLACE RULE Routing2c AS
       ON UPDATE TO p_RT
       WHERE (NEW.status = 'off')
       DO ALSO
           INSERT INTO clock values (NEW.counts);

----------------------------------------------------------------------
-- toy, policy configuration
----------------------------------------------------------------------

-- (PGA) configuration
--INSERT INTO PGA_policy (gid1, gid2, MB)
--VALUES (1,2,'FW'),
--       (4,3,'LB');

--INSERT INTO PGA_group 
--       (gid, sid)
--VALUES
--	(1, 5),
--	(2, 6),
--	(3, 6),
--	(3, 7),
--	(4, 5),
--	(4, 8);

INSERT INTO groupid
VALUES
        ('feodo', 1),
        ('zeus', 2),
        ('spyeye', 3),
        ('palevo', 4),
        ('spamhaus', 5),
        ('dshield', 6),
        ('good', 7);


-- (Kinetic) firewall configuration
INSERT INTO FW_policy_acl VALUES (8,7,0);
INSERT INTO FW_policy_user VALUES (6),(8);
