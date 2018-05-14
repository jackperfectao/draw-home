import MySQLdb
import time
def connect():
    conn = MySQLdb.connect(user="root",passwd="1",host="localhost",db="yingtest")
    return conn
c = connect()
def restart():
    global c
    last = time.time()
    while True :
        time.sleep(1)
        Now = time.time()
        if Now - last > 10 :
            last = Now
    try:
        c.ping()
    except:
        print('now restart')
        c = connect()
        run()
def run():
    try:
        cursor=c.cursor()
        cursor.execute( "SELECT id,detail FROM note where id>1" )
    except Exception,e:
        print'no,it is wrong!'
    print "Rows selected:", cursor.rowcount
    print cursor.fetchall()
    for row in cursor.fetchall():
        print "note : ", row[0], row[1]
        cursor.close()
connect() run() restart()