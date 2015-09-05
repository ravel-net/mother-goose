import time
import sys
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
sql_profile = "/home/mininet/ravel/sql_scripts/primitive_profile.sql"
sql_script1 = "/home/mininet/ravel/sql_scripts/base_and_routing_w.sql"
sql_script2 = "/home/mininet/ravel/sql_scripts/obs_app.sql"
sql_script3 = "/home/mininet/ravel/sql_scripts/base_and_routing_wo_optimized.sql"
primitive = "/home/mininet/ravel/sql_scripts/primitive.sql"
tenant = "/home/mininet/ravel/sql_scripts/tenant.sql"
# without mininet operation, that is, no actual add_flow / del_flow,
# just absolute value of postgres time

def mininet_interactive ():
    dbname = select_dbname ()
    create_db (dbname)
    add_pgrouting_plpy_plsh_extension (dbname, username)
    load_schema (dbname, username, primitive)
    add_cf2flows (dbname, username)
    init_database (dbname, username)
    batch_test (dbname, username, 1, 5)

def procedure ():

    dbname = select_dbname ()
    create_db (dbname)
    add_pgrouting_plpy_plsh_extension (dbname, username)

    while True:
        if database_exists == 0:
            load_schema (dbname, username, primitive)
            init_database (dbname, username)

        m = raw_input ("batch, interactive, or exit? (b/i/e) \n")
        # if m == 't' :
            # m2 = raw_input ("interactive or batch? (i/b) \n")
        if m.strip () == 'b':
            r = raw_input ("input rounds #:\n")
            batch_test (dbname, username, int (r), 1)
            break

        elif m.strip () == 'i':
            batch_test (dbname, username, 1, 1)
            break
                # while True:
                #     m3 = raw_input("maintenance (m), or exit(e), or tenant(t) ")
                #     if m3.strip () == 'm':
                #         load_mt_schema (dbname, username)
                #         break
                #     elif m3.strip () == 't':
                #         break
                #     elif m3.strip () == 'e':
                #         break

        elif m == 'e':
            t = raw_input("clean database? ('y'/'n'): ")
            if t.strip () == 'y':
                kill_pox_module ()
                clean_db (dbname)
                break
            elif t.strip () == 'n':
                kill_pox_module ()
                break

def batch (dbnamelist, username, rounds):
    def fattree_size (dbname, username, rounds):
        batch_test (dbname, username, rounds, 4)

    gdb (dbnamelist, primitive)

    for dbname in l:
        fattree_size (dbname, username, rounds)

def profile (dbnamelist, username, rounds):
    gdb (dbnamelist, sql_profile)

    for d in dbnamelist:
        profile_pg_routing (d, rounds)

if __name__ == '__main__':
    l1 = ['fattree16', 'fattree32', 'fattree64']
    l2 = ['fattree4', 'fattree8', 'fattree16']
    l3 = ['fattree16']

    while True:
        m = raw_input ("profiling, batch, interactive, generate_db, mininet, or exit? (p, b, i, g, m, e) \n")

        if m == 'p':
            profile (l1[:1], username, 30)

        if m == 'i':
            procedure ()

        elif m == 'b':
            batch (l1, 30)

        elif m == 'g':
            gdb (l3, primitive)
        
        elif m == 'm':
            mininet_interactive ()

        elif m == 'e':
            break
