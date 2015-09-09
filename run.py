execfile("libRavel.py")
execfile("plot.py")
execfile("batch.py")
execfile("batch_profile.py")
execfile("batch_fattree.py")
execfile("batch_isp.py")

import libRavel
import batch
import batch_profile
import batch_fattree
import batch_isp
import plot

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
    l4 = ['isp4755_10', 'isp4755_100', 'isp4755_1000']

    while True:
        m = raw_input ("batch, interactive, mininet, or exit? (b, i, m, e) \n")

        if m == 'b':

            primitive = rPlot_primitive ('fattree')
            for db in l2:
                t2 = Batch_fattree (db, 4)
                t2.primitive ()
                t2.close ()
                primitive.add_log (t2.logdest)
            primitive.gen_dat ()
            primitive.gen_plt ()

            tenant = rPlot_tenant ('fattree')
            for db in l2:
                t3 = Batch_fattree (db, 4)
                t3.tenant ()
                t3.close ()
                tenant.add_log (t3.logdest)
            tenant.gen_dat ()
            tenant.gen_plt ()

            isp = rPlot_primitive ('isp')
            for db in l4:
                t4 = Batch_isp (db, 4)
                t4.primitive ()
                t4.close ()
                isp.add_log (t4.logdest)
            isp.gen_dat ()
            isp.gen_plt ()

                # t = Batch_profile (db, 4)
                # t.primitive ()
                # t.close ()

        elif m == 'i':
            procedure ()

        elif m == 'm':
            mininet_interactive ()

        # if m == 'p':
        #     profile (l1[:1], username, 30)

        elif m == 'e':
            break
