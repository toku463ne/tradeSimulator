import psycopg2
import db
from env import *

class PostgreSqlDB(db.DB):
	def __init__(self, is_master=False):
		self.is_master = is_master

	def connect(self):
		inf = conf["postgresql"]

		condb = inf["db"]
		if self.is_master == False:
			if conf["is_test"]:
				condb = inf["test_db"]

		inf = conf["postgresql"]
		conn_string = "host=%s dbname=%s user=%s password=%s" % (
			inf["host"],
			condb,
			inf["user"],
			inf["password"])
		conn =  psycopg2.connect(conn_string)
		conn.autocommit = True
		return conn

	def execSql(self, sql):
		cur = None
		try:
			cur = self.connect().cursor()
			cur.execute(sql)
			return cur
		except:
			if cur: cur.close()
			print(sql)
			raise

	def truncateTable(self, tablename):
		sql = "truncate table %s;" % tablename
		return self.execSql(sql)
		
	def countTable(self, tablename, whereList=[]):
		if self.tableExists(tablename) == False:
			return 0
		strwhere = ""
		if len(whereList) > 0:
			strwhere = "where %s" % (" and ".join(whereList))
		sql = "select count(*) as cnt from %s %s" % (tablename, strwhere)
		cur = self.execSql(sql)
		row = cur.fetchone()
		cur.close()
		return row[0]

	def close(self):
		if self.conn != None:
			self.conn.close()

	def _createTableFromTemplate(self, sqlFile, tableName, replaces={}):
		try:            
			f = open(sqlFile, "r")
			sql = f.read()
			sql = sql.replace("#TABLENAME#", tableName)
			for k in replaces.keys():
				sql = sql.replace(k, replaces[k])
			f.close()
			cur = self.execSql(sql)
			cur.close()
		except:
			raise

	def createTable(self, tableName, templateName="", replaces={}):
		if templateName != "":
			self._createTableFromTemplate("%s/postgresql/create_table_%s.sql" % (SQL_DIR, 
                                                        templateName), tableName, replaces)
		else:
			self._createTableFromTemplate("%s/postgresql/create_table_%s.sql" % (SQL_DIR, 
                                                        tableName), tableName)
	
	def tableExists(self, tableName):
		sql = """SELECT EXISTS (
    SELECT FROM pg_catalog.pg_tables
    WHERE tablename  = '%s'
);
""" % (tableName.lower())
		(b,) = self.select1rec(sql)
		return b


	def dropTable(self, tableName):
		self.execSql("drop table if exists %s;" % tableName)

	def select1rec(self, sql):
		cur = self.execSql(sql)
		row = cur.fetchone()
		cur.close()
		if row:
			return row
		return None

	def select1value(self, tableName, field, whereList):
		strwhere = ""
		strwhere = "where %s" % (" and ".join(whereList))
		sql = "select %s as cnt from %s %s" % (field, tableName, strwhere)
		row = self.select1rec(sql)
		if row:
			(val,) = row
			return val
		return None

def execSql(sql):
	return PostgreSqlDB().execSql(sql)