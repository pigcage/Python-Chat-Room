import socket
import struct
import hashlib
import base64
import threading,random
#import MySQLdb

connectionlist = {}

#For correct userName-password return true, otherwise return false.
def sql_checkLogin(userName,password):
    #return True #Login test, delete this line later
    sqlConn = MySQLdb.connect(host='120.24.36.216',user='root',passwd='75968410cb',db='test',charset='utf8')
    sql="select * from CR_userAccess where userName = '" + userName + "' AND password = '" + password + "';"
    cur = sqlConn.cursor()
    cur.execute(sql)
    result = cur.fetchall()
    if result:
        return True
    else:
        return False

def sendConfirm(self,data):
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
    self.send(data)
    self.close()
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
        loginData = raw_str.split(",")
        if sql_checkLogin(loginData[0],loginData[1]):
            sendConfirm(self,1)
            print 'Login success,break connection.'
            self.close()
        else:
            sendConfirm(self,0)
            print "Login faild,incorrect password or userName doesn't exist,break connection."
            self.close()

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
                print 'User%s Start Handshaken with %s!' % (self.index,self.remote)
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
                    print 'User%s Handshaken with %s success!' % (self.index,self.remote)
                    recvMessage(self.conn,1024)#receive access message from client as a string like "userName,password"
            else:
                continue

class WebSocketServer(object):
    def __init__(self):
        self.socket = None
    def begin(self):
        print 'LoginServer Start!'
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(("127.0.0.1",1236))
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