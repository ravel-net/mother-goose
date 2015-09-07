execfile("libRavel.py")
execfile("batch.py")
execfile("batch_profile.py")
execfile("batch_fattree.py")
execfile("batch_isp.py")

import libRavel
import batch
import batch_profile
import batch_fattree
import batch_isp

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
        m = raw_input ("batch, interactive, generate_db, mininet, or exit? (b, i, g, m, e) \n")

        if m == 'i':
            procedure ()

        elif m == 'b':
            t = Batch_profile (l3[0], 4)
            t.rtm_ins (4)
            t.rtm_del ()
            t.re_route ()
            t.close ()

            # t2 = Batch_fattree (l3[0], 4)
            # t2.primitive ()
            # t2.close ()

            t3 = Batch_fattree (l3[0], 4)
            t3.tenant ()
            t3.close ()

            t4 = Batch_isp ('isp4755', 4)
            # print t4.links
            t4.close ()

        elif m == 'g':
            gdb (l3, primitive)
        
        elif m == 'm':
            mininet_interactive ()

        # if m == 'p':
        #     profile (l1[:1], username, 30)

        elif m == 'e':
            break
