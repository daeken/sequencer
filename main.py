from time import *
from pyaudio import *
from launchpad import Launchpad

class Sequencer(object):
	def __init__(self):
		self.audio = PyAudio()

		self.page = 0
		self.samples = [None] * 8
		self.sampleI = 0
		self.playing = False
		self.playingPage = 0
		self.playingCol = 0
		self.pages = [[[0] * 8 for i in xrange(8)] for i in xrange(8)]

		self.padPlayMode = False
		self.recordMode = False
		self.recording = None

		self.showBPM = False
		self.bpm = 240
		self.bpmPressed = False
		self.bpmTimePressed = None

		self.dev = Launchpad()
		self.dev.handler = self.handler
		self.setLight = self.dev.setLight

		self.repaint()

		bpmState = True
		while True:
			if self.showBPM:
				since = clock() - self.bpmTimePressed
				if since >= 2 and not self.bpmPressed:
					self.showBPM = False
					self.setLight(4, 0, False, self.page == 4)
				else:
					per = 0.5 / self.bpm * 60
					since %= per * 2
					if since < per:
						if bpmState == True:
							self.setLight(4, 0, True, False)
							bpmState = False
							sleep(per / 2.0)
					elif bpmState == False:
						self.setLight(4, 0, False, self.page == 4)
						bpmState = True
						sleep(per / 2.0)
			else:
				sleep(0.5)

	def handler(self, dev, x, y, evt):
		if y == 0:
			if (evt and x not in (4, 5)) or (self.recordMode and x != 6):
				return
			if x == 2: # left page
				self.page = (self.page + 8 - 1) % 8
				self.repaint()
			elif x == 3: # right page
				self.page = (self.page + 1) % 8
				self.repaint()
			elif x == 4 or x == 5: # decrease/increase bpm
				if evt:
					self.bpmPressed = True
					self.showBPM = True
					self.bpmTimePressed = clock()
					self.modBPM = -1 if x == 4 else +1
				else:
					self.bpmPressed = False
					self.bpmTimePressed = clock()
					self.modBPM = None
			elif x == 6: # toggle record mode
				if self.recordMode == 2:
					self.stopRecording()
					self.recordMode = False
				else:
					self.recordMode = 1 if self.recordMode == False else False
				self.setLight(6, 0, self.recordMode == 1, False)
			elif x == 7: # toggle pad play mode
				self.padPlayMode = not self.padPlayMode
				self.setLight(7, 0, False, self.padPlayMode)
		elif x == 8:
			pass
		else:
			if evt: return

			if self.padPlayMode: # just play the sample for this row
				pass
			elif self.recordMode == 1: # recording for that row
				self.recordMode = 2
				self.record(y-1)
				self.setLight(6, 0, True, True)
				for i in xrange(8):
					self.setLight(i, y, True, self.pages[self.page][i][y-1])
			elif self.recordMode == 2: # end recording
				if y - 1 != self.recording:
					return
				self.stopRecording()
			else:
				page = self.pages[self.page]
				page[x][y-1] = not page[x][y-1]
				self.setLight(x, y, False, page[x][y-1])

	def record(self, row):
		self.recording = row
		self.recordingSample = ''
		self.input = self.audio.open(format=paInt16, channels=1, rate=44100, input=True, frames_per_buffer=441, stream_callback=self.gotSample) # 1/100th second per buffer

	def gotSample(self, data, frame_count, time_info, status):
		pass#self.recordingSample += data
		print 'foo?'

	def stopRecording(self):
		print len(self.recordingSample) / 2 / 44100.0
		self.input.stop_stream()
		self.input.close()

		self.setLight(6, 0, False, False)
		for i in xrange(8):
			self.setLight(i, self.recording+1, False, self.pages[self.page][i][self.recording])
		self.recordMode = False
		self.recording = None

	def setStatusLights(self):
		for i in xrange(8):
			self.setLight(i, 0, False, False)
			self.setLight(8, i+1, False, False)
		self.setLight(self.page, 0, self.playing and self.playingPage == self.page and self.playingCol == self.page, True)
		if self.playingPage == self.page and self.playingCol != self.page:
			self.setLight(self.playingCol, 0, True, False)

		if self.padPlayMode:
			self.setLight(7, 0, False, True)

	def repaint(self):
		self.dev.clear()
		self.setStatusLights()
		for x, row in enumerate(self.pages[self.page]):
			for y, val in enumerate(row):
				if val or x == self.recording:
					self.setLight(x, y+1, self.recording == x, True)

Sequencer()
