from typing import Callable
from elkContainer.lNode import LNode


def flattenTrees(root, toL, nodeSelector: Callable[[LNode], bool]):
    """
    Walk all nodes and discover trees of operators and reduce them
    to single node with multiple outputs

    :attention: node has to have single output
    """
    raise not NotImplementedError()
