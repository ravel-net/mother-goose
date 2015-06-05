DROP TABLE IF EXISTS tenant_hosts CASCADE;
CREATE UNLOGGED TABLE tenant_hosts (
       hid	integer,
       PRIMARY key (hid)
);

DROP VIEW IF EXISTS tenant_policy CASCADE;
CREATE OR REPLACE VIEW tenant_policy AS (
       SELECT DISTINCT fid, host1, host2 FROM utm
       WHERE host1 IN (SELECT * FROM tenant_hosts)
       	     AND host2 IN (SELECT * FROM tenant_hosts)
);

CREATE OR REPLACE FUNCTION tenant_policy_ins_fun() RETURNS TRIGGER AS
$$
plpy.notice ("tenant_policy_ins_fun")

h1 = TD["new"]["host1"]
h2 = TD["new"]["host2"]
fid = TD["new"]["fid"]

hs = plpy.execute ("SELECT hid FROM tenant_hosts;")
hosts = [h['hid'] for h in hs]

if (h1 in hosts) & (h2 in hosts):
    plpy.execute ("INSERT INTO utm values (" + str (fid)  + "," +str (h1)+ "," + str (h2) + ");")

return None;
$$
LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;

-- fid = int (plpy.execute ("select max(fid) +1 as c from utm")[0]['c']) 

CREATE TRIGGER tenant_policy_ins_trigger
     INSTEAD OF INSERT ON tenant_policy
     FOR EACH ROW
   EXECUTE PROCEDURE tenant_policy_ins_fun();

CREATE OR REPLACE RULE tenant_policy_del AS
       ON DELETE TO tenant_policy
       DO INSTEAD
       DELETE FROM utm WHERE fid = OLD.fid;

-- CREATE OR REPLACE RULE tenant_policy_update AS
--        ON UPDATE TO tenant_policy
--        DO INSTEAD (
--        DELETE FROM tenant_policy WHERE fid = OLD.fid;
--        INSERT INTO tenant_policy VALUES (NEW.fid, NEW.host1, NEW.host2);
--        );

CREATE OR REPLACE FUNCTION tenant_policy_up_fun() RETURNS TRIGGER AS
$$
plpy.notice ("tenant_policy_update_fun")

h1 = TD["new"]["host1"]
h2 = TD["new"]["host2"]
fid = TD["new"]["fid"]

plpy.execute ("DELETE FROM tenant_policy WHERE fid = "+str (fid)+";") 
plpy.execute ("INSERT INTO tenant_policy VALUES ("+str (fid)+","+str (h1)+", "+ str (h2)+");")  

return None;
$$
LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;

CREATE TRIGGER tenant_policy_up_trigger
     INSTEAD OF UPDATE ON tenant_policy
     FOR EACH ROW
   EXECUTE PROCEDURE tenant_policy_up_fun();


------------------------------------------------------------------
------------------------------------------------------------------
-- acl on tenant_policy

DROP TABLE IF EXISTS tacl_tb CASCADE;
CREATE UNLOGGED TABLE tacl_tb (
       end1	      integer,
       end2 	      integer,
       inBlklist      integer
);

CREATE OR REPLACE VIEW tacl AS (
       SELECT DISTINCT end1, end2, inBlklist, 1 as isViolated
       FROM tacl_tb, tenant_policy
       WHERE tacl_tb.end1 = tenant_policy.host1 and tacl_tb.end2 = tenant_policy.host2 and inBlklist = 1);

CREATE OR REPLACE RULE tacl2tenant_policy AS
       ON UPDATE TO tacl
       DO INSTEAD
       	  DELETE FROM tenant_policy WHERE host1 = NEW.end1 AND host2 = NEW.end2;

------------------------------------------------------------------
------------------------------------------------------------------
--  lb on tenant_policy

DROP TABLE IF EXISTS tlb_tb CASCADE;
CREATE UNLOGGED TABLE tlb_tb (
       sid	integer
);

-- CREATE OR REPLACE VIEW tlb2 AS(
--        SELECT sid, count (*) AS load 
--        FROM tlb_tb, tenant_policy
--        WHERE tlb_tb.sid = tenant_policy.host2
--        GROUP BY sid
--        );

CREATE OR REPLACE VIEW tlb AS (
       SELECT sid,
       	      (SELECT count(*) FROM tenant_policy
	       WHERE host2 = sid) AS load
       FROM tlb_tb
);

CREATE OR REPLACE RULE tlb2tenant_policy AS
       ON UPDATE TO tlb
       DO INSTEAD 
          UPDATE tenant_policy
          SET host2 =
	      (SELECT sid FROM tlb
	       WHERE load = (SELECT min (load) FROM tlb LIMIT (OLD.load - NEW.load))
	       LIMIT 1)
              WHERE fid IN (SELECT fid FROM tenant_policy WHERE host2 = NEW.sid
		              LIMIT (OLD.load - NEW.load));

-- CREATE OR REPLACE RULE tlb2tenant_policy AS
--        ON UPDATE TO tlb
--        DO INSTEAD 
--           UPDATE tenant_policy
--           SET host2 =
-- 	      (SELECT sid FROM tlb
-- 	       WHERE load = (SELECT min (load) FROM tlb LIMIT (OLD.load - NEW.load))
-- 	       LIMIT 1)
--               WHERE host1 IN (SELECT host1 FROM tenant_policy WHERE host2 = NEW.sid
-- 		              LIMIT (OLD.load - NEW.load))
-- 	            AND host2 = NEW.sid ;

----------------------------------------------------------------------
-- tenant orchestration
----------------------------------------------------------------------

DROP TABLE IF EXISTS t1 CASCADE;
CREATE UNLOGGED TABLE t1 (
       counts  	integer,
       status 	text,
       PRIMARY key (counts)
);

DROP TABLE IF EXISTS t2 CASCADE;
CREATE UNLOGGED TABLE t2 (
       counts  	integer,
       status 	text,
       PRIMARY key (counts)
);

DROP TABLE IF EXISTS t3 CASCADE;
CREATE UNLOGGED TABLE t3 (
       counts  	integer,
       status 	text,
       PRIMARY key (counts)
);

CREATE OR REPLACE RULE tlb_constraint AS
       ON INSERT TO t1
       WHERE (NEW.status = 'on')
       DO ALSO (
           UPDATE tlb SET load = 1 WHERE load > 1;
	   UPDATE t1 SET status = 'off' WHERE counts = NEW.counts;
	  );

CREATE OR REPLACE RULE t12 AS
       ON UPDATE TO t1
       WHERE (NEW.status = 'off')
       DO ALSO
           INSERT INTO t2 values (NEW.counts, 'on');

CREATE OR REPLACE RULE tacl_constraint AS
       ON INSERT TO t2
       WHERE (NEW.status = 'on')
       DO ALSO (
           UPDATE tacl SET isviolated = 0 WHERE isviolated = 1;
	   UPDATE t2 SET status = 'off' WHERE counts = NEW.counts;
	  );

CREATE OR REPLACE RULE t23 AS
       ON UPDATE TO t2
       WHERE (NEW.status = 'off')
       DO ALSO
           INSERT INTO t3 values (NEW.counts, 'on');

CREATE TRIGGER trt_constraint_trigger
     AFTER INSERT ON t3
     FOR EACH ROW
   EXECUTE PROCEDURE spv_constraint1_fun();

CREATE OR REPLACE RULE rt_constraint AS
       ON INSERT TO t3
       WHERE (NEW.status = 'on')
       DO ALSO (
	   UPDATE t3 SET status = 'off' WHERE counts = NEW.counts;
	  );

CREATE OR REPLACE RULE t3c AS
       ON UPDATE TO t3
       WHERE (NEW.status = 'off')
       DO ALSO
           INSERT INTO clock values (NEW.counts);
