import sqlite3

connection = sqlite3.connect('testdb.db')
cursor = connection.cursor()
# cursor.execute('CREATE TABLE User(name TEST, age INT);')
name = 'segun'
age = 43
cursor.execute("INSERT INTO User VALUES(?,?)", (name, age))
cursor.execute('SELECT * FROM User')
print(cursor.fetchall())
connection.commit()
connection.close()

