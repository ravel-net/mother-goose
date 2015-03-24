import sys
import time
import random
import os
import psycopg2
import psycopg2.extras
import subprocess
import datetime

def create_mininet_topo (dbname, username):
    try:
        conn = psycopg2.connect(database= dbname, user= username)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cur.execute ("SELECT * FROM switches;")
        cs = cur.fetchall ()
        switches = [s['sid'] for s in cs]
        print switches

        cur.execute ("SELECT * FROM hosts;")
        cs = cur.fetchall ()
        hosts = [h['hid'] for h in cs]
        print hosts

        cur.execute ("SELECT * FROM tp;")
        cs = cur.fetchall ()
        links = [[l['sid'],l['nid']] for l in cs]
        print links

    except psycopg2.DatabaseError, e:
        print 'Error %s' % e    
    finally:
        if conn: conn.close()

    def nid_name (nid, s, h):
        if nid in s:
            outid = 's' + str (nid)
        if nid in h:
            outid = 'h' + str (nid)
        return outid

    timestamp = str (datetime.datetime.now ()) .replace(" ", "-").replace (":","-").replace (".","-")
    # timestamp = ""
    filename = os.getcwd () + '/dtp.py'
    fo = open(filename, "w")
    fo.write ('"""' + timestamp)
    fo.write ('\n$ sudo mn --custom ~/ravel/dtp.py --topo mytopo --test pingall')
    fo.write ('\n$ sudo mn --custom ~/ravel/dtp.py --topo mytopo --mac --switch ovsk --controller remote\n')
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

    for hid in hosts:
        h = 'h' + str (hid)
        fo.write ("""
        """ + h + """ = self.addHost('""" + h + """')""")
    fo.write ('\n')

    for sid in switches:
        s = 's' + str (sid)
        fo.write ("""
        """ + s + """ = self.addSwitch('""" + s + """')""")
    fo.write ('\n')
        
    for [nid1, nid2] in links:
        nname1 = nid_name (nid1, switches, hosts)
        nname2 = nid_name (nid2, switches, hosts)
        fo.write ("""
        self.addLink(""" + nname1 + "," + nname2+ """)""")

    fo.write ("""\n
topos = { 'mytopo': ( lambda: MyTopo() ) }
    """)
    fo.write ('\n')
    fo.close ()


def clean_db (dbname):
    try:
        conn = psycopg2.connect(database= "postgres", user= "mininet")
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        cur = conn.cursor()

        cur.execute ("drop database " + dbname)
        print 'Successfully drop database ' + dbname + '\n'

    except psycopg2.DatabaseError, e:
        print "Unable to connect to database " + dbname 
        print 'Error %s' % e    

    finally:
        if conn: conn.close()

def create_db (dbname):
    try:
        conn = psycopg2.connect(database= 'postgres', user= 'mininet')
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        cur = conn.cursor()
        print "Connect to database postgres, as user " + 'mininet'

        cur.execute ("SELECT datname FROM pg_database WHERE datistemplate = false;")
        c = cur.fetchall ()
        dblist = [c[i][0] for i in range (len (c))]
        if dbname not in dblist:
            cur.execute ("CREATE DATABASE " + dbname + ";")
        else:
            print "database " + dbname + " exists, skip"

    except psycopg2.DatabaseError, e:
        print "Unable to connect to database postgres, as user " + 'mininet'
        print 'Error %s' % e

    finally:
        if conn:
            conn.close()

def add_pgrouting_plpy_plsh_extension (dbname, username):

    try:
        conn = psycopg2.connect(database= dbname, user= username)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        cur = conn.cursor()
        print "Connect to database " + dbname + ", as user " + username

        cur.execute ("SELECT 1 FROM pg_catalog.pg_namespace n JOIN pg_catalog.pg_proc p ON pronamespace = n.oid WHERE proname = 'pgr_dijkstra';")

        c = cur.fetchall ()
        if c == []:
            cur.execute ("CREATE EXTENSION IF NOT EXISTS plpythonu;")
            cur.execute ("CREATE EXTENSION IF NOT EXISTS postgis;")
            cur.execute ("CREATE EXTENSION IF NOT EXISTS pgrouting;")
            cur.execute ("CREATE EXTENSION plsh;")

    except psycopg2.DatabaseError, e:
        print 'Error %s' % e
    finally:
        if conn: conn.close()

    

def load_topo3switch (dbname, username):
    try:
        conn = psycopg2.connect(database= dbname, user= username)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        cur = conn.cursor()
        print "Connect to database " + dbname + ", as user " + username

        cur.execute ("""
        TRUNCATE TABLE tp cascade;
        TRUNCATE TABLE cf cascade;
        TRUNCATE TABLE tm cascade;
        INSERT INTO switches(sid) VALUES (4),(5),(6);
        INSERT INTO hosts(hid) VALUES (1),(2),(3);
        INSERT INTO tp(sid, nid) VALUES (1,4), (2,5), (3,6);
        INSERT INTO tp(sid, nid) VALUES (4,5), (5,6), (6,4);
""")
    except psycopg2.DatabaseError, e:
        print "Unable to connect to database " + dbname + ", as user " + username
        print 'Error %s' % e    

    finally:
        if conn: conn.close()

def load_schema (dbname, username, sql_script):
    try:
        conn = psycopg2.connect(database= dbname, user= username)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        cur = conn.cursor()
        print "Connect to database " + dbname + ", as user " + username

        dbscript  = open (sql_script,'r').read()
        cur.execute(dbscript)

    except psycopg2.DatabaseError, e:
        print 'Error %s' % e
    finally:
        if conn: conn.close()

if __name__ == '__main__':

    dbname = raw_input ('Input database name: ')
    username = 'mininet'
    sql_script = "/home/mininet/ravel/mininet_playground.sql"

    create_db (dbname)

    add_pgrouting_plpy_plsh_extension (dbname, username)

    load_schema (dbname, username, sql_script)

    load_topo3switch (dbname, username)

    create_mininet_topo (dbname, username)

    del_flag = raw_input ('Clean the added database (y/n): ')
    if del_flag == 'y':
        clean_db (dbname)

