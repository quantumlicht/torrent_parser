import re
import string
import time

INT_PATTERN = re.compile("(^-?\d+)e?(.*)")
STR_PATTERN = re.compile("^(\d+):(.*)")
PIECES_KEY = 'pieces'
CREATION_DATE_KEY = 'creation date'
PROTOCOL_PIECE_LENGTH = 20


class Printer():
	"""
	Small util to print to console
	"""

	def __init__(self, debug=False):
		"""
		:param debug: If we should print debug statements or not
		:return: None
		"""
		self.debug_mode = debug

	def debug(self, to_print):
		if self.debug_mode:
			print '=== DEBUG: [{0}] ==='.format(to_print)

	def error(self, to_print):
		print '=== ERROR: [{0}] ==='.format(to_print)


class TorrentParser():
	"""
	 A class to parse a Bittorrent file to extract the meta info for a torrent
	"""

	def __init__(self, filename=None, debug_mode=False):
		"""
		:param filename: You can specify
		:param debug_mode:
		:return: None
		"""
		self.log = Printer(debug=debug_mode)
		self.cur = 0  # The cursor indicates the position in the file
		self.__return_val = None
		self.filename = None
		self.data = None
		if filename is not None:
			self.filename = filename
			self.readfile(filename)

	# ===================================================================================================================
	# PUBLIC METHODS
	# ===================================================================================================================

	def readfile(self, filename=None):

		"""
		:param filename: the string path to the file we want to parse
		:return: Returns nothing but save the read file into the data attribute
		"""

		if filename is None:
			filename = self.filename
		if filename is None:
			raise ValueError("You need to provide specify an input file either in the readfile method or in the"
			                "constructor.You can also read a bencoded string with the decode method")
		with open(filename, 'rb') as f:
			ret = f.read()
		self.data = ret

	def decode(self, data=None):

		"""
		:param data: if we want to decode a bencoded string instead of a file
		:return: the parsed structure contained into return_val
		"""

		self.cur = 0  # reset the cursor so we can use the parser for as many file as we want

		if data is not None:
			self.data = data
		try:
			(data_type, method) = self.__get_data_type()
			self.__return_val = method(data_type)
			self.__build_file_hashes()
			self.__build_creation_date()

			self.log.debug(self.__return_val)
			return self.__return_val
		except ValueError as e:
			self.log.error("Uncaught Exception: {0}".format(e))

		return self.__return_val

	#===================================================================================================================
	# DEBUG UTIL METHODS
	#===================================================================================================================

	def __show_ahead(self, ahead=60):
		"""
		Small util to see the next character in the file to understand if the file is being parsed correctly
		:param ahead: the distance after the cursor we want to inspect the file content
		:return: nothing, simply prints out the result
		"""
		show = ''
		if self.cur > len(self.data):
			return show
		for i in self.data[self.cur:self.cur + ahead]:
			show += i
		self.log.debug('show_ahead {0}'.format(show))

	#===================================================================================================================
	# PRIVATE METHODS
	#===================================================================================================================
	def __build_creation_date(self):
		"""
		Prettyfies the creation date field in the torrent file
		:return: None
		"""
		try:
			creation_date = self.__return_val.get('creation date', None)
			if creation_date is not None:
				date_string = "{0} ({1})".format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(creation_date))),
				                                 creation_date)
				self.__return_val['creation date'] = date_string
		except AttributeError:
			self.log.error(
				"The input provided does not comply with the bittorent metainfo specification. No creation date specified")

	def __build_file_hashes(self):
		"""
		This interprets the piece length field and calculate the sha1 hash of each pieces.
		For each file in the torrent we associate the file_pieces_sha1 key to an array containing the sha1 hash of each pieces for this file
		:return: None
		"""
		try:
			info = self.__return_val.get('info', None)
			if info is not None:
				piece_length = info.get('piece length',
				                        262144)  # 262144 bytes is the default piece size for Version > 3.2
				files = info.get('files', None)
				length = info.get('length', None)

				if files is not None and length is not None:
					raise AssertionError(
						'Meta info does not follow protocol rules. You must specify only one of "files" (multi file)'
						'or "length" (single file) keys')
				elif files is None and length is None:
					raise AssertionError(
						'Meta info does not follow protocol rules. You must specify one of "files" (multi file)'
						'or "length" (single file) keys')

				pieces = (info.get('pieces')).encode('hex')

				if len(pieces) % PROTOCOL_PIECE_LENGTH != 0:
					raise AssertionError("Malformed pieces segment. It should be a multiple of 20")

				pos = 0
				if length:
					#We have a single file torrent
					pieces_hash = []
					while pos < len(pieces):
						pieces_hash.append(pieces[pos:pos + PROTOCOL_PIECE_LENGTH])
						pos += PROTOCOL_PIECE_LENGTH

					self.__return_val['info']['file_pieces_sha1'] = pieces_hash
				elif files:
					rebuilt_files = []
					# We have many files
					for file_data in files:
						nb_pieces = file_data.get('length') / piece_length
						nb_pieces = 1 if nb_pieces == 0 else nb_pieces # make sure we always have at least one piece
						pieces_hash = []
						for piece in xrange(0, nb_pieces):
							pieces_hash.append(pieces[pos:pos + PROTOCOL_PIECE_LENGTH])
							pos += PROTOCOL_PIECE_LENGTH
						file_data['file_pieces_sha1'] = pieces_hash

						rebuilt_files.append(file_data)
					self.__return_val['info']['files'] = rebuilt_files
				del self.__return_val['info']['pieces']
		except AttributeError:
			self.log.error("The input provided does not comply with the bittorent metainfo specification. No info dictionary specified")

	def __get_data_type(self):
		"""
		We parse the torrent file to determine its structure
		:return: None
		"""
		if self.cur > len(self.data) - 1:
			return None, None
		type_code = self.data[self.cur]

		if type_code == 'l':  # l means its a list. it's closed by the character e
			self.cur += 1
			return 'l', self.__read_arr
		elif type_code == 'd':  # d means its a list. it's closed by the character e
			self.cur += 1
			return 'd', self.__read_arr
		elif type_code == 'i':  # l means its an integer. it's closed by the character e, can also accept negative numbers
			self.cur += 1
			return int, self.__read_int
		elif type_code == 'e':  # end of a sequence
			self.cur += 1
			return 'e', None
		elif type_code in string.digits:  # if we encounter a digit, this means we are reading a string
			return str, self.__read_string
		else:
			raise ValueError("The data provided cannot be interpreted as bencoding")

	def __read_arr(self, struct_type):
		"""
		method that is invoked when we encouter a dict or a list. We populate a list that will get parsed into
		a list or a dict when we encouter the ending character
		:param struct_type: the type of input that we have. Will help us differentiate between dict and list
		:return: The structure that was created. either dict or list. this can create nested lists and dicts.
		"""
		container = list()
		data_type, method = self.__get_data_type()
		inner_type = data_type
		while inner_type != 'e':
			try:
				val = method(inner_type)
				container.append(val)
				inner_type, method = self.__get_data_type()
			except TypeError:
				raise ValueError("Malformed input")
		if struct_type == 'l':
			return container
		elif struct_type == 'd':
			return {i: j for i, j in zip(container[::2], container[1::2])}

	def __read_int(self, integer):
		"""
		:param integer: not used
		:return: the integer that is read. The value read from file is coerced to an int
		"""

		match = re.match(INT_PATTERN, self.data[self.cur:])
		val = match.group(1)
		self.log.debug("_read_int {0}".format(val))
		self.cur += match.span(2)[0]  # move cursor past the actual length string
		return int(val)

	def __read_string(self, str):
		"""
		:param str: not used
		:return: the parsed string
		"""
		match = re.match(STR_PATTERN, self.data[self.cur:])
		str_length = int(match.group(1))
		self.cur += match.span(2)[0]  # move cursor past the actual length string

		str_val = self.data[self.cur: self.cur + int(match.group(1))]
		self.cur += str_length

		self.log.debug("_read_string {0}".format(str_val))
		return str_val