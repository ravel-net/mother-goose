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
sql_script1 = "/home/mininet/ravel/sql_scripts/base_and_routing_w.sql"
sql_script2 = "/home/mininet/ravel/sql_scripts/obs_app.sql"
sql_script3 = "/home/mininet/ravel/sql_scripts/base_and_routing_wo_optimized.sql"
primitive = "/home/mininet/ravel/sql_scripts/primitive.sql"
tenant = "/home/mininet/ravel/sql_scripts/tenant.sql"
# without mininet operation, that is, no actual add_flow / del_flow,
# just absolute value of postgres time

# def procedure_interactive ():
#     dbname = select_dbname ()
#     create_db (dbname)
#     add_pgrouting_plpy_plsh_extension (dbname, username)
#     load_schema (dbname, username, sql_script1)
#     # load_schema (dbname, username, sql_script2)
#     load_database (dbname, username)
#     perform_test (dbname, username)

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

def batch (l, rounds):
    for dbname in l:
        print "for " + dbname + " batch_test:"
        batch_test (dbname, username, rounds, 4)

def gdb (l, rounds):
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

if __name__ == '__main__':
    l1 = ['fattree16', 'fattree32', 'fattree64']
    l2 = ['fattree4', 'fattree8', 'fattree16']
    l3 = ['fattree16']

    while True:
        m = raw_input ("batch, interactive, generate_db, mininet, or exit? (b, i, g, m, e) \n")

        if m == 'i':
            procedure ()

        elif m == 'b':
            batch (l1, 30)

        elif m == 'g':
            gdb (l3,30)
        
        elif m == 'm':
            mininet_interactive ()

        elif m == 'e':
            break
