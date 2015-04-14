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
sql_script3 = "/home/mininet/ravel/sql_scripts/base_and_routing_wo.sql"
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

def procedure_batch ():

    dbname = select_dbname ()
    create_db (dbname)
    add_pgrouting_plpy_plsh_extension (dbname, username)

    while True:
        m = raw_input ("test or exit? (t/e) \n")
        if m == 'e':
            t = raw_input("clean database? ('y'/'n'): ")
            if t.strip () == 'y':
                kill_pox_module ()
                clean_db (dbname)
                break
            elif t.strip () == 'n':
                kill_pox_module ()
                break
        elif m == 't' :
            n = raw_input("select test actions: \n\t r (routing) \n\t a (auto-re-routing) \n\t t (tenant) \n")
            if n.strip () == 'r':
                print "routing in postgres, no mininet operation"
                r = raw_input ("input rounds #:\n")
                load_schema (dbname, username, sql_script3)
                load_database (dbname, username)
                batch_test (dbname, username, int (r), flag='routing')

if __name__ == '__main__':

    procedure_batch ()

    # d = select_dbname ()
    # print d
    # load_fattree (4)



