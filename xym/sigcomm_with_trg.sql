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
CREATE UNLOGGED TABLE PGA_group (
       gid	      integer,
       sid_array      integer[],
       PRIMARY key (gid)
);
CREATE INDEX ON PGA_group (gid);


---delete later---
DROP VIEW IF EXISTS PGA_V CASCADE;
CREATE OR REPLACE VIEW PGA_V AS
	SELECT p1.sid_array AS sa1,
	       p2.sid_array AS sa2, MB
	FROM PGA_group p1, PGA_group p2, PGA_policy
	WHERE p1.gid = gid1 AND p2.gid = gid2;


----tables---
DROP TABLE IF EXISTS PGA_t CASCADE;
DROP TABLE IF EXISTS PGA_table CASCADE;
DROP VIEW IF EXISTS PGA_t_view CASCADE;



CREATE TABLE PGA_t AS(
        SELECT p1.sid_array AS sa1,
               p2.sid_array AS sa2, MB
        FROM PGA_group p1, PGA_group p2, PGA_policy
        WHERE p1.gid = gid1 AND p2.gid = gid2
);

CREATE VIEW PGA_t_view AS(
        WITH PGA_t_2 AS(
          SELECT unnest (sa1)"sid1", sa2, MB
          FROM PGA_t)
        SELECT sid1, unnest (sa2)"sid2", MB
        FROM PGA_t_2
);

CREATE TABLE PGA_table AS
        SELECT sid1, sid2, MB, count(*) AS n
        FROM PGA_t_view
        GROUP BY sid1, sid2, MB
;

CREATE OR REPLACE FUNCTION f_policy()
RETURNS TRIGGER AS
$$
if(TD["event"] == "INSERT"):
        new_gid1 = TD["new"]["gid1"]
        new_gid2 = TD["new"]["gid2"]
        new_MB = TD["new"]["mb"]
        sa1 = plpy.execute("SELECT sid_array FROM PGA_group WHERE gid = "+ str(new_gid1))
        sa2 = plpy.execute("SELECT sid_array FROM PGA_group WHERE gid = "+ str(new_gid2))
        if(sa1.nrows()!=0 and sa2.nrows()!=0):
                sa1_str = "ARRAY"+ str(sa1[0]["sid_array"])
                sa2_str = "ARRAY"+ str(sa2[0]["sid_array"])
                plpy.execute("INSERT INTO PGA_t VALUES("+ sa1_str+ ", "+ sa2_str+ ", '"+ str(new_MB)+ "');")

if(TD["event"] == "DELETE"):
        old_gid1 = TD["old"]["gid1"]
        old_gid2 = TD["old"]["gid2"]
        old_MB = TD["old"]["mb"]
        sa1 = plpy.execute("SELECT sid_array FROM PGA_group WHERE gid = "+ str(old_gid1))
        sa2 = plpy.execute("SELECT sid_array FROM PGA_group WHERE gid = "+ str(old_gid2))
        plpy.execute("DELETE FROM PGA_t WHERE sa1 = ARRAY"+ str(sa1[0]["sid_array"])+ " and sa2 = ARRAY"+ str(sa2[0]["sid_array"]))
if(TD["event"] == "UPDATE"):
        old_gid1 = TD["old"]["gid1"]
        old_gid2 = TD["old"]["gid2"]
        old_MB = TD["old"]["mb"]
        new_gid1 = TD["new"]["gid1"]
        new_gid2 = TD["new"]["gid2"]
        new_MB = TD["new"]["mb"]
        old_sa1 = plpy.execute("SELECT sid_array FROM PGA_group WHERE gid = "+ str(old_gid1))
        old_sa2 = plpy.execute("SELECT sid_array FROM PGA_group WHERE gid = "+ str(old_gid2))
        plpy.execute("DELETE FROM PGA_t WHERE sa1 = ARRAY"+ str(sa1[0]["sid_array"])+ " and sa2 = ARRAY"+ str(sa2[0]["sid_array"]))
        sa1 = plpy.execute("SELECT sid_array FROM PGA_group WHERE gid = "+ str(new_gid1))
        sa2 = plpy.execute("SELECT sid_array FROM PGA_group WHERE gid = "+ str(new_gid2))
        if(sa1.nrows()!=0 and sa2.nrows()!=0):
                sa1_str = "ARRAY"+ str(sa1[0]["sid_array"])
                sa2_str = "ARRAY"+ str(sa2[0]["sid_array"])
                plpy.execute("INSERT INTO PGA_t VALUES("+ sa1_str+ ", "+ sa2_str+ ", '"+ str(new_MB)+ "');")
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
        new_sa = TD["new"]["sid_array"]
        r_gid1 = plpy.execute("SELECT * FROM PGA_policy WHERE gid1 = "+ str(new_gid))
        if(r_gid1.nrows()!=0):
                r_other = plpy.execute("SELECT * FROM PGA_group WHERE gid = "+ str(r_gid1[0]["gid2"]))
                if(r_other.nrows()!= 0):
                        plpy.execute("INSERT INTO PGA_t VALUES(ARRAY"+ str(new_sa)+ ", ARRAY"+ str(r_other[0]["sid_array"])+ ", '"+ str(r_gid1[0]["mb"])+ "')")
        r_gid2 = plpy.execute("SELECT * FROM PGA_policy WHERE gid2 = "+ str(new_gid))
        if(r_gid2.nrows()!=0):
                r_other2 = plpy.execute("SELECT * FROM PGA_group WHERE gid = "+ str(r_gid2[0]["gid1"]))
                if(r_other2.nrows()!= 0):
                        plpy.execute("INSERT INTO PGA_t VALUES(ARRAY"+ str(r_other2[0]["sid_array"]) + ", ARRAY"+ str(new_sa)+ ", '"+ str(r_gid2[0]["mb"])+ "')")

if(TD["event"] == "DELETE"):
        old_gid = TD["old"]["gid"]
        old_sa = TD["old"]["sid_array"]
        plpy.execute("DELETE FROM PGA_t WHERE sa1 = ARRAY"+str(old_sa)+ "or sa2 = ARRAY"+ str(old_sa))

if(TD["event"] == "UPDATE"):
        new_gid = TD["new"]["gid"]
        new_sa = TD["new"]["sid_array"]
        old_gid = TD["old"]["gid"]
        old_sa = TD["old"]["sid_array"]
        r_gid1 = plpy.execute("SELECT * FROM PGA_policy WHERE gid1 = "+ str(new_gid))
        if(r_gid1.nrows()!=0):
                r_other = plpy.execute("SELECT * FROM PGA_group WHERE gid = "+ str(r_gid1[0]["gid2"]))
                if(r_other.nrows()!= 0):
                        plpy.execute("INSERT INTO PGA_t VALUES(ARRAY"+ str(new_sa)+ ", ARRAY"+ str(r_other[0]["sid_array"])+ ", '"+ str(r_gid1[0]["mb"])+ "')")
        r_gid2 = plpy.execute("SELECT * FROM PGA_policy WHERE gid2 = "+ str(new_gid))
        if(r_gid2.nrows()!=0):
                r_other2 = plpy.execute("SELECT * FROM PGA_group WHERE gid = "+ str(r_gid2[0]["gid1"]))
                if(r_other2.nrows()!= 0):
                        plpy.execute("INSERT INTO PGA_t VALUES(ARRAY"+ str(new_sa)+ ", ARRAY"+ str(r_other2[0]["sid_array"])+ ", '"+ str(r_gid2[0]["mb"])+ "')")
        plpy.execute("DELETE FROM PGA_t WHERE sa1 = ARRAY"+str(old_sa)+ "or sa2 = ARRAY"+ str(old_sa))

return None;
$$
LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;

CREATE TRIGGER t_group
        BEFORE INSERT OR DELETE OR UPDATE ON PGA_group
        FOR EACH ROW
EXECUTE PROCEDURE f_group();



CREATE OR REPLACE FUNCTION f_unnest()
RETURNS TRIGGER AS
$$
if(TD["event"] == "INSERT"):
        new_sa1q = TD["new"]["sa1"]
        new_sa2q = TD["new"]["sa2"]
        new_mbq = TD["new"]["mb"]
        for i in new_sa1q:
                for j in new_sa2q:
                        f = plpy.execute("SELECT * FROM PGA_table WHERE sid1 = "+ str(i)+ " and sid2 = "+ str(j) +" and mb='" + str(new_mbq)+"'")
                        if(f.nrows()!=0):
                                plpy.execute("UPDATE PGA_table SET n = n+1 WHERE sid1 = "+str(i) + " and sid2 = "+ str(j)+" and mb='" + str(new_mbq)+"'")
                        else:
                                plpy.execute("INSERT INTO PGA_table VALUES("+ str(i)+ ", "+ str(j)+", '"+ str(new_mbq) + "', 1)")

if(TD["event"] == "DELETE"):
        old_sa1q = TD["old"]["sa1"]
        old_sa2q = TD["old"]["sa2"]
        old_mbq = TD["old"]["mb"]
        for i in old_sa1q:
                for j in old_sa2q:
                        plpy.execute("UPDATE PGA_table SET n = n - 1 WHERE sid1 = "+str(i) + " and sid2 = "+ str(j)+" and mb='" + str(old_mbq)+"'")

        plpy.execute("DELETE FROM PGA_table WHERE n = 0")

if(TD["event"] == "UPDATE"):
        old_sa1q = TD["old"]["sa1"]
        old_sa2q = TD["old"]["sa2"]
        old_mbq = TD["old"]["mb"]
        for i in old_sa1q:
                for j in old_sa2q:
                        plpy.execute("UPDATE PGA_table SET n = n - 1 WHERE sid1 = "+str(i) + " and sid2 = "+ str(j)+" and mb='" + str(old_mbq)+"'")
        plpy.execute("DELETE FROM PGA_table WHERE n = 0")
        new_sa1q = TD["new"]["sa1"]
        new_sa2q = TD["new"]["sa2"]
        new_mbq = TD["new"]["mb"]
        for i in new_sa1q:
                for j in new_sa2q:
                        f = plpy.execute("SELECT * FROM PGA_table WHERE sid1 = "+ str(i)+ " and sid2 = "+ str(j)+" and mb='" + str(new_mbq)+"'")
                        if(f.nrows()!=0):
                                plpy.execute("UPDATE PGA_table SET n = n+1 WHERE sid1 = "+str(i) + " and sid2 = "+ str(j)+" and mb='" + str(new_mbq)+"'")
                        else:
                                plpy.execute("INSERT INTO PGA_table VALUES("+ str(i)+ ", "+ str(j)+", '"+ str(new_mbq) + "', 1)")



return None;
$$
LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;

CREATE TRIGGER t_unnest
        AFTER INSERT OR DELETE OR UPDATE ON PGA_t
        FOR EACH ROW
EXECUTE PROCEDURE f_unnest();

CREATE OR REPLACE VIEW PGA_violation AS (
       SELECT fid, MB
       FROM tm, PGA_table
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
INSERT INTO PGA_policy (gid1, gid2, MB)
VALUES (1,2,'FW'),
      (4,3,'LB');

INSERT INTO PGA_group 
       (gid, sid_array)
VALUES
	(1, ARRAY[5]),
	(2, ARRAY[6]),
	(3, ARRAY[6,7]),
	(4, ARRAY[5,8]);

-- (Kinetic) firewall configuration
INSERT INTO FW_policy_acl VALUES (8,7,0);
INSERT INTO FW_policy_user VALUES (6),(8);
