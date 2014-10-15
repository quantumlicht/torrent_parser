
import os
import re
import string

INT_PATTERN = re.compile("(^-?\d+)?e(.*)")
STR_PATTERN = re.compile("^(\d+):(.*)")
test = 'd' \
          '8:announce' '35:udp://tracker.openbittorrent.com:80' \
          '13:creation date i1327049827e' \
          '4:info' 'd' \
            '6:length' 'i20e' \
            '4:name 10:sample.txt' \
            '12:piece length i65536e' \
            '6:pieces 20:\\\xc5\xe6R\xbe\r\xe6\xf2x\x05\xb3\x04d\xff\x9b\x00\xf4\x89\xf0\xc9' \
            '7:private i1e' \
          'e' \
       'e'
class TorrentParser():
	def __init__(self, filename):

		self.cur = 0
		self.filename = filename
		self.data = self._readfile()

	def _readfile(self):
		ret = None
		with open(self.filename, 'rb') as f:
			ret = f.read()

		return ret

	def _show_ahead(self, ahead = 60):
		show = ''
		if self.cur > len(self.data):
			return show
		for i in self.data[self.cur:self.cur + ahead]:
			show += i
		print 'show_ahead {0}'.format(show)

	def decode(self, data=None):
		self.cur = 0
		if data is not None:
			self.data = data

		try:
			# while self.cur < len(self.data):
			(type, method) = self._get_data_type()
			ret = method(type)
			print "decode ret {0}".format(ret)
			return ret
		except ValueError:
			print "Error"
		# print self.result
		# return self.result

	def _read(self, pattern):
		# self._show_ahead()
		print "_read pattern {0}".format(pattern.pattern)
		match = re.match(pattern, self.data[self.cur:])
		print "_read groups {0}".format(match.groups())
		print "_read span {0}, {1}".format(match.span(1), match.span(2))
		print "_read group(1) {0}".format(int(match.group(1)))
		self.cur += match.span(2)[0]
		item = self.data[self.cur: self.cur + int(match.group(1))]
		self.cur += int(match.group(1))
		print "_read item {0}".format(item)
		return item

	def _read_arr(self, container):
		data_type, method = self._get_data_type()
		while data_type is not None:
			val = method(data_type)
			container.append(val)
			data_type, method = self._get_data_type()

		if isinstance(data_type, list):
			return container
		elif isinstance(data_type, dict):
			return {i:j for i,j in zip(container[::2], container[1::2])}


	def _read_int(self, integer):
		# print "read_int"
		match = re.match(INT_PATTERN, self.data[self.cur:])
		val = match.group(1)
		print val, len(val)
		self.cur += len(val) #+ match.span(2)[0]
		return int(val)
		# return self._read(INT_PATTERN)
		# print "read_int {0}".format(val)

	def _read_string(self, str):
		# print '_read_string'
		return self._read(STR_PATTERN)

	def _get_data_type(self):
		self._show_ahead()
		if self.cur > len(self.data)-1:
			return None , None
		type_code = self.data[self.cur]
		# print "type code {0}".format(type_code)

		if type_code in ['d', 'l']:
			self.cur += 1
			return list(), self._read_arr
		elif type_code == 'i':
			self.cur += 1
			return int, self._read_int
		elif type_code == 'e':
			self.cur += 1
			return None, None
		elif type_code in string.digits:
			return str, self._read_string
		else:
			raise ValueError("Giberrish")