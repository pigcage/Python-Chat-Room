import socket
import struct
import hashlib
import base64
import threading,random
import json
import MySQLdb

connectionlist = {}

#return online members and amount as a tuple: (user1,user2,...)
def sql_onlineList():
    sqlConn = MySQLdb.connect(host='184.170.213.206',user='root',passwd='',db='pythonchatroom',charset='utf8')
    sql="select * from CR_onlineList;"
    cur = sqlConn.cursor()
    cur.execute(sql)
    result = cur.fetchall()
    cur.close()
    sqlConn.close()
    return result

#add new member to online list
def sql_addToList(name):
    sqlConn = MySQLdb.connect(host='184.170.213.206',user='root',passwd='',db='pythonchatroom',charset='utf8')
    sql="insert into CR_onlineList values ('" + name + "');"
    cur = sqlConn.cursor()
    cur.execute(sql)
    cur.close()
    sqlConn.close()

#remove offline members
def sql_removeFromList(name):
    sqlConn = MySQLdb.connect(host='184.170.213.206',user='root',passwd='',db='pythonchatroom',charset='utf8')
    sql="delete from CR_onlineList where name = '" + name + "';"
    cur = sqlConn.cursor()
    cur.execute(sql)
    cur.close()
    sqlConn.close()


def sendMessage(data):
    if data:
        data = str(data)
    else:
        return False
    token = "\x81"
    length = len(data)
    if length<126:
        token += struct.pack("B",length)
    elif length <= 0xFFFF:
        token += struct.pack("!BH",126,length)
    else:
        token += struct.pack("!BQ",127,length)
    data = "%s%s" % (token,data)
    global connectionlist
    for connection in connectionlist.values():
        connection.send(data)	
    return True

def recvMessage(self,num):
    try:
        all_data = self.recv(num)
        if not len(all_data):
            return False
    except:
        return False
    else:
        masks = []
        data = []
        code_len = ord(all_data[1]) & 127
        if code_len == 126:
            masks = all_data[4:8]
            data = all_data[8:]
        elif code_len == 127:
            masks = all_Data[10:14]
            data = all_data[14:]
        else:
            masks = all_data[2:6]
            data = all_data[6:]
        raw_str = ""
        i = 0
        for d in data :
            raw_str += chr(ord(d)^ord(masks[i%4]))
            i += 1
        return raw_str

def deleteconnection(item):
    global connectionlist
    del connectionlist['connection'+item]
     
class WebSocket(threading.Thread):
    def __init__(self,conn,index,name,remote, path="/"):
        threading.Thread.__init__(self)
        self.conn = conn
        self.index = index
        self.name = name
        self.remote = remote
        self.path = path
        self.buffer = ""
         
    def run(self):
        print 'Socket%s Start!' % self.index
        headers = {}
        self.handshaken = False
 
        while True:
            if self.handshaken == False:
                print 'Socket%s Start Handshaken with %s!' % (self.index,self.remote)
                self.buffer += self.conn.recv(1024)
                if self.buffer.find('\r\n\r\n') != -1:
                    header, data = self.buffer.split('\r\n\r\n', 1)
                    for line in header.split("\r\n")[1:]:
                        key, value = line.split(": ", 1)
                        headers[key] = value
                    headers["Location"] = "ws://%s%s" %(headers["Host"], self.path)
                    key1 = headers["Sec-WebSocket-Key"]
                    key1 = key1 + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
                    token = base64.b64encode(hashlib.sha1(key1).digest())
                    handshake = '\
HTTP/1.1 101 Switching Protocols\r\n\
Upgrade: websocket\r\n\
Connection: Upgrade\r\n\
Sec-WebSocket-Accept:%s\r\n\
WebSocket-Origin: %s\r\n\
WebSocket-Location: %s\r\n\r\n\
' %(token, headers['Origin'], headers['Location'])
                    self.conn.send(handshake)
                    self.handshaken = True
                    print 'Socket%s Handshaken with %s success!' % (self.index,self.remote)
                    #online informations
                    userName = recvMessage(self.conn,1024)
                    sendMessage('LoginInfo,%s' % userName)
                    sql_addToList(userName)
                    sendMessage('onlineList,%s' % str(sql_onlineList()))
            else:
                s = recvMessage(self.conn,1024).split(",")
                if s[0]=='**quit**':
                    sendMessage('quitInfo,%s' % (s[1]))
                    sql_removeFromList(s[1])
                    sendMessage('onlineList,%s' % str(sql_onlineList()))
                    deleteconnection(str(self.index))
                    self.conn.close()
                    break
                else:
                    msg = ''
                    for i in s[2::]:
                        msg = msg + i + ','
                    sendMessage('newMessage,' + s[1]+','+msg)

class WebSocketServer(object):
    def __init__(self):
        self.socket = None
    def begin(self):
        print 'WebSocketServer Start!'
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(("184.170.213.206",1237))
        self.socket.listen(50)
         
        global connectionlist

        i=0
        while True:

            connection, address = self.socket.accept()
            username=address[0]
            newSocket = WebSocket(connection,i,username,address)
            newSocket.start()
            connectionlist['connection'+str(i)]=connection
            i = i + 1
 
if __name__ == "__main__":
    server = WebSocketServer()
    server.begin()
