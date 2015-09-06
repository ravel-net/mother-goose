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
execfile("libEval.py")
import libRavel
import libEval

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

if __name__ == '__main__':
    l1 = ['fattree16', 'fattree32', 'fattree64']
    l2 = ['fattree4', 'fattree8', 'fattree16']
    l3 = ['fattree16']

    while True:
        m = raw_input ("class, profiling, batch, interactive, generate_db, mininet, or exit? (c, p, b, i, g, m, e) \n")

        if m == 'c':
            t = NSDI_profile (l3[0], 3, l3[0]+'.log')
            t.rtm_ins ()
            t.rtm_ins ()
            t.rtm_del ()
            t.re_route ()
            t.close ()

            t2 = NSDI_fattree (l3[0], 3, l3[0]+'.log')
            t2.rtm_ins ()
            t2.close ()

            # t2 = ravel (l3[0], primitive, 30, 'profile_rm')
            # t.rtm_del ()
            # t.close ()

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
