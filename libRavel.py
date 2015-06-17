def add_cf2flows (dbname, username):
    conn = psycopg2.connect(database= dbname, user= username)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
    cur = conn.cursor()

    add_flow = """
CREATE OR REPLACE FUNCTION add_flow_fun ()
RETURNS TRIGGER
AS $$
plpy.notice ("hello, add_flow_fun")
f = TD["new"]["pid"]
s = TD["new"]["sid"]
n = TD["new"]["nid"]

u = plpy.execute('select port from get_port (' +str (s)+') where nid = ' +str (n))
outport = str(u[0]['port'])
plpy.notice (str (u))
v = plpy.execute('select port from get_port (' +str (s)+') where nid = ' +str (f))
inport = str (v[0]['port'])
plpy.notice (str (v))

cmd1 = '/usr/bin/sudo /usr/bin/ovs-ofctl add-flow s' + str (s) + ' in_port=' + inport + ',actions=output:' + outport
cmd2 = '/usr/bin/sudo /usr/bin/ovs-ofctl add-flow s' + str (s) + ' in_port=' + outport + ',actions=output:' + inport

import os
import sys

x1 = os.system (cmd1)
plpy.notice (cmd1)

x2 = os.system (cmd2)
plpy.notice (cmd2)

return None;
$$ LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;"""

    del_flow = """
CREATE OR REPLACE FUNCTION del_flow_fun ()
RETURNS TRIGGER
AS $$
plpy.notice ("invoke del_flow_fun")

f = TD["old"]["pid"]
s = TD["old"]["sid"]
n = TD["old"]["nid"]

u = plpy.execute('select port from get_port (' +str (s)+') where nid = ' +str (n))
outport = str(u[0]['port'])

v = plpy.execute('select port from get_port (' +str (s)+') where nid = ' +str (f))
inport = str (v[0]['port'])

cmd1 = '/usr/bin/sudo /usr/bin/ovs-ofctl del-flows s' + str (s) + ' in_port=' + inport
cmd2 = '/usr/bin/sudo /usr/bin/ovs-ofctl del-flows s' + str (s) + ' in_port=' + outport

import os
import sys
import time

x1 = os.system (cmd1)
plpy.notice (str (x1))
x1 = os.system (cmd2)
plpy.notice (str (x1))

return None;
$$ LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;

"""
    cur.execute (add_flow)
    cur.execute (del_flow)
    print "--------------------> add cf2flow entries functions successful"
    

def select_dbname ():
    global monitor_mininet
    global switch_size
    global fanout_size
    global k_size

    while True:
        n = raw_input ('select topology type : \n \t\'t,\'y\'/\'n\'\'(toy w/o mininet monitor) \n \t\'i,/y/n\'(isp w/o mininet monitor) \n\t\'m,\'y\'/\'n\'\'(mininet) \n\t\'tree\',switch_size,fanout_size,\'y\'/\'n\' (tree w/o mininet monitor) \n\t\'f\',k_size (fat tree with k)\n')
        if n.strip ().split (',')[0] == 't':
            monitor_mininet = n.strip ().split (',')[1]
            return 'toy'
            break
        elif n.strip ().split (',')[0] == 'i':
            monitor_mininet = n.strip ().split (',')[1]
            return 'isp'
            break
        elif n.strip ().split (',')[0] == 'm':
            return 'mininet'
            break
        elif n.strip ().split (',')[0] == 'tree':
            switch_size = int (n.strip ().split (',')[1]) 
            fanout_size = int (n.strip ().split (',')[2])
            monitor_mininet = n.strip ().split (',')[3]
            return 'tree'
            break
        elif n.strip ().split (',')[0] == 'f':
            k_size = int (n.strip ().split (',')[1])
            return 'fattree' + n.strip ().split (',')[1]
            break
        else:
            print 'wrong topology type'


def create_mininet_topo (dbname, username):
    try:
        conn = psycopg2.connect(database= dbname, user= username)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cur.execute ("SELECT * FROM switches;")
        cs = cur.fetchall ()
        switches = [s['sid'] for s in cs]

        # cur.execute ("SELECT * FROM hosts;")
        # cs = cur.fetchall ()
        # hosts = [h['hid'] for h in cs]

        cur.execute ("SELECT * FROM tp;")
        cs = cur.fetchall ()
        links = [[l['sid'],l['nid']] for l in cs]

        cur.execute ("SELECT * FROM uhosts;")
        cs = cur.fetchall ()
        hids = [h['hid'] for h in cs]
        u_hids = [h['u_hid'] for h in cs]
        host_dict = dict (zip (hids, u_hids))

    except psycopg2.DatabaseError, e:
        print 'Error %s' % e    
    finally:
        if conn: conn.close()

    def nid_name (nid, s, h):
        if nid in s:
            outid = 's' + str (nid)
        elif nid in h.keys ():
            outid = 'h' + str (h[nid])
        else:
            print "nid_name wrong"
        return outid

    timestamp = str (datetime.datetime.now ()) .replace(" ", "-").replace (":","-").replace (".","-")
    # timestamp = ""
    filename = os.getcwd () + '/topo/'+ dbname + '_dtp.py'
    fo = open(filename, "w")
    fo.write ('"""' + timestamp)
    fo.write ('\n$ sudo mn --custom '+ filename + ' --topo mytopo --test pingall')
    fo.write ('\n$ sudo mn --custom '+ filename + ' --topo mytopo --mac --switch ovsk --controller remote\n')
    fo.write ('"""')

    fo.write ('\n')
    fo.write ("""
from mininet.topo import Topo

class MyTopo( Topo ):
    "Simple topology example."

    def __init__( self ):
        "Create custom topo."

        # Initialize topology
        Topo.__init__( self )
    """)

    for hid in host_dict.keys ():
        h = 'h' + str (host_dict [hid])
        fo.write ("""
        """ + h + """ = self.addHost('""" + h + """')""")
    fo.write ('\n')

    for sid in switches:
        s = 's' + str (sid)
        fo.write ("""
        """ + s + """ = self.addSwitch('""" + s + """')""")
    fo.write ('\n')
        
    for [nid1, nid2] in links:
        nname1 = nid_name (nid1, switches, host_dict)
        nname2 = nid_name (nid2, switches, host_dict)
        fo.write ("""
        self.addLink(""" + nname1 + "," + nname2+ """)""")

    fo.write ("""\n
topos = { 'mytopo': ( lambda: MyTopo() ) }
    """)
    fo.write ('\n')
    fo.close ()
    print "--------------------> create_mininet_topo successful"

def truncate_db (dbname):
    try:
        conn = psycopg2.connect(database= dbname, user= "mininet")
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        cur = conn.cursor()


        cur.execute ("truncate cf, clock, p1, p2, p3, p_spv, pox_hosts, pox_switches, pox_tp, rtm, rtm_clock, spatial_ref_sys, spv_tb_del, spv_tb_ins, tm, tm_delta, utm, acl_tb, lb_tb;")

        cur.execute ("INSERT INTO clock values (0);")

        cur.execute ("truncate t1, t2, t3, tacl_tb, tenant_hosts, tlb_tb;")

        print "--------------------> truncate_db successful"

    except psycopg2.DatabaseError, e:
        print "clean_db error"
        print 'Error %s' % e    

    finally:
        if conn: conn.close()

def clean_db (dbname):
    try:
        conn = psycopg2.connect(database= "postgres", user= "mininet")
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        cur = conn.cursor()

        cur.execute ("drop database " + dbname)
        print "--------------------> clean_db successful"

    except psycopg2.DatabaseError, e:
        print "clean_db error"
        print 'Error %s' % e    

    finally:
        if conn: conn.close()

def create_db (dbname):
    global database_exists

    try:
        conn = psycopg2.connect(database= 'postgres', user= 'mininet')
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        cur = conn.cursor()

        cur.execute ("SELECT datname FROM pg_database WHERE datistemplate = false;")
        c = cur.fetchall ()
        dblist = [c[i][0] for i in range (len (c))]
        if dbname not in dblist:
            cur.execute ("CREATE DATABASE " + dbname + ";")
            database_exists = 0
        else:
            print "database " + dbname + " exists, skip"
            database_exists = 1

        print "--------------------> create_db successful"
    except psycopg2.DatabaseError, e:
        print "create_db: unable to connect to database postgres, as user " + 'mininet'
        print 'Error %s' % e

    finally:
        if conn:
            conn.close()

def add_pgrouting_plpy_plsh_extension (dbname, username):

    try:
        conn = psycopg2.connect(database= dbname, user= username)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        cur = conn.cursor()

        cur.execute ("SELECT 1 FROM pg_catalog.pg_namespace n JOIN pg_catalog.pg_proc p ON pronamespace = n.oid WHERE proname = 'pgr_dijkstra';")
        c = cur.fetchall ()
        if c == []:
            cur.execute ("CREATE EXTENSION IF NOT EXISTS plpythonu;")
            cur.execute ("CREATE EXTENSION IF NOT EXISTS postgis;")
            cur.execute ("CREATE EXTENSION IF NOT EXISTS pgrouting;")
            cur.execute ("CREATE EXTENSION plsh;")

        print "--------------------> add_pgrouting_plpy_plsh_extension successful"
    except psycopg2.DatabaseError, e:
        print 'Error %s' % e
    finally:
        if conn: conn.close()

def init_database (dbname, username):
    # print monitor_mininet, "before"
    def print_mn_manual (dbname):
        # print message, exit loop after user inputs 'y'
        filename = os.getcwd () + '/topo/'+ dbname + '_dtp.py'
        while True:
            cmd = 'please run (press y to not repeat the message)\n' + 'sudo mn --custom '+ filename + ' --topo mytopo --mac --switch ovsk --controller remote\n'
            n = raw_input(cmd)
            if n.strip () == 'y':
                break

    if dbname == 'toy' or dbname == 't':
        # load_topo3switch ('toy', username)
        load_topo4switch ('toy', username)
    elif dbname[0:3] == 'isp' or dbname == 'i':
        load_ISP_topo_fewer_hosts ('isp', username)
    elif dbname == 'mininet' or dbname == 'm':
        load_topo3switch_new ('mininet', username)
    elif dbname == 'tree':
        load_tree (switch_size, fanout_size, dbname, username)
    elif dbname[0:7] == 'fattree':
        init_fattree (k_size, dbname, username)

    create_mininet_topo (dbname, username)

    if monitor_mininet == 'y':
        print_mn_manual (dbname)
        load_pox_module (dbname, username)

    print "--------------------> init_database successful"

def igraph_fattree (k):
    core_size = (k/2)**2
    agg_size = (k/2) *k
    eg_size = (k/2) *k
    host_size = (k/2)**2 *k

    # g = Graph(directed = True)    
    g = Graph()    

    g.add_vertices (core_size + agg_size + eg_size + host_size)
    g.vs['type'] = ['core'] * core_size + ['agg'] * agg_size + ['edge'] * eg_size + ['host'] * host_size

    for pod in range (0,k):
        agg_offset = core_size + k/2 * pod
        eg_offset = core_size + agg_size + k/2*pod
        host_offset = core_size + agg_size + eg_size + (k/2)**2 * pod

        for agg in range (0, k/2):
            core_offset = agg * k/2

            for core in range (0, k/2):
                g.add_edge (agg_offset + agg, core_offset + core)
                # connect core and aggregate routers

            for eg in range (0, k/2):
                g.add_edge (agg_offset + agg, eg_offset + eg)
                # connect aggregate and edge routers

        for eg in range (0, k/2):
            for h in range (0, k/2):
                g.add_edge (eg_offset + eg, host_offset + k/2*eg + h)
                # connect edge routers and hosts
    return g

def init_fattree (k, dbname, username):
    conn = psycopg2.connect(database= dbname, user= username)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
    cur = conn.cursor()

    g = igraph_fattree (k)
    edges = g.get_edgelist ()

    global switch_size
    switch_size = (k/2)**2 + (k/2) *k + (k/2) *k

    for i in range (switch_size):
        cur.execute ("insert into switches (sid) values (" +str (i) +")")

    for i in range (switch_size, switch_size + (k/2)**2 *k):
        cur.execute ("insert into hosts (hid) values (" + str (i) + ")")
        # cur.execute ("insert into tp (sid, nid, ishost,isactive) values (" + str (i) +','+ str (i+switch_size) + ", 1,1)")

    for e in edges:
        if e[1] < switch_size:
            cur.execute ('insert into tp (sid, nid, ishost, isactive) values (' + str (e[0]) + ',' + str (e[1]) + ',0,1);' )
        else:
            cur.execute ('insert into tp (sid, nid, ishost, isactive) values (' + str (e[0]) + ',' + str (e[1]) + ',1,1);' )

    conn.close ()
    print "--------------------> init_fattree successful"
    
def load_tree (switch_size, fanout_size, dbname, username):
    g = Graph.Tree(switch_size, fanout_size)
    edges = g.get_edgelist ()

    conn = psycopg2.connect(database= dbname, user= username)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
    cur = conn.cursor()

    for i in range (switch_size):
        cur.execute ("insert into switches (sid) values (" +str (i) +")")

        if g.degree (i) == 1:
            cur.execute ("insert into hosts (hid) values (" + str (i + switch_size) + ")")
            cur.execute ("insert into tp (sid, nid, ishost,isactive) values (" + str (i) +','+ str (i+switch_size) + ", 1,1)")

    for e in edges:
        cur.execute ('insert into tp (sid, nid, ishost, isactive) values (' + str (e[0]) + ',' + str (e[1]) + ',0,1);' )

    conn.close ()
    print "--------------------> load_tree successful"


def load_ISP_topo_fewer_hosts (dbname, username):
    def init_topology (cursor):
        ISP_edges_file = os.getcwd () + '/ISP_topo/4755_edges.txt'
        ISP_nodes_file = os.getcwd () + '/ISP_topo/4755_nodes.txt'

        f = open (ISP_edges_file, "r").readlines ()# [:10]

        for edge in f:
            ed = edge[:-1].split()
            try:
                cursor.execute("""INSERT INTO tp(sid, nid, isactive) VALUES (%s, %s,1);""", (int(ed[0]), int(ed[1])))
            except psycopg2.DatabaseError, e:
                print "Unable to insert into topology table: %s" % str(e)

        f = open (ISP_nodes_file, "r").readlines ()
        for node in f:
            nd = node[:-1]
            try:
                cursor.execute ("""INSERT INTO switches VALUES (%s);""", ([int (nd)]))
            except psycopg2.DatabaseError, e:
                print "Unable to insert into switches table: %s" % str(e)

        f = ['60\n','34\n','112\n','141\n','193\n','238\n','28\n','89\n','91\n','253\n','472\n']
        for node in f:
            nd = node[:-1]
            try:
                cursor.execute ("""INSERT INTO hosts VALUES (%s);""", ([int (nd)+1000]))
                cursor.execute ("""INSERT INTO tp(sid, nid, isactive) VALUES (%s, %s,1);""",(int(nd)+1000,int(nd)))
            except psycopg2.DatabaseError, e:
                print "Unable to insert into hosts table: %s" % str(e)
        print "Initialize topology table with edges in " + ISP_edges_file

    try:
        conn = psycopg2.connect(database= dbname, user= username)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        cur = conn.cursor()
        init_topology (cur)

        print "--------------------> load_ISP_topo_fewer_hosts successful"

    except psycopg2.DatabaseError, e:
        print "Unable to connect to database " + dbname + ", as user " + username
        print 'Error %s' % e    

    finally:
        if conn: conn.close()    

def load_topo3switch_new (dbname, username):
    try:
        conn = psycopg2.connect(database= dbname, user= username)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        cur = conn.cursor()
        cur.execute ("""
        TRUNCATE TABLE tp cascade;
        TRUNCATE TABLE cf cascade;
        TRUNCATE TABLE tm cascade;
        INSERT INTO switches(sid) VALUES (1),(2),(3);
        INSERT INTO hosts(hid) VALUES (4),(5),(6);
        INSERT INTO tp(sid, nid, ishost, isactive) VALUES (1,4,1,1), (2,5,1,1), (3,6,1,1);
        INSERT INTO tp(sid, nid, ishost, isactive) VALUES (1,2,0,1), (2,3,0,1), (3,1,0,1);
""")
        print "--------------------> load_topo3switch successful"
    except psycopg2.DatabaseError, e:
        print "Unable to connect to database " + dbname + ", as user " + username
        print 'Error %s' % e

    finally:
        if conn: conn.close()

def load_topo4switch (dbname, username):
    conn = psycopg2.connect(database= dbname, user= username)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
    cur = conn.cursor()
    cur.execute ("""
        TRUNCATE TABLE tp cascade;
        TRUNCATE TABLE cf cascade;
        TRUNCATE TABLE tm cascade;
        INSERT INTO switches(sid) VALUES (1),(2),(3),(4);
        INSERT INTO hosts(hid) VALUES (5),(6),(7),(8);
        INSERT INTO tp(sid, nid, ishost, isactive) VALUES (1,5,1,1), (2,6,1,1), (3,7,1,1), (4,8,1,1);
        INSERT INTO tp(sid, nid, ishost, isactive) VALUES (1,2,0,1), (2,3,0,1), (3,4,0,1),(4,1,0,1);
""")
    print "--------------------> load_topo4switch successful"
    if conn: conn.close()


def load_schema (dbname, username, sql_script):
    try:
        conn = psycopg2.connect(database= dbname, user= username)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        dbscript  = open (sql_script,'r').read()
        cur.execute(dbscript)

        print "--------------------> load_schema successful " + sql_script
    except psycopg2.DatabaseError, e:
        print 'Error %s' % e
    finally:
        if conn: conn.close()

def batch_test (dbname, username, rounds, default):
    global logdest

    # if dbname[0:7] == 'fattree':
    logdestfile = dbname + '_' + str (rounds)
    logdest = os.getcwd () + '/data/' + logdestfile + '.log'


    conn = psycopg2.connect(database= dbname, user= username)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute ("SELECT u_hid FROM uhosts;")
    cs = cur.fetchall ()
    uhosts = [h['u_hid'] for h in cs]

    cur.execute ("SELECT * FROM hosts;")
    cs = cur.fetchall ()
    hosts = [h['hid'] for h in cs]

    cur.execute ("SELECT * FROM switches;")
    cs = cur.fetchall ()
    switches = [h['sid'] for h in cs]

    cur.execute ("SELECT sid,nid FROM tp where ishost = 0;")
    cs = cur.fetchall ()
    links = [[h['sid'], h['nid']] for h in cs]

    logfile = os.getcwd ()+'/log.txt'

    open(logfile, 'w').close()
    f = open(logfile, 'a')


    def init_tacl (cur=cur):
        cur.execute ("select distinct host1, host2 from tenant_policy ;")
        cs = cur.fetchall ()
        ends = [[h['host1'], h['host2']] for h in cs]
        
        foo = [0, 1]
        for i in range (len (ends)):
            [e1, e2] = ends[i]
            is_inblacklist = random.choice(foo)
            cur.execute ("INSERT INTO tacl_tb VALUES ("+ str (e1)+ ","+ str (e2) + "," + str (is_inblacklist) +");") 

    def init_tlb (cur=cur):
        cur.execute ("select distinct host2 from tenant_policy ;")
        cs = cur.fetchall ()
        ends = [h['host2'] for h in cs]
        print ends
        
        for e in ends:
            cur.execute ("INSERT INTO tlb_tb VALUES ("+ str (e)+ ");")

    def init_acl (cur=cur):
        cur.execute ("select distinct host1, host2 from utm ;")
        cs = cur.fetchall ()
        ends = [[h['host1'], h['host2']] for h in cs]
        
        foo = [0, 1]
        for i in range (len (ends)):
            [e1, e2] = ends[i]
            is_inblacklist = random.choice(foo)
            cur.execute ("INSERT INTO acl_tb VALUES ("+ str (e1)+ ","+ str (e2) + "," + str (is_inblacklist) +");") 

    def init_lb (cur=cur):
        cur.execute ("select distinct host2 from utm ;")
        cs = cur.fetchall ()
        ends = [h['host2'] for h in cs]
        
        for i in range (len (ends)):
            e = ends[i]
            cur.execute ("INSERT INTO lb_tb VALUES ("+ str (e)+ ");")

    def op_tlb (cur=cur, f=f):
        t1 = time.time ()
        cur.execute ("select * from tlb order by load DESC limit 1;")
        t2 = time.time ()
        f.write ('----lb*tenant: check max load----' + str ((t2-t1)*1000) + '\n')
        f.flush ()
        max_load = cur.fetchall ()[0]['load']

        cur.execute ("select sid from tlb where load = "+str (max_load)+" limit 1;")
        s_id = cur.fetchall ()[0]['sid']

        t1 = time.time ()
        cur.execute ("update tlb set load = " +str (max_load - 1)+" where sid = "+str (s_id)+";")
        t2 = time.time ()
        f.write ('----lb*tenant: re-balance----' + str ((t2-t1)*1000) + '\n')
        f.flush ()

        t3 = time.time ()
        cur.execute("select max (counts) from clock;")
        ct = cur.fetchall () [0]['max'] 
        cur.execute ("INSERT INTO p_spv VALUES (" + str (ct+1) + ", 'on');")
        t4 = time.time ()
        f.write ('----(lb+rt)*tenant: re-balance----' + str ((t2-t1 + t4-t3)*1000) + '\n')
        # f.write ('----lb+rt: re-balance (absolute)----' + str ((t2-t1 + t4-t3)*1000) + '\n')
        f.flush ()


    def op_lb (cur=cur, f=f):
        t1 = time.time ()
        cur.execute ("select max(load) from lb ;")
        t2 = time.time ()
        f.write ('----lb: check max load----' + str ((t2-t1)*1000) + '\n')
        f.flush ()
        max_load = cur.fetchall ()[0]['max']

        cur.execute ("select sid from lb where load = "+str (max_load)+" limit 1;")
        s_id = cur.fetchall ()[0]['sid']
        t1 = time.time ()
        cur.execute ("update lb set load = " +str (max_load - 1)+" where sid = "+str (s_id)+";")
        t2 = time.time ()
        # f.write ('----lb: re-balance (per rule)----' + str ((t2-t1)*1000) + '\n')
        f.write ('----lb: re-balance (absolute)----' + str ((t2-t1)*1000) + '\n')
        f.flush ()

        t3 = time.time ()
        cur.execute("select max (counts) from clock;")
        ct = cur.fetchall () [0]['max'] 
        cur.execute ("INSERT INTO p_spv VALUES (" + str (ct+1) + ", 'on');")
        t4 = time.time ()
        f.write ('----lb+rt: re-balance (per rule)----' + str ((t2-t1 + t4-t3)*1000) + '\n')
        f.write ('----lb+rt: re-balance (absolute)----' + str ((t2-t1 + t4-t3)*1000) + '\n')
        f.flush ()

    def op_tacl (cur=cur, f=f):

        t1 = time.time ()
        cur.execute ("select end1, end2 from tacl limit 1;")
        t2 = time.time ()
        f.write ('----acl*tenant: check violation----' + str ((t2-t1)*1000) + '\n')
        f.flush ()
        t = cur.fetchall ()[0]
        e1 = t['end1']
        e2 = t['end2']

        t1 = time.time ()
        cur.execute ("update tacl set isviolated = 0 where end1 = "+ str (e1) +" and end2 = "+str (e2)+";")
        t2 = time.time ()
        f.write ('----acl*tenant: fix violation----' + str ((t2-t1)*1000) + '\n')
        f.flush ()

        t3 = time.time ()
        cur.execute("select max (counts) from clock;")
        ct = cur.fetchall () [0]['max'] 
        cur.execute ("INSERT INTO p_spv VALUES (" + str (ct+1) + ", 'on');")
        t4 = time.time ()
        f.write ('----acl+rt*tenant: fix violation----' + str ((t2-t1 + t4-t3)*1000) + '\n')
        f.flush ()


    def op_acl (cur=cur, f=f):

        t1 = time.time ()
        cur.execute ("select end1, end2 from acl limit 1;")
        t2 = time.time ()
        f.write ('----acl: check violation----' + str ((t2-t1)*1000) + '\n')
        f.flush ()
        t = cur.fetchall ()[0]
        e1 = t['end1']
        e2 = t['end2']

        t1 = time.time ()
        cur.execute ("update acl set isviolated = 0 where end1 = "+ str (e1) +" and end2 = "+str (e2)+";")
        t2 = time.time ()
        f.write ('----acl: fix violation----' + str ((t2-t1)*1000) + '\n')
        f.flush ()

        t3 = time.time ()
        cur.execute("select max (counts) from clock;")
        ct = cur.fetchall () [0]['max'] 
        cur.execute ("INSERT INTO p_spv VALUES (" + str (ct+1) + ", 'on');")
        t4 = time.time ()
        f.write ('----acl+rt: fix violation (per rule)----' + str ((t2-t1 + t4-t3)*1000) + '\n')
        f.write ('----acl+rt: fix violation (absolute)----' + str ((t2-t1 + t4-t3)*1000) + '\n')
        f.flush ()
        
    def routing_ins (fid, cur=cur, hosts=uhosts, f=f):

        # print hosts
        [h1, h2] = random.sample(uhosts, 2)
        # print [h1,h2]

        t1 = time.time ()
        cur.execute ("INSERT INTO rtm values (%s,%s,%s);",([int (fid),int (h1),int (h2)]))
        t2 = time.time ()
        f.write ('----rt: route ins----' + str ((t2-t1)*1000) + '\n')
        f.flush ()

    def init_acl_lb (cur=cur):
        cur.execute ("select sum(load) from lb ;")
        agg_load = cur.fetchall ()[0]['sum']

        cur.execute ("select count(*) from lb ;")
        switch_size = cur.fetchall ()[0]['count']

        cur.execute ("select max(load) from lb;")
        max_load = cur.fetchall ()[0]['max']
        print "max_load is: " + str (max_load)

        cur.execute (""" 
        CREATE OR REPLACE RULE lb_constraint AS
        ON INSERT TO p1
        WHERE (NEW.status = 'on')
        DO ALSO (
            UPDATE lb SET load = """ +str (max_load+1)+ """ WHERE load > """ +str (max_load+1)+""";
	    UPDATE p1 SET status = 'off' WHERE counts = NEW.counts;
	   );        
""")
        
        residual_load = switch_size * max_load - agg_load
        return residual_load

    def routing_ins_acl_lb_tenant (hosts, fid, cur=cur, f=f):
        [h1, h2] = random.sample(hosts, 2)

        t1 = time.time ()
        cur.execute ("INSERT INTO tenant_policy VALUES ("+str (fid) +"," +str (h1) + "," + str (h2)+");")
        cur.execute("select max (counts) from clock;")
        ct = cur.fetchall () [0]['max'] 
        cur.execute ("INSERT INTO t1 VALUES (" + str (ct+1) + ", 'on');")
        t2 = time.time ()
        f.write ('----(acl+lb+rt)*tenant: route ins----' + str ((t2-t1)*1000) + '\n')
        f.flush ()


    def routing_ins_acl_lb (h1s, h2s, fid, cur=cur, f=f):
        h1 = random.sample(h1s, 1)[0]
        h2 = random.sample(h2s, 1)[0]

        t1 = time.time ()
        cur.execute ("INSERT INTO utm VALUES ("+str (fid) +"," +str (h1) + "," + str (h2)+");")
        cur.execute("select max (counts) from clock;")
        ct = cur.fetchall () [0]['max'] 
        cur.execute ("INSERT INTO p1 VALUES (" + str (ct+1) + ", 'on');")
        t2 = time.time ()
        f.write ('----acl+lb+rt: route ins----' + str ((t2-t1)*1000) + '\n')
        f.flush ()

    def routing_del (fid, cur=cur, hosts=hosts, f=f):
        t1 = time.time ()
        cur.execute ("DELETE FROM tm WHERE fid =" +str (fid)+ ";")
        t2 = time.time ()
        f.write ('----rt: route del----' + str ((t2-t1)*1000) + '\n')
        f.flush ()

    def mt_updown (cur = cur, hosts = hosts, f=f):
        s = random.sample (switches,1)[0]
        print s

        t1 = time.time ()
        cur.execute ("UPDATE mt SET isactive = 0 WHERE sid = %s;",([s]))
        t2 = time.time ()
        f.write ('----maintenance down----' + str ((t2-t1)*1000) + '\n')
        f.flush ()

        cur.execute ("UPDATE mt SET isactive = 1 WHERE sid = %s;",([s]))


    def link_updown (flag, cur=cur, hosts=hosts, f=f, links = links):
        link = random.sample(links, 1)[0]
        print link

        t1 = time.time ()
        cur.execute ("UPDATE tp SET isactive = 0 WHERE sid = %s AND nid = %s;",([link[0], link[1]]))
        t2 = time.time ()
        f.write ('----'+flag+': linkdown----' + str ((t2-t1)*1000) + '\n')
        f.flush ()

        # cur.execute ("SELECT * from cf;")
        # cs = cur.fetchall ()
        # print 'link_down'
        # print cs

        t1 = time.time ()
        cur.execute ("UPDATE tp SET isactive = 1 WHERE sid = %s AND nid = %s;",([link[0], link[1]]))
        t2 = time.time ()
        f.write ('----'+flag+': linkup----' + str ((t2-t1)*1000) + '\n')
        f.flush ()

        # cur.execute ("SELECT * from cf;")
        # cs = cur.fetchall ()
        # print 'link_up'
        # print cs

    def primitive (rounds):
        for i in range (rounds):
            print i
            routing_ins (i+1)

        init_lb ()
        for i in range (rounds):
            op_lb ()

        init_acl ()
        cur.execute("select count(*) from acl;")
        ct = cur.fetchall () [0]['count']
        for i in range (ct):
            op_acl ()

        for i in range (rounds):
            link_updown ('rt')

        capacity = init_acl_lb ()
        print "capacity is: "+ str (capacity)
        cur.execute ("SELECT DISTINCT end1 FROM acl_tb;")
        cs = cur.fetchall ()
        h1s = [h['end1'] for h in cs]
        cur.execute ("SELECT DISTINCT end2 FROM acl_tb;")
        cs = cur.fetchall ()
        h2s = [h['end2'] for h in cs]
        # print h2s
        for i in range (capacity):
            routing_ins_acl_lb (h1s, h2s, int (rounds + i + 1))

    def tenant_fullmesh_clean (cur = cur):
        cur.execute ("truncate tm;")
        cur.execute ("truncate utm;")
        cur.execute ("truncate cf;")
        cur.execute ("truncate tenant_hosts;")

    def tenant_fullmesh (hosts, cur = cur, f=f):
        cur.execute ("select max(fid) from utm ;")
        t = cur.fetchall ()
        if t[0]['max'] == None:
            fid = 1
        else:
            fid = int (t[0]['max'])  + 1

        cur.execute ("select max (counts) from clock;")
        ct = cur.fetchall ()[0]['max'] + 1

        l = len (hosts)
        for i in range (l):
            for j in range (i+1,l):
                print "tenant_fullmesh: [" + str (hosts[i]) + "," + str (hosts[j]) + "]"
                t1 = time.time ()
                cur.execute ("INSERT INTO tenant_policy values (%s,%s,%s);",([str (fid) ,int (hosts[i]), int (hosts[j])]))
                cur.execute ("INSERT INTO p_spv values (%s,'on');",([ct]))
                t2 = time.time ()
                f.write ('----rt*tenant: route ins----' + str ((t2-t1)*1000) + '\n')
                f.flush ()
                ct += 1
                fid += 1

    def tenant (size):

        def init_tenant (size):
            selected_hosts = load_tenant_schema (dbname, username, size)
            print selected_hosts
            tenant_fullmesh (selected_hosts)
            print "--------------------> init_tenant successful"

        init_tenant (size)
        init_tacl ()
        init_tlb ()

        for i in range (size*3):
            op_tlb ()

        cur.execute("select count(*) from tacl;")
        ct = cur.fetchall () [0]['count']
        for i in range (ct):
            op_tacl ()

        cur.execute ("select * from tenant_hosts ;")
        cs = cur.fetchall ()
        thosts = [h['hid'] for h in cs]
        for i in range (10):
            cur.execute ("select max (fid) from utm;")
            fid = cur.fetchall ()[0]['max'] + 1
            routing_ins_acl_lb_tenant (thosts, fid)
        
    # primitive
    # logdest = os.getcwd () + '/data/' + logdestfile + '.log'

    if default == 4:
        # primitive (rounds)
        # s = raw_input("primitive or tenant: (p or t)")
        s = 't'

        if s == 'p':
            primitive (rounds)
            cur.execute ("truncate cf, clock, p1, p2, p3, p_spv, pox_hosts, pox_switches, pox_tp, rtm, rtm_clock, spatial_ref_sys, spv_tb_del, spv_tb_ins, tm, tm_delta, utm, acl_tb, lb_tb;")
            cur.execute ("INSERT INTO clock values (0);")
            logdest += 'primitive'

        elif s == 't':
            tenant (10)
            cur.execute ("truncate cf, clock, p1, p2, p3, p_spv, pox_hosts, pox_switches, pox_tp, rtm, rtm_clock, spatial_ref_sys, spv_tb_del, spv_tb_ins, tm, tm_delta, utm, acl_tb, lb_tb;")
            cur.execute ("INSERT INTO clock values (0);")
            cur.execute ("truncate t1, t2, t3, tacl_tb, tenant_hosts, tlb_tb;")

            logdest += 'tenant'

        f.close ()
        os.system ("cp "+ logfile + ' ' + logdest)
        os.system ("sudo cp "+ logdest + ' ' + ' /media/sf_share/ravel_plot/')

        print "--------------------> batch_test successful"
        conn.close()


    while default == 5:
        n = raw_input("play or exit (p, e)")
        if n == 'p':
            pass
        elif n == 'e':
            t = raw_input("clean database? ('y'/'n'): ")
            if t.strip () == 'y':
                kill_pox_module ()
                clean_db (dbname)
                break
            elif t.strip () == 'n':
                kill_pox_module ()
                break


    while default == 1:
        n = raw_input("select actions: \n\t r (routing) \n\t t (tenant) \n\t e (exit)\n\t m (maintenance)\n\t ct (clean tenant)")

        if n == 'r':
            primitive (rounds)
            # for i in range (0,rounds):
            #     routing_ins (i)

            # for i in range (0,rounds):
            #     link_updown ('routing')

            # for i in range (0, rounds):
            #     routing_del (i)

            logdest += 'routing'

        elif n == 't':

            def init_tenant (size):
                selected_hosts = load_tenant_schema (dbname, username, size)
                print selected_hosts
                tenant_fullmesh (selected_hosts)
                print "--------------------> init_tenant successful"

            size = raw_input("select tenant size (1 - " + str (len (hosts) -1) + "): ")
            init_tenant (int (size))
            init_tacl ()
            init_tlb ()

            logdest += 'tenant' + str (s)

            # selected_hosts = load_tenant_schema (dbname, username, int (s))
            # tenant_fullmesh (selected_hosts)
            # for i in range (0,rounds):
            #     link_updown ('tenant_fullmesh')
        elif n == 'ct':
            tenant_fullmesh_clean ()

        elif n == 'm':
            selected_hosts = load_tenant_schema (dbname, username, 10)
            tenant_fullmesh (selected_hosts)

            load_mt_schema (dbname, username)
            for i in range (0, rounds):
                mt_updown ()

            tenant_fullmesh_clean ()

        elif n == 'e':
            f.close ()
            # logdest = os.getcwd () + '/data/log_' + str (datetime.datetime.now ()) .replace(" ", "-").replace (":","-").replace (".","-")
            os.system ("cp "+ logfile + ' ' + logdest)

            print "--------------------> batch_test successful"
            conn.close()
            break

    if default == 2:
        for i in range (0,rounds):
            routing_ins (i)

        for i in range (0,rounds):
            link_updown ('routing')

        for i in range (0, rounds):
            routing_del (i)
        
        logdest += 'routing'
        f.close ()
        os.system ("cp "+ logfile + ' ' + logdest)

        print "--------------------> batch_test primitive successful"
        conn.close()


    if default == 3:
        selected_hosts = load_tenant_schema (dbname, username, 20)
        tenant_fullmesh (selected_hosts)
        for i in range (0,rounds):
            link_updown ('tenant_fullmesh')
        tenant_fullmesh_clean ()

        logdest += 'tenant20'
        f.close ()
        os.system ("cp "+ logfile + ' ' + logdest)

        print "--------------------> batch_test successful"
        conn.close()

def load_pox_module (dbname,username):
    cmd = "/home/mininet/pox/pox.py pox.openflow.discovery pox.samples.pretty_log pox.host_tracker db --dbname=" + str (dbname) + " --username=" + str (username)
    # cmd = "/home/mininet/pox/pox.py pox.openflow.discovery pox.samples.pretty_log pox.forwarding.l3_learning pox.host_tracker db"
    os.system (cmd + " &")
    print "--------------------> load_pox_module successful: Fan's db.py running in the background"

def kill_pox_module ():
    cmd = "pkill -f '/home/mininet/pox/pox.py pox.openflow.discovery pox.samples.pretty_log pox.host_tracker db'"
    # cmd = "pkill -f '/home/mininet/pox/pox.py pox.openflow.discovery pox.samples.pretty_log pox.forwarding.l3_learning pox.host_tracker db'"
    os.system (cmd)
    print "--------------------> kill pox module that populates mininet events to database"


def load_mt_schema (dbname, username):
    conn = psycopg2.connect(database= dbname, user= username)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute (""" 
----------------------------------------------------------------------
-- maintenance application
----------------------------------------------------------------------
    insert into mt_tb values (1),(64),(100),(122),(160),(200);
""")

    print "-------------------->load_mt_schema successful"
    conn.close()


def init_tenant2 (dbname, username, size):
    conn = psycopg2.connect(database= dbname, user= username)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute ("SELECT * FROM uhosts;")
    cs = cur.fetchall ()
    hosts = [int (s['u_hid']) for s in cs]

    selected_hosts = [ hosts[i] for i in random.sample(xrange(len(hosts)), size) ]

    for h in selected_hosts:
        cur.execute ("insert into tenant_hosts values (" + str (h) + ");")

    print '--------------------> init_tenant, interact with \'tenant_hosts\' and \'tenant_policy\''

    conn.close()
    return selected_hosts

def load_tenant_schema (dbname, username, size):
    conn = psycopg2.connect(database= dbname, user= username)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    load_schema (dbname, username, '/home/mininet/ravel/sql_scripts/tenant.sql')

    cur.execute ("SELECT * FROM uhosts;")
    cs = cur.fetchall ()
    hosts = [int (s['u_hid']) for s in cs]

    selected_hosts = [ hosts[i] for i in random.sample(xrange(len(hosts)), size) ]

    for h in selected_hosts:
        cur.execute ("insert into tenant_hosts values (" + str (h) + ");")

    print '--------------------> create tenant, interact with \'tenant_hosts\' and \'tenant_policy\''

    conn.close()
    return selected_hosts

def perform_test (dbname, username):
    
    while True:
        n = raw_input("select test actions: \n\t'e'(exit) \n\t'b'(batch test) \n\t't'(dc tenant)\n")
        if n.strip() == 'e':
            t = raw_input("clean database? ('y'/'n'): ")
            if t.strip () == 'y':
                kill_pox_module ()
                clean_db (dbname)
                break
            elif t.strip () == 'n':
                kill_pox_module ()
                break
        elif n.strip () == 'b':
            print 'start batch_test ()'
            print 'flag = routing'
            batch_test (dbname, username, 10, flag='routing')

        elif n.strip () == 't':
            print 'play with dc tenant'
            load_tenant_schema (dbname, username)


#     cur.execute (""" 

# DROP TABLE IF EXISTS tenant_hosts CASCADE;
# CREATE UNLOGGED TABLE tenant_hosts (
#        hid	integer,
#        PRIMARY key (hid)
# );

# CREATE OR REPLACE VIEW tenant_policy AS (
#        SELECT DISTINCT host1, host2 FROM rtm
#        WHERE host1 IN (SELECT * FROM tenant_hosts)
#        	     AND host2 IN (SELECT * FROM tenant_hosts)
# );

# CREATE OR REPLACE FUNCTION tenant_policy_ins_fun() RETURNS TRIGGER AS
# $$
# plpy.notice ("tenant_policy_ins_fun")

# h1 = TD["new"]["host1"]
# h2 = TD["new"]["host2"]

# hs = plpy.execute ("SELECT hid FROM tenant_hosts;")
# hosts = [h['hid'] for h in hs]

# fid = int (plpy.execute ("select count(*) +1 as c from rtm")[0]['c']) 

# if (h1 in hosts) & (h2 in hosts):
#     plpy.execute ("INSERT INTO rtm values (" + str (fid)  + "," +str (h1)+ "," + str (h2) + ");")

# return None;
# $$
# LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;

# CREATE TRIGGER tenant_policy_ins_trigger
#      INSTEAD OF INSERT ON tenant_policy
#      FOR EACH ROW
#    EXECUTE PROCEDURE tenant_policy_ins_fun();

# CREATE OR REPLACE RULE tenant_policy_del AS
#        ON DELETE TO tenant_policy
#        DO INSTEAD
#        DELETE FROM rtm WHERE host1 = OLD.host1 AND host2 = OLD.host2;

# """)
