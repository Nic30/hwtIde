import unittest

from hwtIde.layout.crossing.binaryIndexedTree import BinaryIndexedTree


class BinaryIndexedTreeTC(unittest.TestCase):

    def test_sumBefore(self):
        ft = BinaryIndexedTree(5)
        ft.add(1)
        ft.add(2)
        ft.add(1)

        self.assertEqual(ft.rank(1), 0)
        self.assertEqual(ft.rank(2), 2)

    def test_size(self):
        ft = BinaryIndexedTree(5)
        ft.add(2)
        ft.add(1)
        ft.add(1)

        self.assertEqual(ft.size, 3)

    def removeAll(self):
        ft = BinaryIndexedTree(5)
        ft.add(0)
        ft.add(2)
        ft.add(1)
        ft.add(1)

        ft.removeAll(1)

        self.assertEqual(ft.size, 2)
        self.assertEqual(ft.rank(2), 1)

        ft.removeAll(1)

        self.assertEqual(ft.size, 2)
        self.assertEqual(ft.rank(2), 1)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(FrameTmplTC('test_sWithStartPadding'))
    suite.addTest(unittest.makeSuite(BinaryIndexedTreeTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
