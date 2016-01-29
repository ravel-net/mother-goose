import difflib
from collections import defaultdict
import random


deltafile = "/tmp/delta.txt"


def get_delta1(file1, file2):
	open(deltafile, 'w').close()
	fo = open(deltafile, 'a')
	
	with open(file1, 'r') as f1:
		lines1 = f1.readlines()
	with open(file2, 'r') as f2:
		lines2 = f2.readlines()

	def getGroupName(theList, bound):
		return next((x for x in reversed(theList[:bound+1]) if x.startswith("#")))

	lineCount = 0
	for line in difflib.unified_diff(lines1, lines2, fromfile='file1', tofile='file2', lineterm='', n=0):
        	if not (line.startswith("---") or line.startswith("+++") or line.startswith("@@")):
			groupName = getGroupName(lines2,lineCount)
        		fo.write(groupName+line)
			fo.flush
		lineCount += 1


def get_delta(file1, file2):
	data1 = parse_emerging(file1)
	data2 = parse_emerging(file2)
	insertion = defaultdict(list)
	deletion = defaultdict(list)
	for k,v in data1.items():
		set1 = set(v)
		set2 = set(data2[k])
		insertion[k] = list(set2-set1)
		deletion[k] = list(set1 - set2)
	return (insertion, deletion)







def parse_emerging(filepath):
	
	f = open(filepath, 'r')
	groupname = ""
	data = defaultdict(list)
	
	for l in f.readlines():
		if(l[0] == '#'):
			if(l[2:7] == 'Feodo'):
				groupname = "feodo"
			elif(l[2:6]== 'Zeus'):
				groupname = "zeus"
			elif(l[2:8] == 'Spyeye'):
				groupname = "spyeye"
			elif(l[2:8] == 'Palevo'):
				groupname = "palevo"
			elif(l[1:9] == 'Spamhaus'):
				groupname = "spamhaus"
			elif(l[1:8] == 'Dshield'):
				groupname = "dshield"
			else:
				pass
		elif(l[0].isdigit()):
			data[groupname].append(l[:-1])
			
		else:
			pass

	return data

def test(data,db):
	print("testting")
	for k, v in data.items():
			print(k)

def init_emerging(data, db, percent):
	for k,v in data.items():
		print(k)
		sampled_v = random.sample(v, int(len(v)*percent/100)) 	
		db.cur.execute("select * from groupid where gname = '"+ k+ "'")
		findg = db.cur.fetchall()
		if findg and sampled_v:
			gid = findg[0]["gid"]
			sa_arr = []
			for each in sampled_v:
				db.cur.execute("select * from addrid where addr = '"+ each + "';")
				find = db.cur.fetchall()
                        	if find:
                                	sa_arr.append(find[0]["aid"])
				else:
					db.cur.execute("select max(aid) from addrid ;")
					res = db.cur.fetchall()
					maxid = res[0]["max"]
					if not maxid:
						maxid = 0
					
	                                db.cur.execute("insert into addrid values ('"+ each + "', "+ str(maxid+1)+ ");")
        	                        sa_arr.append(maxid+1)
			for sid in sa_arr:	
				db.cur.execute("insert into PGA_group values ("+ str(gid) + ", "+ str(sid)+ ")")

	
		
def stat_delta(delta):
	insert = delta[0]
	ins = 0
	for k,v in insert.items():
		print(k)
		ins = ins + len(v)
	delete = delta[1]
	de = 0
	for k, v in delete.items():
		print(k)
		de = de + len(v)
	res = []
	res.append(ins)
	res.append(de)
	return res	
		

			
def apply_delta(db, delta):
        insert = delta[0]
        delete = delta[1]
        for k,v in insert.items():
                db.cur.execute("select * from groupid where gname = '"+ k +"'")
                gid = db.cur.fetchall()[0]["gid"]
                sa_arr = []
                for each in v:
                        db.cur.execute("select * from addrid where addr = '"+ each + "';")
                        find = db.cur.fetchall()
                        if find:
                                sa_arr.append(find[0]["aid"])
                        else:
                                db.cur.execute("select max(aid) from addrid ;")
                                res = db.cur.fetchall()
                                maxid = res[0]["max"]
                                if not maxid:
                                        maxid = 0

                                db.cur.execute("insert into addrid values ('"+ each + "', "+ str(maxid+1)+ ");")
                                sa_arr.append(maxid+1)
                for sid in sa_arr:
                        db.cur.execute("insert into PGA_group values ("+ str(gid) + ", "+ str(sid)+ ")")

        for k,v in delete.items():
                db.cur.execute("select * from groupid where gname = '"+ k+ "'")
                gid = db.cur.fetchall()[0]["gid"]
                sa_arr = []
                for each in v:
                        db.cur.execute("select * from addrid where addr = '"+ each + "';")
                        find = db.cur.fetchall()
                        if find:
                                sa_arr.append(find[0]["aid"])
                for sid in sa_arr:
                        db.cur.execute("delete from PGA_group where gid = "+ str(gid)+ " and sid = "+ str(sid))


def ins_deletion(db, delta):
	delete = delta[1]
	for k, v in delete.items():
		db.cur.execute("select * from groupid where gname = '"+k+"'")
		gid = db.cur.fetchall()[0]["gid"]
		sa_arr = []
		for each in v:
                        db.cur.execute("select * from addrid where addr = '"+ each + "';")
                        find = db.cur.fetchall()
                        if find:
                                sa_arr.append(find[0]["aid"])
                        else:
                                db.cur.execute("select max(aid) from addrid ;")
                                res = db.cur.fetchall()
                                maxid = res[0]["max"]
                                if not maxid:
                                        maxid = 0

                                db.cur.execute("insert into addrid values ('"+ each + "', "+ str(maxid+1)+ ");")
                                sa_arr.append(maxid+1)
                for sid in sa_arr:
                        db.cur.execute("insert into PGA_group values ("+ str(gid) + ", "+ str(sid)+ ")")		



def main():
	#data =parse_emerging("/home/mininet/ravel/emergingthreats/emerging-Block-IPs.txt")
	#print(data)
	print("hello")


if __name__ == "__main__": main()



