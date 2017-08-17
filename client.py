import _thread
import socket
from threading import Lock
from sys import platform
import os

if platform == "linux" or platform == "linux2":
	import os
elif platform == "win32":
	import winsound

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
		self.do_beep = True

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
				elif cmd == "beep":
					self.do_beep = not self.do_beep
					if self.do_beep:
						self.print("Beep enabled")
					else:
						self.print("Beep disabled")
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
		print("Possible commands: /help, /pm, /nick, /beep")
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
		self.beep()

	def handleMSG(self, msg):
		try:
			nick = msg[0:msg.index(":")]
			body = msg[msg.index(":") + 1:]
		except ValueError:
			return

		self.print(nick + " : " + body)
		self.beep()

	def handlePM2(self, msg):
		try:
			nick = msg[0:msg.index(":")]
			body = msg[msg.index(":") + 1:]
		except ValueError:
			return
		self.print("(private) " + nick + " : " + body)
		self.beep()

	def handleTXT(self, msg):
		self.print(msg)

	def handleRES(self, msg):
		if msg == "USED_NIC":
			self.print("Error: Nickname already in use!")
		elif msg == "BAD_NICK":
			self.print("Error: Nickname is invalid!")

	def handleJON(self, msg):
		self.print(msg + " joined the chat")

	def handleLEV(self, msg):
		try:
			nick = msg[0:msg.index(":")]
			reason = msg[msg.index(":") + 1:]
		except ValueError:
			return
		self.print(nick + " left the chat (" + reason + ")")

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
		self.beep()

	def handleKIC(self, msg):
		self.print("You have been kicked from the server : " + msg)
		self.beep()

	def handleDIE(self, msg):
		self.print("The server has shut down : ", reason)
		self.beep()

	def print(self, msg):
		self.buffer_mutex.acquire()
		self.recv_buffer.append(msg)
		self.buffer_mutex.release()

	def beep(self):
		if self.do_beep:
			if platform == "linux" or platform == "linux2":
				os.system("play --no-show-progress --null --channels 1 synth 0.2 sine 1000")
			elif platform == "win32":
				winsound.Beep(1000, 200)

	def send(self, msg):
		if self.sock != None:
			self.sock.sendto(str.encode(msg), (self.s_ip, self.s_port))

CFG_FILE = "client.cfg"

if __name__ == "__main__":

	read = False
	if os.path.isfile(CFG_FILE):
		y = str(input("Configuration file found. Type 'y' to load: ")).lower()
		if y == "y":
			cfg = open(CFG_FILE, "r")
			read = True
			for line in cfg.readlines():
				if line[0:3] == "ip:":
					ip = line[3:].strip()
				elif line[0:5] == "port:":
					port = int(line[5:].strip())
				if line[0:4] == "sip:":
					s_ip = line[4:].strip()
				if line[0:6] == "sport:":
					s_port = int(line[6:].strip())
				if line[0:5] == "nick:":
					nick = line[5:].strip()
			cfg.close()
			print("Using ip = " + ip)
			print("Using port = " + str(port))
			print("Using s_ip = " + s_ip)
			print("Using s_port = " + str(s_port))
			print("Using nick = " + nick)

	if not read:
		ip = str(input("Enter your local IP: "))
		port = int(input("Enter your local port: "))
		s_ip = str(input("Enter the server IP: "))
		s_port = int(input("Enter the server port: "))
		nick = str(input("Enter your nickname: "))

		y = str(input("Type 'y' to save configuration: ")).lower()
		if y == "y":
			cfg = open(CFG_FILE, "w")
			cfg.write("ip:" + ip + "\n")
			cfg.write("port:" + str(port) + "\n")
			cfg.write("sip:" + s_ip + "\n")
			cfg.write("sport:" + str(s_port) + "\n")
			cfg.write("nick:" + nick + "\n")
			cfg.close()

	print("Starting client... Press <return> to start talking, and type 'q' to quit.")
	client = Client(ip, port, s_ip, s_port, nick)
	client.run()
