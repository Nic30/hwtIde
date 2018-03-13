class BinaryIndexedTree():
    """
    :note: Ported from ELK.
    :note: Highly inefficient in python.

    Sorted list of integers storing values from 0 up to the maxNumber passed
    on creation. Adding, removing and indexOf
    (and addAndIndexOf) is in O(log maxNumber).

    Implemented as a binary tree where each leaf stores the number of integers
    at the leaf index and each node stores the
    number of values in the left branch of the node.
    """

    def __init__(self, maxNum: int):
        """
        :param maxNum: maximum number elements.
        """
        self.maxNum = maxNum
        self.binarySums = [0 for _ in range(maxNum + 1)]
        self.numsPerIndex = [0 for _ in range(maxNum)]
        self.size = 0

    def add(self, index: int):
        """
        Increment given index.
        :param index: The index to increment.
        """
        self.size += 1
        self.numsPerIndex[index] += 1
        i = index + 1
        binarySums = self.binarySums
        while i < len(binarySums):
            binarySums[i] += 1
            i += i & -i

    def rank(self, index: int):
        """
        Sum all entries before given index, i.e. index - 1.

        :param index:
                   Not included end index.
        :return sum:
        """
        i = index
        sum_ = 0
        binarySums = self.binarySums
        while i > 0:
            sum_ += binarySums[i]
            i -= i & -i

        return sum_

    def size(self):
        return self.size

    def removeAll(self, index: int):
        """
        Remove all entries for one index.

        :param index: the index
        """
        numEntries = self.numsPerIndex[index]
        if numEntries == 0:
            return

        self.numsPerIndex[index] = 0
        self.size -= numEntries
        i = index + 1
        binarySums = self.binarySums
        while i < len(binarySums):
            binarySums[i] -= numEntries
            i += i & -i

    def clear(self):
        """
        Clears contents of tree.
        """
        self.binarySums.clear()
        self.numsPerIndex.clear()
        self.size = 0

    def isEmpty(self) -> bool:
        return self.size == 0
