DROP TABLE IF EXISTS hop CASCADE;

DROP TABLE IF EXISTS link CASCADE;

DROP TABLE IF EXISTS sample CASCADE;


CREATE TABLE sample(x, y) AS 
	SELECT sid, nid
	FROM tp
;

CREATE VIEW sample_hop(x,z) AS
	SELECT x,z
	FROM sample as sample1(x, y), sample as sample2(y,z)
	WHERE sample1.y = sample2.y
;


CREATE TABLE link(x, y) AS 
	SELECT sid, nid
	FROM tp
;
CREATE INDEX link_x_idx ON link(x);
        
CREATE VIEW hop_view AS
        SELECT  x, z 
        FROM    link as link1(x, y), link as link2(y,z)
        WHERE   link1.y = link2.y
;


CREATE TABLE hop AS
SELECT x, z, count(*)
FROM hop_view
GROUP BY x, z;
CREATE INDEX hop_sid_idx ON hop(x);

CREATE OR REPLACE FUNCTION d_1()
RETURNS TRIGGER AS
$$
import time

logfile = '/tmp/log.txt'
f = open(logfile, 'a')
log = "rule1: \n"
if(TD["event"] == "INSERT"):
	log+= "insert (" + str(TD["new"]["x"])+ "," + str(TD["new"]["y"]) +")\n"
        t1 = time.time()
	delta_p = plpy.execute("SELECT x, y FROM link")
        def comma_join(x) :
                if x["x"] == TD["new"]["y"]:
                        return {"x" : TD["new"]["x"], "z" : x["y"]}
                else:
                        return None
        delta_p = list(filter(lambda x: x != None,map(comma_join,delta_p)))
	t2 = time.time()
	log += "rule 1-----calculating delta_p-----\n" + str((t2-t1)*1000) + "\n"

        t3 = time.time()
	for each in delta_p:
                p_table = plpy.execute("SELECT * FROM hop;")
                flag = 0
                for p in p_table:
                        if(each["x"] == p["x"] and each["z"] == p["z"]):
                                plpy.execute("UPDATE hop SET count = count+ 1 WHERE x = "+ str(each["x"])+ " AND z="+ str(each["z"])+";")
                                flag = 1
                if(flag ==0):
                        plpy.execute("INSERT INTO hop VALUES ("+ str(each["x"])+ ", "+ str(each["z"])+ ", 1);")
	t4 = time.time()
	log += "rule 1-----updating hop table------\n" + str((t4-t3)*1000) + "\n"

if(TD["event"] == "DELETE"):
	log+= "delete (" + str(TD["old"]["x"])+ "," + str(TD["old"]["y"]) +")\n"
	t1 = time.time()
        delta_p = plpy.execute("SELECT x, y FROM link")
        def comma_join(x) :
                if x["x"] == TD["old"]["y"]:
                        return {"x" : TD["old"]["x"], "z" : x["y"]}
                else:
                        return None
        delta_p = list(filter(lambda x: x != None,map(comma_join,delta_p)))
	t2 = time.time()
        log += "rule 1-----calculating delta_p-----\n" + str((t2-t1)*1000) + "\n"
	
	t3 = time.time()
        for each in delta_p:
                p_table = plpy.execute("SELECT * FROM hop;")
                flag = 0
                for p in p_table:
                        if(each["x"] == p["x"] and each["z"] == p["z"] and not(p["count"]==1)):
                                plpy.execute("UPDATE hop SET count = count - 1 WHERE x = "+ str(each["x"])+ " AND z="+ str(each["z"])+";")
                                flag = 1
                        elif(each["x"] == p["x"] and each["z"] == p["z"] and p["count"]==1):
                                plpy.execute("DELETE FROM hop WHERE x = "+ str(each["x"])+ " AND z="+ str(each["z"])+";")
                                flag = 1
                if(flag == 0):
                        plpy.execute("INSERT INTO hop VALUES ("+ str(each["x"])+ ", "+ str(each["z"])+ ", 1);")
	t4 = time.time()
        log += "rule 1-----updating hop table------\n" + str((t4-t3)*1000) + "\n"

f.write(log)
f.flush()
f.close()
return None;
$$
LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;

-- d2: delta_p :- s_v(x,y) & delta_s(y,z)
CREATE OR REPLACE FUNCTION d_2()
RETURNS TRIGGER AS
$$
import time

logfile = '/tmp/log.txt'
f = open(logfile, 'a')
log = "rule2: \n"
if(TD["event"] == "INSERT"):
	log+= "insert (" + str(TD["new"]["x"])+ "," +str(TD["new"]["y"]) +")\n"
	t1 = time.time()
        delta_p = plpy.execute("SELECT x, y FROM link")
        def comma_join(x) :
                if x["y"] == TD["new"]["x"]:
                        return {"x" : x["x"], "z" : TD["new"]["y"]}
                else:
                        return None
        delta_p = list(filter(lambda x: x != None,map(comma_join,delta_p)))
	t2 = time.time()
	log += "rule 2-----calculating delta_p-----\n" + str((t2-t1)*1000) + "\n"

	t3 = time.time()
        for each in delta_p:
                p_table = plpy.execute("SELECT * FROM hop;")
                flag =0
                for p in p_table:
                        if(each["x"] == p["x"] and each["z"] == p["z"]):
                                plpy.execute("UPDATE hop SET count = count+ 1 WHERE x = "+ str(each["x"])+ " AND z="+ str(each["z"])+";")
                                flag = 1
                if(flag ==0):
                        plpy.execute("INSERT INTO hop VALUES ("+ str(each["x"])+ ", "+ str(each["z"])+ ", 1);")

	t4 = time.time()
	log += "rule 2-----updating hop table------\n" + str((t4-t3)*1000) + "\n"
if(TD["event"] == "DELETE"):
	log+= "delete (" + str(TD["old"]["x"])+ "," + str(TD["old"]["y"]) +")\n"
	t1 = time.time()
        delta_p = plpy.execute("SELECT x, y FROM link")
        def comma_join(x) :
                if x["y"] == TD["old"]["x"]:
                        return {"x" : x["x"], "z" : TD["old"]["y"]}
                else:
                        return None
        delta_p = list(filter(lambda x: x != None,map(comma_join,delta_p)))
	t2 = time.time()
	log += "rule 2-----calculating delta_p-----\n" + str((t2-t1)*1000) + "\n"

	t3 = time.time()
        for each in delta_p:
                p_table = plpy.execute("SELECT * FROM hop;")
                flag = 0;
                for p in p_table:
                        if(each["x"] == p["x"] and each["z"] == p["z"] and not(p["count"]==1)):
                                plpy.execute("UPDATE hop SET count = count - 1 WHERE x = "+ str(each["x"])+ " AND z="+ str(each["z"])+";")
                                flag = 1
                        elif(each["x"] == p["x"] and each["z"] == p["z"] and p["count"]==1):
                                plpy.execute("DELETE FROM hop WHERE x = "+ str(each["x"])+ " AND z="+ str(each["z"])+";")
                                flag = 1
                if(flag ==0):
                        plpy.execute("INSERT INTO hop VALUES ("+ str(each["x"])+ ", "+ str(each["z"])+ ", 1);")

	t4 = time.time()
	log += "rule 2-----updating hop table------\n" + str((t4-t3)*1000) + "\n"

f.write(log)
f.flush()
f.close()
return None;
$$
LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;


CREATE TRIGGER t_1
        BEFORE DELETE OR INSERT ON link
        FOR EACH ROW
EXECUTE PROCEDURE d_1();



CREATE TRIGGER t_2
        AFTER DELETE OR INSERT ON link
        FOR EACH ROW
EXECUTE PROCEDURE d_2();



