from elkContainer.lNode import LNode


class ElkIdStore(dict):
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.reverseDict = {v: k for k, v in self.items()}
        self.nodeCnt = -1 # skip root node in numbering

    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            pass

        if isinstance(key, LNode):
            name = self.nodeCnt
            self.nodeCnt += 1
        else:
            try:
                name = key.name
            except AttributeError:
                name = None

            if name is None:
                name = len(self)

        if name in self.reverseDict:
            name = "%s_%d" % (name, id(key))

        if name in self.reverseDict:
            raise AssertionError("Redifinition", name,
                                 self.reverseDict[name], key)
        self[key] = name
        self.reverseDict[name] = key
        return name
