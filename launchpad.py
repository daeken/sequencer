import usb.core
from usb.core import *
from usb.util import *
from thread import start_new_thread
import atexit

class Launchpad(object):
	def __init__(self):
		self.dev = find(idVendor=0x1235)
		self.dev.set_configuration()

		self.queue = []
		self.handler = None
		start_new_thread(self.reader, ())

		self.clear()
		atexit.register(self.clear)

	def write(self, *data):
		self.dev.write(2, ''.join(map(chr, data)), 0)

	def reader(self):
		while True:
			try:
				data = self.dev.read(0x81, 8)
			except KeyboardInterrupt:
				break
			except usb.core.USBError, e:
				if e.errno == 60: # timeout
					continue
				import traceback
				traceback.print_exc()
				break

			while len(data) >= 2:
				mod = False
				if data[0] in (176, 144):
					mod = data[0] == 176
					data = data[1:]
				elif len(data) & 1:
					print data
					break
				x, y = data[0] & 0x0F, (data[0] >> 4) + 1
				if y == 7 and x >= 8:
					if x != 8 or mod:
						y = 0
						x -= 8
				evt = data[1] == 127
				if self.handler:
					self.handler(self, x, y, evt)
				else:
					self.queue.append((x, y, evt))
				data = data[2:]

	def clear(self):
		self.write(176, 0, 0)
		self.write(176, 0, 32)
		self.front = None

	def doublebuffer(self, enable=True):
		if enable:
			self.write(176, 0, (1 << 5) | (0 << 2) | 1)
			self.front = 0
		else:
			self.write(176, 0, 32)
			self.front = None

	def swap(self):
		if self.front != None:
			self.front = 1 - self.front
			self.write(176, 0, (1 << 5) | (1 << 4) | (self.front << 2) | (1 - self.front))

	def setLight(self, x, y, red, green):
		if red == True:
			red = 3
		elif red == False:
			red = 0
		if green == True:
			green = 3
		elif green == False:
			green = 0
		
		if y == 0:
			self.write(176, 104 + x, (green << 4) | red)
		else:
			self.write(144, x + (y - 1) * 16, (green << 4) | red)
