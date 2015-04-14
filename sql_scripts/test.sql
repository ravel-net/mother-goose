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
