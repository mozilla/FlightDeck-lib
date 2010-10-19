# copyright 2003-2010 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
# contact http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This file is part of logilab-common.
#
# logilab-common is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 2.1 of the License, or (at your option) any
# later version.
#
# logilab-common is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with logilab-common.  If not, see <http://www.gnu.org/licenses/>.
"""provides unit tests for compat module"""

from logilab.common.testlib import TestCase, unittest_main
import sys
import types
from logilab.common.compat import builtins

class CompatTCMixIn:
    MODNAMES = {}
    BUILTINS = []
    ALTERED_BUILTINS = {}

    def setUp(self):
        self.builtins_backup = {}
        self.modules_backup = {}
        self.remove_builtins()
        self.alter_builtins()
        self.remove_modules()

    def tearDown(self):
        for modname in self.MODNAMES:
            del sys.modules[modname]
        for funcname, func in self.builtins_backup.items():
            setattr(builtins, funcname, func)
            # delattr(builtins, 'builtin_%s' % funcname)
        for modname, mod in self.modules_backup.items():
            sys.modules[modname] = mod
        try:
            del sys.modules['logilab.common.compat']
        except KeyError:
            pass

    def remove_builtins(self):
        for builtin in self.BUILTINS:
            func = getattr(builtins, builtin, None)
            if func is not None:
                self.builtins_backup[builtin] = func
                delattr(builtins, builtin)
                # setattr(builtins, 'builtin_%s' % builtin, func)
    def alter_builtins(self):
        for builtin, func in self.ALTERED_BUILTINS.iteritems():
            old_func = getattr(builtins, builtin, None)
            if func is not None:
                self.builtins_backup[builtin] = old_func
                setattr(builtins, builtin, func)
                # setattr(builtins, 'builtin_%s' % builtin, func)

    def remove_modules(self):
        for modname in self.MODNAMES:
            if modname in sys.modules:
                self.modules_backup[modname] = sys.modules[modname]
            sys.modules[modname] = types.ModuleType('faked%s' % modname)

    def test_removed_builtins(self):
        """tests that builtins are actually uncallable"""
        for builtin in self.BUILTINS:
            self.assertRaises(NameError, eval, builtin, {})

    def test_removed_modules(self):
        """tests that builtins are actually emtpy"""
        for modname, funcnames in self.MODNAMES.items():
            import_stmt = 'from %s import %s' % (modname, ', '.join(funcnames))
            # FIXME: use __import__ instead
            code = compile(import_stmt, 'foo.py', 'exec')
            self.assertRaises(ImportError, eval, code)


class Py23CompatTC(CompatTCMixIn, TestCase):
    MODNAMES = {
        'sets' : ('Set', 'ImmutableSet'),
        }

    def test_basic_set(self):
        from logilab.common.compat import set
        s = set('abc')
        self.assertEqual(len(s), 3)
        s.remove('a')
        self.assertEqual(len(s), 2)
        s.add('a')
        self.assertEqual(len(s), 3)
        s.add('a')
        self.assertEqual(len(s), 3)
        self.assertRaises(KeyError, s.remove, 'd')

    def test_basic_set(self):
        from logilab.common.compat import set
        s = set('abc')
        self.assertEqual(len(s), 3)
        s.remove('a')
        self.assertEqual(len(s), 2)
        s.add('a')
        self.assertEqual(len(s), 3)
        s.add('a')
        self.assertEqual(len(s), 3)
        self.assertRaises(KeyError, s.remove, 'd')
        self.assertRaises(TypeError, dict, [(s, 'foo')])


    def test_frozenset(self):
        from logilab.common.compat import frozenset
        s = frozenset('abc')
        self.assertEqual(len(s), 3)
        self.assertRaises(AttributeError, getattr, s, 'remove')
        self.assertRaises(AttributeError, getattr, s, 'add')
        d = {s : 'foo'} # frozenset should be hashable
        d[s] = 'bar'
        self.assertEqual(len(d), 1)
        self.assertEqual(d[s], 'bar')


class Py24CompatTC(CompatTCMixIn, TestCase):
    BUILTINS = ('reversed', 'sorted', 'set', 'frozenset',)

    def test_sorted(self):
        if sys.version_info >= (3, 0):
            self.skip("don't test 2.4 compat 'sorted' on >= 3.0")
        from logilab.common.compat import sorted
        l = [3, 1, 2, 5, 4]
        s = sorted(l)
        self.assertEqual(s, [1, 2, 3, 4, 5])
        self.assertEqual(l, [3, 1, 2, 5, 4])
        self.assertEqual(sorted('FeCBaD'), list('BCDFae'))
        self.assertEqual(sorted('FeCBaD', key=str.lower), list('aBCDeF'))
        self.assertEqual(sorted('FeCBaD', key=str.lower, reverse=True), list('FeDCBa'))
        def strcmp(s1, s2):
            return cmp(s1.lower(), s2.lower())
        self.assertEqual(sorted('FeCBaD', cmp=strcmp), list('aBCDeF'))


    def test_reversed(self):
        from logilab.common.compat import reversed
        l = range(5)
        r = reversed(l)
        self.assertEqual(r, [4, 3, 2, 1, 0])
        self.assertEqual(l, range(5))

    def test_set(self):
        if sys.version_info >= (3, 0):
            self.skip("don't test 2.4 compat 'set' on >= 3.0")
        from logilab.common.compat import set
        s1 = set(range(5))
        s2 = set(range(2, 6))
        self.assertEqual(len(s1), 5)
        self.assertEqual(s1 & s2, set([2, 3, 4]))
        self.assertEqual(s1 | s2, set(range(6)))



class _MaxFaker(object):
    def __init__(self, func):
        self.func = func
    def fake(self,*args,**kargs):
        if kargs:
            raise TypeError("max() takes no keyword argument")
        return self.func(*args)


class Py25CompatTC(CompatTCMixIn, TestCase):
    BUILTINS = ('any', 'all',)
    ALTERED_BUILTINS = {'max': _MaxFaker(max).fake}

    def test_any(self):
        from logilab.common.compat import any
        testdata = ([], (), '', 'abc', xrange(0, 10), xrange(0, -10, -1))
        self.assertEqual(any([]), False)
        self.assertEqual(any(()), False)
        self.assertEqual(any(''), False)
        self.assertEqual(any('abc'), True)
        self.assertEqual(any(xrange(10)), True)
        self.assertEqual(any(xrange(0, -10, -1)), True)
        # python2.5's any consumes iterables
        irange = iter(range(10))
        self.assertEqual(any(irange), True)
        self.assertEqual(irange.next(), 2)


    def test_all(self):
        from logilab.common.compat import all
        testdata = ([], (), '', 'abc', xrange(0, 10), xrange(0, -10, -1))
        self.assertEqual(all([]), True)
        self.assertEqual(all(()), True)
        self.assertEqual(all(''), True)
        self.assertEqual(all('abc'), True)
        self.assertEqual(all(xrange(10)), False)
        self.assertEqual(all(xrange(0, -10, -1)), False)
        # python2.5's all consumes iterables
        irange = iter(range(10))
        self.assertEqual(all(irange), False)
        self.assertEqual(irange.next(), 1)

    def test_max(self):
        from logilab.common.compat import max

        # old apy
        self.assertEqual(max("fdjkmhsgmdfhsg"),'s')
        self.assertEqual(max(1,43,12,45,1337,34,2), 1337)
        self.assertRaises(TypeError,max)
        self.assertRaises(TypeError,max,1)
        self.assertRaises(ValueError,max,[])
        self.assertRaises(TypeError,max,bob=None)

        # new apy
        self.assertEqual(max("shorter","longer",key=len),"shorter")
        self.assertEqual(max(((1,1),(2,3,5),(8,13,21)),key=len),(2,3,5))
        self.assertEqual(max(((1,1),(42,),(2,3,5),(8,13,21)),key=max),(42,))
        self.assertRaises(TypeError,max,key=None)
        self.assertRaises(TypeError,max,1,key=len)
        self.assertRaises(ValueError,max,[],key=max)
        self.assertRaises(TypeError,max,"shorter","longer",key=len,kathy=None)


if __name__ == '__main__':
    unittest_main()
