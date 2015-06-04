import sys
import time
import random
import os
import psycopg2
import psycopg2.extras
import subprocess
import datetime
from igraph import *

execfile("libRavel.py")
import libRavel

switch_size = 0
fanout_size = 0
monitor_mininet = 0
k_size = 0 # number of pods of the fat tree

username = 'mininet'
sql_script1 = "/home/mininet/ravel/sql_scripts/base_and_routing_w.sql"
sql_script2 = "/home/mininet/ravel/sql_scripts/obs_app.sql"
sql_script3 = "/home/mininet/ravel/sql_scripts/base_and_routing_wo_optimized.sql"
primitive = "/home/mininet/ravel/sql_scripts/primitive.sql"
tenant = "/home/mininet/ravel/sql_scripts/tenant.sql"
# without mininet operation, that is, no actual add_flow / del_flow,
# just absolute value of postgres time

def procedure_interactive ():

    dbname = select_dbname ()
    create_db (dbname)
    add_pgrouting_plpy_plsh_extension (dbname, username)
    load_schema (dbname, username, sql_script1)
    # load_schema (dbname, username, sql_script2)
    load_database (dbname, username)
    perform_test (dbname, username)

def procedure ():

    dbname = select_dbname ()
    create_db (dbname)
    add_pgrouting_plpy_plsh_extension (dbname, username)

    while True:
        m = raw_input ("test or exit? (t/e) \n")
        if m == 't' :
            if database_exists == 0:
                load_schema (dbname, username, primitive)
                init_database (dbname, username)

            m2 = raw_input ("interactive or batch? (i/b) \n")
            if m2.strip () == 'b':
                r = raw_input ("input rounds #:\n")
                batch_test (dbname, username, int (r), 1)

            elif m2.strip () == 'i':
                while True:
                    m3 = raw_input("maintenance (m), or exit(e), or tenant(t) ")
                    if m3.strip () == 'm':
                        load_mt_schema (dbname, username)
                        break
                    elif m3.strip () == 't':
                        # load_tenant_schema (dbname, username, 10)
                        load_schema (dbname, username, tenant)
                        init_tenant (dbname, username, 6)
                        break
                    elif m3.strip () == 'e':
                        break

        elif m == 'e':
            t = raw_input("clean database? ('y'/'n'): ")
            if t.strip () == 'y':
                kill_pox_module ()
                clean_db (dbname)
                break
            elif t.strip () == 'n':
                kill_pox_module ()
                break

def batch (l):
    def generate_db (k_size, dbname, username):
        clean_db (dbname)
        create_db (dbname)
        add_pgrouting_plpy_plsh_extension (dbname, username)
        load_schema (dbname, username, primitive)
        init_fattree (k_size, dbname, username)

    for dbname in l:
        k_size = int (dbname[7:]) 
        print "for " + dbname + ":"
        generate_db (k_size, dbname, 'mininet')

    for dbname in l:
        print "for " + dbname + " batch_test:"
        batch_test (dbname, username, 30, 4)

if __name__ == '__main__':

    while True:
        m = raw_input ("batch, interactive, or exit? (b, i, e) \n")

        if m == 'i':
            procedure ()

        elif m == 'b':
            l1 = ['fattree16', 'fattree32', 'fattree64']
            l2 = ['fattree4', 'fattree8', 'fattree16']
            batch (l2)

        elif m == 'e':
            break
