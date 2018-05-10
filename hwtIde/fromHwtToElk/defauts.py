from fromHwtToElk.convertor import sortStatementPorts
from fromHwtToElk.extractSplits import extractSplits
from fromHwtToElk.flattenPorts import flattenPorts
from fromHwtToElk.flattenTrees import flattenTrees
from fromHwtToElk.mergeSplitsOnInterfaces import mergeSplitsOnInterfaces
from fromHwtToElk.netlistPreprocessors import indexedAssignmentsToConcatenation,\
    unhideResultsOfIndexingAndConcatOnPublicSignals
from fromHwtToElk.reduceUselessAssignments import reduceUselessAssignments
from fromHwtToElk.resolveSharedConnections import resolveSharedConnections
from hwt.synthesizer.dummyPlatform import DummyPlatform


DEFAULT_PLATFORM = DummyPlatform()
DEFAULT_PLATFORM.beforeHdlArchGeneration.extend([
    indexedAssignmentsToConcatenation,
    unhideResultsOfIndexingAndConcatOnPublicSignals,
])

DEFAULT_LAYOUT_OPTIMIZATIONS = [
    # optimizations
    reduceUselessAssignments,
    extractSplits,
    lambda root: flattenTrees(root, lambda node: node.name == "CONCAT"),
    mergeSplitsOnInterfaces,
    resolveSharedConnections,
    sortStatementPorts,
    # required for to json conversion
    flattenPorts,
]
