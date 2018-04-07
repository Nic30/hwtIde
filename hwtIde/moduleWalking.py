import os
from os.path import join, relpath
from importlib import import_module
from hwt.synthesizer.unit import Unit
from inspect import isclass


def walk_modules_recursive_names(module):
    """
    For specified module walk all python files and yield module name for them
    """
    f = module.__file__
    rootName = module.__name__
    init = "__init__.py"
    if f.endswith(init):
        folder = f[:-len(init)]
        for root, _, files in os.walk(folder):
            root = relpath(root, folder)
            for file in files:
                if file.endswith(".py"):
                    if file.endswith(init):
                        if root == ".":
                            file = rootName
                        else:
                            assert "." not in root, root
                            file = rootName + "." + root.replace("/", ".")
                    else:
                        file = file[:-len(".py")]
                        assert "." not in file, file
                        if root != ".":
                            file = join(root, file)
                        file = rootName + "." + file.replace("/", ".")
                    yield file


def walk_modules_recursive(module):
    for file in walk_modules_recursive_names(module):
        yield import_module(file)


def walk_Unit_cls_in_module(module):
    seen = set()
    for m in walk_modules_recursive(module):
        for _, o in m.__dict__.items():
            if isclass(o) and issubclass(o, Unit) and o not in seen:
                seen.add(o)
                yield o
