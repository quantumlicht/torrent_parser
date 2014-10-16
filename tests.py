import unittest
from lib.torrent_parser import TorrentParser


TEST_FILE_GODFATHER = 'The.God.Father.2TPB.torrent'
TEST_FILE_SAMPLE = 'sample.torrent'
TEST_FILE_DISTRICT9 = 'District_9.TPB.torrent'
class TestParser(unittest.TestCase):

	def setUp(self):
		self.parser = TorrentParser(debug_mode=False)

	def test_base_integer(self):
			res = self.parser.decode('i198790790e')
			self.assertEqual(res, 198790790)

	def test_negative_integer(self):
		res = self.parser.decode('i-178978789e')
		self.assertEqual(res, -178978789)

	def test_base_dict(self):
		res = self.parser.decode('d3:abc5:abcde3:lmn2:poe')
		self.assertEqual(res,{'abc':'abcde','lmn':'po'})

	def test_nested_dict(self):
		res_a = self.parser.decode('d3:abc3:abc1:ad2:ab3:kbae3:lmn2:poe')
		res_b = self.parser.decode('d3:abc3:abc1:ad2:ab3:kba3:lmn2:poee')
		self.assertEqual(res_a,{'abc': 'abc', 'a': {'ab': 'kba'}, 'lmn': 'po'})
		self.assertEqual(res_b,{'abc': 'abc', 'a': {'ab': 'kba', 'lmn': 'po'}})

	def test_malformed_dict(self):
		input = 'd3:abc2:ak4:cvbn'
		res = self.parser.decode('d3:abc2:ak4:cvbn')
		self.assertEquals(res, None)
		# self.assertRaises(ValueError, self.parser.decode, input)

	def test_base_list(self):
		res = self.parser.decode('l3:abc5:abcde3:lmn2:poe')
		self.assertEqual(res,['abc', 'abcde', 'lmn', 'po'])

	def test_nested_list(self):
		res_a = self.parser.decode('l3:abcl5:abcde3:lmn2:poe4:cvbne')
		res_b = self.parser.decode('l3:abc5:abcdel2:mn2:po4:cvbnee')
		self.assertEqual(res_a,['abc', ['abcde', 'lmn', 'po'], 'cvbn'])
		self.assertEqual(res_b,['abc', 'abcde', ['mn', 'po', 'cvbn']])

	def test_malformed_list(self):
		input = 'l3:abc2:ak4:cvbn'
		res = self.parser.decode(input)
		self.assertEquals(res, None)
		# self.assertRaises(ValueError, self.parser.decode, input)

	def test_gibberish(self):
		input = 'a3ee2:fjkhklae'
		res = self.parser.decode(input)
		self.assertEquals(res, None)

	def test_input_file(self):
		self.parser.readfile(TEST_FILE_SAMPLE)
		print self.parser.decode()

	def test_real_torrent_file(self):
		self.parser.readfile(TEST_FILE_GODFATHER)
		# self.parser.readfile(TEST_FILE_DISTRICT9)
		print self.parser.decode()