execfile("libRavel.py")
execfile("plot.py")
execfile("batch.py")
execfile("batch_profile.py")
execfile("batch_fattree.py")
execfile("batch_isp.py")
# execfile ("toy.py")
execfile("toyt.py")

import libRavel
import batch
import batch_profile
import batch_fattree
import batch_isp
# import toy
import toyt

print "load classes\n"

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

l1 = ['fattree16', 'fattree32', 'fattree64']
l3 = ['isp4755_10', 'isp4755_100', 'isp4755_1000']
l4 = ['isp2914_10', 'isp4755_10', 'isp7018_10']

nsql = '/home/mininet/ravel/sql_scripts/sigcomm_example.sql'
