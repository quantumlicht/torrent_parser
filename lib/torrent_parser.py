import re
import string
from datetime import datetime
import time
import pprint

INT_PATTERN = re.compile("(^-?\d+)e?(.*)")
STR_PATTERN = re.compile("^(\d+):(.*)")
PIECES_KEY = 'pieces'
CREATION_DATE_KEY = 'creation date'

pp = pprint.PrettyPrinter(indent=3)
class Printer():
	def __init__(self, debug = False):
		self.debug_mode = debug

	def debug(self, to_print):
		if self.debug_mode:
			print to_print

	def error(self, to_print):
		print '===ERROR [{0}]=='.format(to_print)

class TorrentParser():
	def __init__(self, filename=None, debug_mode=False):
		self.log = Printer(debug=debug_mode)
		self.cur = 0
		self.return_val = None
		self.filename = None
		self.data = None
		if filename is not None:
			self.filename = filename
			self.readfile(filename)

	#===================================================================================================================
	# PUBLIC METHODS
	#===================================================================================================================

	def readfile(self, filename=None):
		ret = None
		if filename is None:
			filename = self.filename
		if filename is None:
			raise Exception("You need to provide specify an input file either in the readfile method or in the"
			                "constructor.You can also read a bencoded string with the decode method")
		with open(filename, 'rb') as f:
			ret = f.read()
		self.data = ret

	def decode(self, data=None):
		self.cur = 0

		if data is not None:
			self.data = data
		try:
			(data_type, method) = self._get_data_type()
			self.return_val = method(data_type)
			self._build_file_hashes()
			self._build_creation_date()

			self.log.debug(self.return_val)
			return self.return_val
		except ValueError as e:
			self.log.error("Uncaught Error {0}".format(e))

		return self.return_val

	# print self.result
	# return self.result

	#===================================================================================================================
	# DEBUG UTIL METHODS
	#===================================================================================================================

	def _show_ahead(self, ahead=60):
		show = ''
		if self.cur > len(self.data):
			return show
		for i in self.data[self.cur:self.cur + ahead]:
			show += i
		print 'show_ahead {0}'.format(show)

	#===================================================================================================================
	# PRIVATE METHODS
	#===================================================================================================================
	def _build_creation_date(self):
		try:
			creation_date = self.return_val.get('creation date')
			date_string = "{0} ({1})".format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(creation_date))),creation_date)
			self.return_val['creation date'] = date_string
		except AttributeError:
			self.log.error("The input provided does not comply with the bittorent metainfo specification. No creation date specified")

	def _build_file_hashes(self):
		try:
			info = self.return_val.get('info', None)
			if info is not None:
				piece_length = info.get('piece length', 262144) # 262144 bytes is the default piece size for Version > 3.2
				files = info.get('files', None)
				length = info.get('length', None)

				if files is not None and length is not None:
					raise Exception("Meta info does not follow protocol rules. You must specify only one of files(multi file)"
					                "or length(single file) keys")
				elif files is None and length is None:
					raise Exception("Meta info does not follow protocol rules. You must specify one of files(multi file)"
					                "or length(single file) keys")

				pieces = (info.get('pieces')).encode('hex')
				pos = 0

				if length:
					#We have a single file torrent
					pieces_hash = []
					while pos < len(pieces):
						pieces_hash.append(pieces[pos:pos + 20])
						pos += 20

					self.return_val['info']['file_pieces_sha1'] = pieces_hash
				elif files:
					rebuilt_files = []
					# We have many files
					for file in files:
						nb_pieces = file.get('length') / piece_length
						nb_pieces = 1 if nb_pieces == 0 else nb_pieces
						pieces_hash = []
						for piece in xrange(0, nb_pieces):
							pieces_hash.append(pieces[pos:pos + 20])
							pos += 20
						file['file_pieces_sha1'] = pieces_hash

						rebuilt_files.append(file)
					self.return_val['info']['files'] = rebuilt_files
				del self.return_val['info']['pieces']
		except AttributeError:
			print "The input provided does not comply with the bittorent metainfo specification. No info dictionary specified"

	def _read(self, pattern):
		# self._show_ahead()
		# print "_read pattern {0}".format(pattern.pattern)
		match = re.match(pattern, self.data[self.cur:])
		# print "_read groups {0}".format(match.groups())
		# print "_read span {0}, {1}".format(match.span(1), match.span(2))
		# print "_read group(1) {0}".format(int(match.group(1)))
		self.cur += match.span(2)[0]
		item = self.data[self.cur: self.cur + int(match.group(1))]
		self.cur += int(match.group(1))
		# print "_read item {0}".format(item)
		return item

	def _get_data_type(self):
		# self._show_ahead()
		if self.cur > len(self.data) - 1:
			return None, None
		type_code = self.data[self.cur]

		if type_code == 'l':
			self.cur += 1
			return 'l', self._read_arr
		elif type_code == 'd':
			self.cur += 1
			return 'd', self._read_arr
		elif type_code == 'i':
			self.cur += 1
			return int, self._read_int
		elif type_code == 'e':
			self.cur += 1
			return None, None
		elif type_code in string.digits:
			return str, self._read_string
		else:
			raise ValueError("The data provided cannot be interpreted as bencoding")

	def _read_arr(self, struct_type):
		container = list()
		data_type, method = self._get_data_type()
		inner_type = data_type
		while inner_type is not None:
			val = method(inner_type)
			container.append(val)
			inner_type, method = self._get_data_type()
		if struct_type == 'l':
			return container
		elif struct_type == 'd':
			return {i: j for i, j in zip(container[::2], container[1::2])}

	def _read_int(self, integer):
		match = re.match(INT_PATTERN, self.data[self.cur:])
		val = match.group(1)
		self.log.debug("_read_int {0}".format(val))
		self.cur += match.span(2)[0]
		return int(val)

	def _read_pieces(self):
		match = re.match(STR_PATTERN, self.data[self.cur:])
		str_length = int(match.group(1))
		self.log.debug("_read_pieces str_length {0}".format(str_length))
		self.cur += match.span(2)[0]  # move cursor past the actual length string

		if str_length % 20 != 0:
			raise Exception("Malformed pieces segment. It should be a multiple of 20")

		self.str_pieces = (self.data[self.cur: self.cur + int(match.group(1))]).encode('hex')
		self.cur += str_length

		self._show_ahead()
		hashes = []
		pos = 0
		hash_string = self.str_pieces.encode('hex')
		self.log.debug("number of hash string {1} {0}".format(len(hash_string) / 20, len(hash_string)))
		while pos < len(hash_string):
			hashes.append(hash_string[pos:pos + 20])
			pos += 20
		return self.str_pieces

	def _read_string(self, str):
		match = re.match(STR_PATTERN, self.data[self.cur:])
		str_length = int(match.group(1))
		self.cur += match.span(2)[0]  # move cursor past the actual length string

		str_val = self.data[self.cur: self.cur + int(match.group(1))]
		self.cur += str_length

		self.log.debug("_read_string {0}".format(str_val))
		return str_val