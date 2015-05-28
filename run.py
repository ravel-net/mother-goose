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
                        load_tenant_schema (dbname, username, 10)
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

def batch ():
    for dbname in ['fattree16', 'fattree32', 'fattree64']:
        # routing with linkup, linkdown
        # batch_test (dbname, username, 1, 2)
        # tenant with linkup, linkdown
        batch_test (dbname, username, 100, 3)
                    
if __name__ == '__main__':

    batch ()
    # procedure ()

    # d = select_dbname ()
    # print d
    # load_fattree (4)


            # if n.strip () == 'r':
            #     print "routing in postgres, no mininet actions"

            # elif n.strip () == 't':
            #     print "tenant operation in postgres, no mininet actions"
            #     r = raw_input ("input rounds #:\n")
            #     load_schema (dbname, username, sql_script3)
            #     load_database (dbname, username)
            #     batch_test (dbname, username, int (r), flag='tenant')
