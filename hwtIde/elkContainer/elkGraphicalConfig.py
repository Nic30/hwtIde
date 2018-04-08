
class ElkGraphicalConfig():
    def __init__(self):
        self.portHeight = 20

    def width_of_str(self, s):
        if not s:
            return 0
        return len(s) * 7.55
