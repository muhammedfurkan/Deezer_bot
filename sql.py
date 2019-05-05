import sqlite3


"""
INTEGER: A signed integer up to 8 bytes depending on the magnitude of the value.
REAL: An 8-byte floating point value.
TEXT: A text string, typically UTF-8 encoded (depending on the database encoding).
BLOB: A blob of data (binary large object) for storing binary data.
NULL: A NULL value, represents missing data or an empty cell.
"""


class database:
	def __init__(self, file):
		self.conn = sqlite3.connect(file)
		self.c = self.conn.cursor()

	def close(self):
		self.conn.close()

	def commit(self):
		self.conn.commit()

	def create_table(self, name, keys):
		exec_str = f"""CREATE TABLE {name}("""
		for key, datatype in keys.items():
			exec_str += f'\n{key} {datatype},'
		exec_str = exec_str[:-1] + ');'
		self.c.execute(exec_str)

	def insert(self, table, values):
		exec_str = f'INSERT INTO {table} '
		exec_str += 'VALUES (' + ','.join('?' for x in range(len(values))) + ')'
		self.c.execute(exec_str, values)

	def select(self, table, def_column, def_value, column='*'):
		exec_str = f'SELECT {column} FROM {table} WHERE {def_column} = ?'
		self.c.execute(exec_str, (def_value,))
		result = self.c.fetchall()
		return result

	# def select_one(self, table, def_col, def_val, column='*'):

	def update_one(self, table, def_col, def_val, col, val):
		if isinstance(def_val, str):
			def_val = "'%s'" % def_val
		if isinstance(val, str):
			val = "'%s'" % val
		exec_str = f'UPDATE {table} SET {col} = {val} WHERE {def_col} = {def_val}'
		self.c.execute(exec_str)

	def print_table(self, table):
		items = self.c.execute(f'SELECT * FROM {table}')
		for item in items:
			print(item)

	def execute(self, string, iterable=None):
		if iterable:
			self.c.execute(string, iterable)
		else:
			self.c.execute(string)

	def fetchall(self):
		return self.c.fetchall()
