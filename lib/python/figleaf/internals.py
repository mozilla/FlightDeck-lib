"""
Coverage tracking internals.
"""

import sys
import threading

err = sys.stderr

from token import *
import parser, types, symbol

# use builtin sets if in >= 2.4, otherwise use 'sets' module.
try:
    set()
except NameError:
    from sets import Set as set

def get_token_name(x):
    """
    Utility to help pretty-print AST symbols/Python tokens.
    """
    if symbol.sym_name.has_key(x):
        return symbol.sym_name[x]
    return tok_name.get(x, '-')

class LineGrabber:
    """
    Count 'interesting' lines of Python in source files, where
    'interesting' is defined as 'lines that could possibly be
    executed'.

    @CTB this badly needs to be refactored... once I have automated
    tests ;)
    """
    def __init__(self, fp):
        """
        Count lines of code in 'fp'.
        """
        self.lines = set()

        src = fp.read().strip() + "\n"
        
        self.ast = parser.suite(src)
        
        self.tree = parser.ast2tuple(self.ast, True)

        self.find_terminal_nodes(self.tree)

    def find_terminal_nodes(self, tup):
        """
        Recursively eat an AST in tuple form, finding the first line
        number for "interesting" code.
        """
        (sym, rest) = tup[0], tup[1:]

        line_nos = set()
        if type(rest[0]) == types.TupleType:  ### node

            for x in rest:
                token_line_no = self.find_terminal_nodes(x)
                if token_line_no is not None:
                    line_nos.add(token_line_no)

            if symbol.sym_name[sym] in ('stmt', 'suite', 'lambdef',
                                        'except_clause') and line_nos:
                # store the line number that this statement started at
                self.lines.add(min(line_nos))
            elif symbol.sym_name[sym] in ('if_stmt',):
                # add all lines under this
                self.lines.update(line_nos)
            elif symbol.sym_name[sym] in ('global_stmt',): # IGNORE
                return
            else:
                if line_nos:
                    return min(line_nos)

        else:                               ### leaf
            if sym not in (NEWLINE, STRING, INDENT, DEDENT, COLON) and \
               tup[1] != 'else':
                return tup[2]
            return None

    def pretty_print(self, tup=None, indent=0):
        """
        Pretty print the AST.
        """
        if tup is None:
            tup = self.tree

        s = tup[1]

        if type(s) == types.TupleType:
            print ' '*indent, get_token_name(tup[0])
            for x in tup[1:]:
                self.pretty_print(x, indent+1)
        else:
            print ' '*indent, get_token_name(tup[0]), tup[1:]

class CodeTracer:
    """
    Basic mechanisms for code coverage tracking, using sys.settrace.  
    """
    def __init__(self, exclude_prefix, include_only_prefix):
        self.common = self.c = set()
        self.section_name = None
        self.sections = {}
        
        self.started = False

        assert not (exclude_prefix and include_only_prefix), \
               "mutually exclusive"
        
        self.excl = exclude_prefix
        self.incl = include_only_prefix

    def start(self):
        """
        Start recording.
        """
        if not self.started:
            self.started = True

            if self.excl and not self.incl:
                global_trace_fn = self.g1
            elif self.incl and not self.excl:
                global_trace_fn = self.g2
            else:
                global_trace_fn = self.g0

            sys.settrace(global_trace_fn)

            if hasattr(threading, 'settrace'):
                threading.settrace(global_trace_fn)

    def stop(self):
        if self.started:
            sys.settrace(None)
            
            if hasattr(threading, 'settrace'):
                threading.settrace(None)

            self.started = False
            self.stop_section()

    def g0(self, f, e, a):
        """
        global trace function, no exclude/include info.

        f == frame, e == event, a == arg        .
        """
        if e == 'call':
            return self.t

    def g1(self, f, e, a):
        """
        global trace function like g0, but ignores files starting with
        'self.excl'.
        """
        if e == 'call':
            excl = self.excl
            if excl and f.f_code.co_filename.startswith(excl):
                return

            return self.t

    def g2(self, f, e, a):
        """
        global trace function like g0, but only records files starting with
        'self.incl'.
        """
        if e == 'call':
            incl = self.incl
            if incl and f.f_code.co_filename.startswith(incl):
                return self.t

    def t(self, f, e, a):
        """
        local trace function.
        """
        if e is 'line':
            self.c.add((f.f_code.co_filename, f.f_lineno))
        return self.t

    def clear(self):
        """
        wipe out coverage info
        """

        self.c = {}

    def start_section(self, name):
        self.stop_section()

        self.section_name = name
        self.c = self.sections.get(name, set())
        
    def stop_section(self):
        if self.section_name:
            self.sections[self.section_name] = self.c
            self.section_name = None
            self.c = self.common

class CoverageData:
    """
    A class to manipulate and combine data from the CodeTracer object.

    In general, do not pickle this object; it's simpler and more
    straightforward to just pass the basic Python objects around
    (e.g. CoverageData.common, a set, and CoverageData.sections, a
    dictionary of sets).
    """
    def __init__(self, trace_obj=None):
        self.common = set()
        self.sections = {}
        
        if trace_obj:
            self.update(trace_obj)
            
    def update(self, trace_obj):
        # transfer common-block code coverage -- if no sections are set,
        # this will be all of the code coverage info.
        self.common.update(trace_obj.common)

        # update our internal section dictionary with the (filename, line_no)
        # pairs from the section coverage as well.
        
        for section_name, section_d in trace_obj.sections.items():
            section_set = self.sections.get(section_name, set())
            section_set.update(section_d)
            self.sections[section_name] = section_set

    def gather_files(self, name=None):
        """
        Return the dictionary of lines of executed code; the dict
        keys are filenames and values are sets containing individual
        (integer) line numbers.
        
        'name', if set, is the desired section name from which to gather
        coverage info.
        """
        cov = set()
        cov.update(self.common)

        if name is None:
            for section_name, coverage_set in self.sections.items():
                cov.update(coverage_set)
        else:
            coverage_set = self.sections.get(name, set())
            cov.update(coverage_set)
            
#        cov = list(cov)
#        cov.sort()

        files = {}
        for (filename, line) in cov:    # @CTB could optimize
            d = files.get(filename, set())
            d.add(line)
            files[filename] = d

        return files

    def gather_sections(self, file):
        """
        Return a dictionary of sets containing section coverage information for
        a specific file.  Dict keys are sections, and the dict values are
        sets containing (integer) line numbers.
        """
        sections = {}
        for k, c in self.sections.items():
            s = set()
            for (filename, line) in c.keys():
                if filename == file:
                    s.add(line)
            sections[k] = s
        return sections
