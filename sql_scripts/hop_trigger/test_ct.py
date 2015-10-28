import psycopg2
import psycopg2.extras
import psycopg2.extensions

username = 'mininet'
dbname = 'fattree16'

connect = psycopg2.connect(database= dbname, user= username)
cur = connect.cursor()

filename = "/tmp/log.txt"
open(filename, 'w').close()

cur.execute(open("/home/mininet/ravel/sql_scripts/tgs_counting_fattree.sql", "r").read())


connect.commit()
cur.close()
connect.close()
