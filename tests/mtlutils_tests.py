import unittest
import sys
import datetime

sys.path.append('../ingestor')

import mtlutils


class Tests(unittest.TestCase):
    
    def test_unquoted_times(self):
        mtl_dict = mtlutils.parsemeta('data/LC80010052015083LGN00_MTL.txt')
        self.assertEqual(
            datetime.time(14, 8, 18, 854493),
            mtl_dict['L1_METADATA_FILE']['PRODUCT_METADATA']['SCENE_CENTER_TIME'])

    def test_quoted_times(self):
        mtl_dict = mtlutils.parsemeta('data/LC82200762015113LGN00_MTL.txt')
        self.assertEqual(
            datetime.time(13, 9, 52, 809375),
            mtl_dict['L1_METADATA_FILE']['PRODUCT_METADATA']['SCENE_CENTER_TIME'])

if __name__ == '__main__':
    unittest.main()
