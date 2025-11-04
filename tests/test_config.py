from webresource.config import ResourceConfig

import unittest
import webresource as wr


class TestConfig(unittest.TestCase):
    def test_ResourceConfig(self):
        config = ResourceConfig()
        self.assertIsInstance(wr.config, ResourceConfig)
        self.assertFalse(config.development)

        config.development = True
        self.assertTrue(config.development)


if __name__ == '__main__':
    unittest.main()
