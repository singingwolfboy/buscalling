import pdb, sys

def set_trace():
    sys.stdout, sys.__stdout__ = sys.__stdout__, sys.stdout
    sys.stdin, sys.__stdin__ = sys.__stdin__, sys.stdin
    sys.stderr, sys.__stderr__ = sys.__stderr__, sys.stderr
    # debugger = pdb.Pdb()
    # debugger.set_trace(sys._getframe().f_back)
    pdb.set_trace()
    sys.stdout, sys.__stdout__ = sys.__stdout__, sys.stdout
    sys.stdin, sys.__stdin__ = sys.__stdin__, sys.stdin
    sys.stderr, sys.__stderr__ = sys.__stderr__, sys.stderr
