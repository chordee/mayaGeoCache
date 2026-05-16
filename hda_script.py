
import importlib.util
import hou


def cache():
    node = hou.pwd()
    path = node.parm('module_path').eval()
    spec = importlib.util.spec_from_file_location('nCache', path)
    nc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(nc)
    nc.houdini_export()
