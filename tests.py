import unittest
from lib.torrent_parser import TorrentParser


TEST_FILE = 'The.God.Father.2TPB.torrent'
# TEST_FILE = 'sample.torrent'
class TestParser(unittest.TestCase):


	def setUp(self):
		self.parser = TorrentParser(TEST_FILE)

	def test_base_integer(self):
			# self.parser.dump_content()
			res = self.parser.decode('i198790790e')
			self.assertEqual(res, 198790790)

	def test_negative_integer(self):
		res = self.parser.decode('i-178978789e')
		self.assertEqual(res,-178978789)


	def test_base_dict(self):
		res = self.parser.decode('d3:abc5:abcde3:lmn2:poe')
		self.assertEqual(res,{'abc':'abcde','lmn':'po'})

	def test_base_list(self):
		res = self.parser.decode('l3:abc5:abcde3:lmn2:poe')
		self.assertEqual(res,['abc','abcde','lmn','po'])

	def test_nested_list(self):
		res_a = self.parser.decode('l3:abcl5:abcde3:lmn2:poe4:cvbne')
		res_b = self.parser.decode('l3:abc5:abcdel2:mn2:po4:cvbnee')
		self.assertEqual(res_a,['abc', ['abcde','lmn','po'],'cvbn'])
		self.assertEqual(res_b,['abc', 'abcde',['mn','po','cvbn']])

