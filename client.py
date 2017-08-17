import _thread
import socket
from threading import Lock

class Client:
	def __init__(self, ip, port, s_ip, s_port, nick):
		self.ip = ip
		self.port = port
		self.s_ip = s_ip
		self.s_port = s_port
		self.recv_buffer = []
		self.buffer_mutex = Lock()
		self.display_mutex = Lock()

		self.nick = nick

		self.host_at(s_ip, s_port)
		_thread.start_new_thread(self.output, ())

	def run(self):
		self.running = True
		while self.running:
			input()
			self.display_mutex.acquire()

			msg = str(input("> "))
			if msg == "q":
				self.close()
				break
			elif msg == "":
				pass
			else:
				self.parse(msg)

			self.display_mutex.release()

	def parse(self, msg):
		if len(msg) > 0:
			if msg[0] == "/":
				try:
					cmd = msg[1:msg.index(" ")]
					body = msg[msg.index(" ") + 1:]
				except ValueError:
					cmd = msg[1:]
					body = ""

				if cmd == "pm":
					self.parsePM2(body)
				elif cmd == "nick":
					self.parseNIC(body)
				elif cmd == "help":
					self.parseHELP(body)
				else:
					self.parseCMD(cmd, body)
			else:
				self.send("MSG:" + msg)

	def parsePM2(self, msg):
		try:
			nick = msg[0:msg.index(" ")]
			body = msg[msg.index(" ") + 1:]
			self.send("PM2:" + nick + ":" + body)
		except ValueError:
			self.print("Error! Usage: /pm <nick> <message>")

	def parseNIC(self, msg):
		if len(msg) == 0:
			self.print("Error! Usage: /nick <nick>")
		else:
			self.send("NIC:" + msg)

	def parseHELP(self, msg):
		print("Possible commands: /help, /pm, /nick")
		print("Note that the server may support other commands")
		print("You can find out by doing /shelp")

	def parseCMD(self, cmd, data):
		if len(data) > 0:
			self.send("CMD:" + cmd + ":" + data)
		else:
			self.send("CMD:" + cmd)

	def close(self):
		self.send("QIT:Quitting")
		self.sock.close()
		self.running = False

	def host_at(self, s_ip, s_port):
		self.s_ip = s_ip
		self.s_port = s_port
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.sock.bind((self.ip, self.port))
		_thread.start_new_thread(self.recv, ())
		self.send("CON:" + self.nick)

	def recv(self):
		while True:
			if self.sock != None:
				packet = self.sock.recvfrom(1024)
				if packet[1][0] == self.s_ip and packet[1][1] == self.s_port:
					self.handle(str(packet[0].decode("utf-8")))

	def output(self):
		while True:
			self.display_mutex.acquire()
			self.buffer_mutex.acquire()
			if len(self.recv_buffer) > 0:
				print(self.recv_buffer[0])
				self.recv_buffer.pop(0)
			self.buffer_mutex.release()
			self.display_mutex.release()

	def handle(self, msg):
		# Find the first message components
		code = ""
		body = ""

		if len(msg) >= 3:
			code = msg[0:3]
			if len(msg) >= 4:
				body = msg[4:]

		if code == "KAL":
			self.send("KAL")
		elif code == "NIC":
			self.handleNIC(body)
		elif code == "MSG":
			self.handleMSG(body)
		elif code == "PM2":
			self.handlePM2(body)
		elif code == "TXT":
			self.handleTXT(body)
		elif code == "RES":
			self.handleRES(body)
		elif code == "JON":
			self.handleJON(body)
		elif code == "LEV":
			self.handleLEV(body)
		elif code == "NCH":
			self.handleNCH(body)
		elif code == "TOP":
			self.handleTOP(body)
		elif code == "KIC":
			self.handleKIC(body)
		elif code == "DIE":
			self.handleDIE(body)

	def handleKAL(self):
		self.send("KAL")

	def handleNIC(self, msg):
		self.nick = msg

	def handleMSG(self, msg):
		try:
			nick = msg[0:msg.index(":")]
			body = msg[msg.index(":") + 1:]
		except ValueError:
			return

		self.print(nick + " : " + body)

	def handlePM2(self, msg):
		try:
			nick = msg[0:msg.index(":")]
			body = msg[msg.index(":") + 1:]
		except ValueError:
			return
		self.print("(private) " + nick + " : " + body)

	def handleTXT(self, msg):
		self.print(msg)

	def handleRES(self, msg):
		pass # Stub

	def handleJON(self, msg):
		self.print(msg + " joined the chat")

	def handleLEV(self, msg):
		try:
			nick = msg[0:msg.index(":")]
			reason = msg[msg.index(":") + 1:]
		except ValueError:
			return
		self.print(msg + " left the chat (" + reason + ")")

	def handleNCH(self, msg):
		try:
			old = msg[0:msg.index(":")]
			new = msg[msg.index(":") + 1:]
		except ValueError:
			return
		self.print(old + " is now known as " + new)

	def handleTOP(self, msg):
		try:
			nick = msg[0:msg.index(":")]
			topic = msg[msg.index(":") + 1:]
		except ValueError:
			return

		if len(nick) == 0:
			self.print("Topic: " + topic)
		else:
			self.print(nick + " changed the topic to " + topic)

	def handleKIC(self, msg):
		self.print("You have been kicked from the server : " + msg)

	def handleDIE(self, msg):
		self.print("The server has shut down : ", reason)

	def print(self, msg):
		self.buffer_mutex.acquire()
		self.recv_buffer.append(msg)
		self.buffer_mutex.release()

	def send(self, msg):
		if self.sock != None:
			self.sock.sendto(str.encode(msg), (self.s_ip, self.s_port))

if __name__ == "__main__":
	ip = str(input("Enter your local IP: "))
	port = int(input("Enter your local port: "))
	s_ip = str(input("Enter the server IP: "))
	s_port = int(input("Enter the server port: "))
	nick = str(input("Enter your nickname: "))
	print("Starting client... Press <return> to start talking, and type 'q' to quit.")
	client = Client(ip, port, s_ip, s_port, nick)
	client.run()