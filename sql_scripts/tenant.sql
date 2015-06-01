DROP TABLE IF EXISTS tenant_hosts CASCADE;
CREATE UNLOGGED TABLE tenant_hosts (
       hid	integer,
       PRIMARY key (hid)
);

DROP VIEW IF EXISTS tenant_policy CASCADE;
CREATE OR REPLACE VIEW tenant_policy AS (
       SELECT DISTINCT fid, host1, host2 FROM rtm
       WHERE host1 IN (SELECT * FROM tenant_hosts)
       	     AND host2 IN (SELECT * FROM tenant_hosts)
);

CREATE OR REPLACE FUNCTION tenant_policy_ins_fun() RETURNS TRIGGER AS
$$
plpy.notice ("tenant_policy_ins_fun")

h1 = TD["new"]["host1"]
h2 = TD["new"]["host2"]

hs = plpy.execute ("SELECT hid FROM tenant_hosts;")
hosts = [h['hid'] for h in hs]

fid = int (plpy.execute ("select max(fid) +1 as c from rtm")[0]['c']) 

if (h1 in hosts) & (h2 in hosts):
    plpy.execute ("INSERT INTO rtm values (" + str (fid)  + "," +str (h1)+ "," + str (h2) + ");")

return None;
$$
LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;

CREATE TRIGGER tenant_policy_ins_trigger
     INSTEAD OF INSERT ON tenant_policy
     FOR EACH ROW
   EXECUTE PROCEDURE tenant_policy_ins_fun();

CREATE OR REPLACE RULE tenant_policy_del AS
       ON DELETE TO tenant_policy
       DO INSTEAD
       DELETE FROM rtm WHERE fid = OLD.fid;

CREATE OR REPLACE RULE tenant_policy_update AS
       ON UPDATE TO tenant_policy
       DO INSTEAD (
       INSERT INTO tenant_policy VALUES (NEW.fid, NEW.host1, NEW.host2);
       DELETE FROM tenant_policy WHERE fid = OLD.fid;	
       );
       

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
