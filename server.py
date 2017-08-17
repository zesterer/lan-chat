import _thread
import socket
import random
import datetime
import time

PRIV_NONE = 0
PRIV_USER = 1
PRIV_ADMIN = 2

TIMEOUT = 60

def valid_nick(nick): # Stub
	return True

class Client:
	def __init__(self, ip, port, nick):
		self.ip = ip
		self.port = port
		self.nick = nick
		self.priv = PRIV_NONE
		self.timeout = None
		self.update_timeout()

	def update_timeout(self):
		self.timeout = datetime.datetime.now()

class Server:
	def __init__(self, ip, port):
		self.clients = []
		self.ip = None
		self.port = None
		self.sock = None

		self.topic = "Welcome to the server. Type /help for more info."

		self.host_at(ip, port)
		_thread.start_new_thread(self.watch, ())

	def watch(self):
		while True:
			if self.sock != None:
				now = datetime.datetime.now()
				for c in self.clients:
					if (now - c.timeout).total_seconds() > TIMEOUT / 2:
						self.send(c, "KAL")
						if (now - c.timeout).total_seconds() > TIMEOUT:
							for oc in self.clients:
								self.send(oc, "LEV:" + c.nick + ":Timeout")
							self.clients.remove(c)
				time.sleep(1)

	def host_at(self, ip, port):
		self.ip = ip
		self.port = port
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.sock.bind((self.ip, self.port))
		_thread.start_new_thread(self.recv, ())

	def close(self):
		for c in self.clients:
			self.send(c, "DIE:Server is closed")
		self.sock.close()

	def recv(self):
		while True:
			if self.sock != None:
				self.handle(self.sock.recvfrom(4096))

	def handle(self, packet):
		# Find the packet details
		ip = packet[1][0]
		port = packet[1][1]
		msg = str(packet[0].decode("utf-8"))

		print(datetime.datetime.now().strftime("[%H:%M:%S] Received : ") + msg)

		# Find the client
		client = None
		for c in self.clients:
			if c.ip == ip and c.port == port:
				client = c

		if client != None:
			client.update_timeout()

		# Find the first message components
		code = ""
		body = ""

		if len(msg) >= 3:
			code = msg[0:3]
			if len(msg) >= 4:
				body = msg[4:]

		if code == "KAL": # It's a keep-alive message
			self.handleKAL(client)
		elif code == "CON":
			self.handleCON(client, body, ip, port)
		elif code == "NIC":
			self.handleNIC(client, body)
		elif code == "MSG":
			self.handleMSG(client, body)
		elif code == "PM2":
			self.handlePM2(client, body)
		elif code == "CMD":
			self.handleCMD(client, body)
		elif code == "QIT":
			self.handleQIT(client, body)

	def handleKAL(self, client):
		if client != None:
			pass

	def handleCON(self, client, msg, ip, port):
		if client == None:
			if valid_nick(msg):
				nclient = Client(ip, port, msg)
				self.clients.append(nclient)
				self.send(nclient, "TOP::" + self.topic)
				for c in self.clients:
					self.send(c, "JON:" + msg)
		else:
			client.update_timeout()

	def handleNIC(self, client, msg):
		if client != None:
			if valid_nick(msg):
				failed = False
				for c in self.clients:
					if c.nick == msg:
						failed = True
				if failed:
					self.send(client, "RES:USED_NIC")
				else:
					for c in self.clients:
						self.send(c, "NCH:" + client.nick + ":" + msg)
					client.nick = msg
			else:
				self.send(client, "RES:BAD_NICK")

	def handleMSG(self, client, msg):
		if client != None:
			for c in self.clients:
				self.send(c, "MSG:" + client.nick + ":" + msg)

	def handlePM2(self, client, msg):
		if client != None:
			try:
				tgt = msg[0:msg.index(":")]
				body = msg[msg.index(":") + 1:]
			except ValueError:
				return

			for c in self.clients:
				if c.nick == tgt:
					self.send(c, "PM2:" + client.nick + ":" + body)
					self.send(client, "PM2:" + client.nick + ":" + body)
					break

	def handleCMD(self, client, msg):
		if client != None:
			try:
				cmd = msg[0:msg.index(":")]
				body = msg[msg.index(":") + 1:]
			except ValueError:
				cmd = msg
				body = ""

			if cmd == "shelp":
				self.send(client, "TXT:The server support several commands such as:")
				self.send(client, "TXT:/list ---- List users on the server")
				self.send(client, "TXT:/ping ---- Ping the server")
				self.send(client, "TXT:/info ---- See server info")
				self.send(client, "TXT:/topic---- See the server topic")
				self.send(client, "TXT:/settopic- Set the server topic")
			elif cmd == "list":
				self.send(client, "TXT:There are " + str(len(self.clients)) + " people on this server:")
				for c in self.clients:
					self.send(client, "TXT:" + c.nick)
			elif cmd == "ping":
				self.send(client, "TXT:pong!")
			elif cmd == "info":
				self.send(client, "TXT:Server Info:")
				self.send(client, "TXT:Address is " + self.ip + ":" + str(self.port))
			elif cmd == "topic":
				self.send(client, "TXT:The topic is: " + self.topic)
			elif cmd == "settopic":
				self.topic = body
				for c in self.clients:
					self.send(c, "TOP:" + client.nick + ":" + self.topic)

	def handleQIT(self, client, msg):
		if client != None:
			for c in self.clients:
				self.send(c, "LEV:" + client.nick + ":" + msg)
			self.clients.remove(client)

	def send(self, client, msg):
		if self.sock != None:
			self.sock.sendto(str.encode(msg), (client.ip, client.port))
		print(datetime.datetime.now().strftime("[%H:%M:%S] Sent : ") + msg)

if __name__ == "__main__":
    ip = str(input("What IP should the server host on? "))
    port = int(input("What port should the server host on? "))
    server = Server(ip, port)

    # Wait for input
    input("Press <return> to quit\n")
    server.close()
