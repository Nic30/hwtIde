import os
from stat import S_ISDIR
import time


class FSEntry():
    def __init__(self, name, isGroup):
        self.isGroup = isGroup
        self.name = name
        self.size = ""
        self.type = ""
        self.dateModified = None
        self.children = []

    @classmethod
    def fromFile(cls, fileName):
        st = os.stat(fileName)

        self = cls(os.path.basename(fileName), S_ISDIR(st.st_mode))
        self.size = st.st_size
        # "%Y/%m/%d  %H:%M:%S"
        self.dateModified = time.strftime(
            "%Y/%m/%d  %H:%M:%S", time.gmtime(st.st_ctime))

        return self

    def toJson(self):
        return {"group": self.isGroup,
                "data": {"name": self.name,
                         "size": self.size,
                         "type": self.type,
                         "dateModified": self.dateModified},
                "children": []
                }
