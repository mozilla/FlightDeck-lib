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
"""unittest module for logilab.comon.testlib"""

import os
import sys
from os.path import join, dirname, isdir, isfile, abspath, exists
from cStringIO import StringIO
import tempfile
import shutil

from logilab.common.compat import sorted

try:
    __file__
except NameError:
    __file__ = sys.argv[0]

from logilab.common.testlib import unittest, TestSuite, unittest_main
from logilab.common.testlib import TestCase, SkipAwareTextTestRunner, Tags
from logilab.common.testlib import mock_object, NonStrictTestLoader, create_files
from logilab.common.testlib import capture_stdout, InnerTest, with_tempdir, tag
from logilab.common.testlib import require_version, require_module


class MockTestCase(TestCase):
    def __init__(self):
        # Do not call unittest.TestCase's __init__
        pass

    def fail(self, msg):
        raise AssertionError(msg)

class UtilTC(TestCase):

    def test_mockobject(self):
        obj = mock_object(foo='bar', baz='bam')
        self.assertEqual(obj.foo, 'bar')
        self.assertEqual(obj.baz, 'bam')


    def test_create_files(self):
        chroot = tempfile.mkdtemp()
        path_to = lambda path: join(chroot, path)
        dircontent = lambda path: sorted(os.listdir(join(chroot, path)))
        try:
            self.assertFalse(isdir(path_to('a/')))
            create_files(['a/b/foo.py', 'a/b/c/', 'a/b/c/d/e.py'], chroot)
            # make sure directories exist
            self.assertTrue(isdir(path_to('a')))
            self.assertTrue(isdir(path_to('a/b')))
            self.assertTrue(isdir(path_to('a/b/c')))
            self.assertTrue(isdir(path_to('a/b/c/d')))
            # make sure files exist
            self.assertTrue(isfile(path_to('a/b/foo.py')))
            self.assertTrue(isfile(path_to('a/b/c/d/e.py')))
            # make sure only asked files were created
            self.assertEqual(dircontent('a'), ['b'])
            self.assertEqual(dircontent('a/b'), ['c', 'foo.py'])
            self.assertEqual(dircontent('a/b/c'), ['d'])
            self.assertEqual(dircontent('a/b/c/d'), ['e.py'])
        finally:
            shutil.rmtree(chroot)


class TestlibTC(TestCase):

    capture = True

    def mkdir(self,path):
        if not exists(path):
            self._dirs.add(path)
            os.mkdir(path)

    def setUp(self):
        self.tc = MockTestCase()
        self._dirs = set()

    def tearDown(self):
        while(self._dirs):
            shutil.rmtree(self._dirs.pop(), ignore_errors=True)

    def test_dict_equals(self):
        """tests TestCase.assertDictEquals"""
        d1 = {'a' : 1, 'b' : 2}
        d2 = {'a' : 1, 'b' : 3}
        d3 = dict(d1)
        self.assertRaises(AssertionError, self.tc.assertDictEquals, d1, d2)
        self.tc.assertDictEquals(d1, d3)
        self.tc.assertDictEquals(d3, d1)
        self.tc.assertDictEquals(d1, d1)

    def test_list_equals(self):
        """tests TestCase.assertListEqual"""
        l1 = range(10)
        l2 = range(5)
        l3 = range(10)
        self.assertRaises(AssertionError, self.tc.assertListEqual, l1, l2)
        self.tc.assertListEqual(l1, l1)
        self.tc.assertListEqual(l1, l3)
        self.tc.assertListEqual(l3, l1)

    def test_lines_equals(self):
        """tests assertLineEquals"""
        t1 = """some
        text
"""
        t2 = """some

        text"""
        t3 = """some
        text"""
        self.assertRaises(AssertionError, self.tc.assertLinesEquals, t1, t2)
        self.assertRaises(AssertionError, self.tc.assertMultiLineEqual, t1, t2)
        self.tc.assertLinesEquals(t1, t3)
        self.tc.assertMultiLineEqual(t1, t3 + "\n")
        self.tc.assertLinesEquals(t3, t1)
        self.tc.assertMultiLineEqual(t3 + "\n", t1)
        self.tc.assertLinesEquals(t1, t1)
        self.tc.assertMultiLineEqual(t1, t1)

    def test_xml_valid(self):
        """tests xml is valid"""
        valid = """<root>
        <hello />
        <world>Logilab</world>
        </root>"""
        invalid = """<root><h2> </root>"""
        self.tc.assertXMLStringWellFormed(valid)
        self.assertRaises(AssertionError, self.tc.assertXMLStringWellFormed, invalid)
        invalid = """<root><h2 </h2> </root>"""
        self.assertRaises(AssertionError, self.tc.assertXMLStringWellFormed, invalid)

    def test_unordered_equality_for_lists(self):
        l1 = [0, 1, 2]
        l2 = [1, 2, 3]
        self.assertRaises(AssertionError, self.tc.assertUnorderedIterableEquals, l1, l2)
        self.assertRaises(AssertionError, self.tc.assertItemsEqual, l1, l2)
        self.tc.assertUnorderedIterableEquals(l1, l1)
        self.tc.assertItemsEqual(l1, l1)
        self.tc.assertUnorderedIterableEquals([], [])
        self.tc.assertItemsEqual([], [])
        l1 = [0, 1, 1]
        l2 = [0, 1]
        self.assertRaises(AssertionError, self.tc.assertUnorderedIterableEquals, l1, l2)
        self.assertRaises(AssertionError, self.tc.assertItemsEqual, l1, l2)
        self.tc.assertUnorderedIterableEquals(l1, l1)
        self.tc.assertItemsEqual(l1, l1)

    def test_unordered_equality_for_dicts(self):
        d1 = {'a' : 1, 'b' : 2}
        d2 = {'a' : 1}
        self.assertRaises(AssertionError, self.tc.assertUnorderedIterableEquals, d1, d2)
        self.tc.assertUnorderedIterableEquals(d1, d1)
        self.tc.assertUnorderedIterableEquals({}, {})

    def test_equality_for_sets(self):
        s1 = set('ab')
        s2 = set('a')
        self.assertRaises(AssertionError, self.tc.assertSetEqual, s1, s2)
        self.tc.assertSetEqual(s1, s1)
        self.tc.assertSetEqual(set(), set())

    def test_unordered_equality_for_iterables(self):
        self.assertRaises(AssertionError, self.tc.assertUnorderedIterableEquals, xrange(5), xrange(6))
        self.assertRaises(AssertionError, self.tc.assertItemsEqual, xrange(5), xrange(6))
        self.tc.assertUnorderedIterableEquals(xrange(5), range(5))
        self.tc.assertItemsEqual(xrange(5), range(5))
        self.tc.assertUnorderedIterableEquals([], ())
        self.tc.assertItemsEqual([], ())

    def test_file_equality(self):
        foo = join(dirname(__file__), 'data', 'foo.txt')
        spam = join(dirname(__file__), 'data', 'spam.txt')
        self.assertRaises(AssertionError, self.tc.assertFileEqual, foo, spam)
        self.tc.assertFileEqual(foo, foo)

    def test_dir_equality(self):
        ref = join(dirname(__file__), 'data', 'reference_dir')
        same = join(dirname(__file__), 'data', 'same_dir')
        subdir_differ = join(dirname(__file__), 'data', 'subdir_differ_dir')
        file_differ = join(dirname(__file__), 'data', 'file_differ_dir')
        content_differ = join(dirname(__file__), 'data', 'content_differ_dir')
        ed1 = join(dirname(__file__), 'data', 'empty_dir_1')
        ed2 = join(dirname(__file__), 'data', 'empty_dir_2')

        for path in (ed1, ed2, join(subdir_differ,'unexpected')):
            self.mkdir(path)

        self.assertDirEquals(ed1, ed2)
        self.assertDirEquals(ref, ref)
        self.assertDirEquals( ref, same)
        self.assertRaises(AssertionError, self.assertDirEquals, ed1, ref)
        self.assertRaises(AssertionError, self.assertDirEquals, ref, ed2)
        self.assertRaises(AssertionError, self.assertDirEquals, subdir_differ, ref)
        self.assertRaises(AssertionError, self.assertDirEquals, file_differ, ref)
        self.assertRaises(AssertionError, self.assertDirEquals, ref, content_differ)

    def test_stream_equality(self):
        foo = join(dirname(__file__), 'data', 'foo.txt')
        spam = join(dirname(__file__), 'data', 'spam.txt')
        stream1 = file(foo)
        self.tc.assertStreamEqual(stream1, stream1)
        stream1 = file(foo)
        stream2 = file(spam)
        self.assertRaises(AssertionError, self.tc.assertStreamEqual, stream1, stream2)

    def test_text_equality(self):
        self.assertRaises(AssertionError, self.tc.assertTextEqual, "toto", 12)
        self.assertRaises(AssertionError, self.tc.assertMultiLineEqual, "toto", 12)
        self.assertRaises(AssertionError, self.tc.assertTextEqual, "toto", None)
        self.assertRaises(AssertionError, self.tc.assertMultiLineEqual, "toto", None)
        self.assertRaises(AssertionError, self.tc.assertTextEqual, 3.12, u"toto")
        self.assertRaises(AssertionError, self.tc.assertMultiLineEqual, 3.12, u"toto")
        self.assertRaises(AssertionError, self.tc.assertTextEqual, None, u"toto")
        self.assertRaises(AssertionError, self.tc.assertMultiLineEqual, None, u"toto")
        self.tc.assertTextEqual('toto\ntiti', 'toto\ntiti')
        self.tc.assertMultiLineEqual('toto\ntiti', 'toto\ntiti')
        self.tc.assertTextEqual('toto\ntiti', 'toto\n titi\n', striplines=True)
        self.assertRaises(AssertionError, self.tc.assertTextEqual, 'toto\ntiti', 'toto\n titi\n')
        self.assertRaises(AssertionError, self.tc.assertMultiLineEqual, 'toto\ntiti', 'toto\n titi\n')
        foo = join(dirname(__file__), 'data', 'foo.txt')
        spam = join(dirname(__file__), 'data', 'spam.txt')
        text1 = file(foo).read()
        self.tc.assertTextEqual(text1, text1)
        self.tc.assertMultiLineEqual(text1, text1)
        text2 = file(spam).read()
        self.assertRaises(AssertionError, self.tc.assertTextEqual, text1, text2)
        self.assertRaises(AssertionError, self.tc.assertMultiLineEqual, text1, text2)

    def test_assert_raises(self):
        exc = self.tc.assertRaises(KeyError, {}.__getitem__, 'foo')
        self.assertTrue(isinstance(exc, KeyError))
        self.assertEqual(exc.args, ('foo',))

    def test_default_datadir(self):
        expected_datadir = join(dirname(abspath(__file__)), 'data')
        self.assertEqual(self.datadir, expected_datadir)
        self.assertEqual(self.datapath('foo'), join(expected_datadir, 'foo'))

    def test_multiple_args_datadir(self):
        expected_datadir = join(dirname(abspath(__file__)), 'data')
        self.assertEqual(self.datadir, expected_datadir)
        self.assertEqual(self.datapath('foo', 'bar'), join(expected_datadir, 'foo', 'bar'))

    def test_custom_datadir(self):
        class MyTC(TestCase):
            datadir = 'foo'
            def test_1(self): pass

        # class' custom datadir
        tc = MyTC('test_1')
        self.assertEqual(tc.datapath('bar'), join('foo', 'bar'))
        # instance's custom datadir
        self.skipTest('should this really work?')
        tc.datadir = 'spam'
        self.assertEqual(tc.datapath('bar'), join('spam', 'bar'))

    def test_cached_datadir(self):
        """test datadir is cached on the class"""
        class MyTC(TestCase):
            def test_1(self): pass

        expected_datadir = join(dirname(abspath(__file__)), 'data')
        tc = MyTC('test_1')
        self.assertEqual(tc.datadir, expected_datadir)
        # changing module should not change the datadir
        MyTC.__module__ = 'os'
        self.assertEqual(tc.datadir, expected_datadir)
        # even on new instances
        tc2 = MyTC('test_1')
        self.assertEqual(tc2.datadir, expected_datadir)

    def test_is(self):
        obj_1 = []
        obj_2 = []
        self.assertIs(obj_1,obj_1)
        self.assertRaises(AssertionError, self.assertIs, obj_1, obj_2)

    def test_isnot(self):
        obj_1 = []
        obj_2 = []
        self.assertIsNot(obj_1,obj_2)
        self.assertRaises(AssertionError, self.assertIsNot, obj_1, obj_1)

    def test_none(self):
        self.assertNone(None)
        self.assertRaises(AssertionError, self.assertNone, object())

    def test_not_none(self):
        self.assertNotNone(object())
        self.assertRaises(AssertionError, self.assertNotNone, None)

    def test_in(self):
        self.assertIn("a", "dsqgaqg")
        obj, seq = 'a', ('toto', "azf", "coin")
        self.assertRaises(AssertionError, self.assertIn, obj, seq)

    def test_not_in(self):
        self.assertNotIn('a', ('toto', "azf", "coin"))
        self.assertRaises(AssertionError, self.assertNotIn, 'a', "dsqgaqg")


class GenerativeTestsTC(TestCase):

    def setUp(self):
        output = StringIO()
        self.runner = SkipAwareTextTestRunner(stream=output)

    def test_generative_ok(self):
        class FooTC(TestCase):
            def test_generative(self):
                for i in xrange(10):
                    yield self.assertEqual, i, i
        result = self.runner.run(FooTC('test_generative'))
        self.assertEqual(result.testsRun, 10)
        self.assertEqual(len(result.failures), 0)
        self.assertEqual(len(result.errors), 0)


    def test_generative_half_bad(self):
        class FooTC(TestCase):
            def test_generative(self):
                for i in xrange(10):
                    yield self.assertEqual, i%2, 0
        result = self.runner.run(FooTC('test_generative'))
        self.assertEqual(result.testsRun, 10)
        self.assertEqual(len(result.failures), 5)
        self.assertEqual(len(result.errors), 0)


    def test_generative_error(self):
        class FooTC(TestCase):
            def test_generative(self):
                for i in xrange(10):
                    if i == 5:
                        raise ValueError('STOP !')
                    yield self.assertEqual, i, i

        result = self.runner.run(FooTC('test_generative'))
        self.assertEqual(result.testsRun, 5)
        self.assertEqual(len(result.failures), 0)
        self.assertEqual(len(result.errors), 1)

    def test_generative_error2(self):
        class FooTC(TestCase):
            def test_generative(self):
                for i in xrange(10):
                    if i == 5:
                        yield self.ouch
                    yield self.assertEqual, i, i
            def ouch(self): raise ValueError('stop !')
        result = self.runner.run(FooTC('test_generative'))
        self.assertEqual(result.testsRun, 6)
        self.assertEqual(len(result.failures), 0)
        self.assertEqual(len(result.errors), 1)


    def test_generative_setup(self):
        class FooTC(TestCase):
            def setUp(self):
                raise ValueError('STOP !')
            def test_generative(self):
                for i in xrange(10):
                    yield self.assertEqual, i, i

        result = self.runner.run(FooTC('test_generative'))
        self.assertEqual(result.testsRun, 1)
        self.assertEqual(len(result.failures), 0)
        self.assertEqual(len(result.errors), 1)

    def test_generative_inner_skip(self):
        class FooTC(TestCase):
            def check(self, val):
                if val == 5:
                    self.innerSkip("no 5")
                else:
                    self.assertEqual(val, val)

            def test_generative(self):
                for i in xrange(10):
                    yield InnerTest("check_%s"%i, self.check, i)

        result = self.runner.run(FooTC('test_generative'))
        self.assertEqual(result.testsRun, 10)
        self.assertEqual(len(result.failures), 0)
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(len(result.skipped), 1)

    def test_generative_skip(self):
        class FooTC(TestCase):
            def check(self, val):
                if val == 5:
                    self.skipTest("no 5")
                else:
                    self.assertEqual(val, val)

            def test_generative(self):
                for i in xrange(10):
                    yield InnerTest("check_%s"%i, self.check, i)

        result = self.runner.run(FooTC('test_generative'))
        self.assertEqual(result.testsRun, 6)
        self.assertEqual(len(result.failures), 0)
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(len(result.skipped), 1)

    def test_generative_inner_error(self):
        class FooTC(TestCase):
            def check(self, val):
                if val == 5:
                    raise ValueError("no 5")
                else:
                    self.assertEqual(val, val)

            def test_generative(self):
                for i in xrange(10):
                    yield InnerTest("check_%s"%i, self.check, i)

        result = self.runner.run(FooTC('test_generative'))
        self.assertEqual(result.testsRun, 6)
        self.assertEqual(len(result.failures), 0)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(len(result.skipped), 0)

    def test_generative_inner_failure(self):
        class FooTC(TestCase):
            def check(self, val):
                if val == 5:
                    self.assertEqual(val, val+1)
                else:
                    self.assertEqual(val, val)

            def test_generative(self):
                for i in xrange(10):
                    yield InnerTest("check_%s"%i, self.check, i)

        result = self.runner.run(FooTC('test_generative'))
        self.assertEqual(result.testsRun, 10)
        self.assertEqual(len(result.failures), 1)
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(len(result.skipped), 0)


class ExitFirstTC(TestCase):
    def setUp(self):
        output = StringIO()
        self.runner = SkipAwareTextTestRunner(stream=output, exitfirst=True)

    def test_failure_exit_first(self):
        class FooTC(TestCase):
            def test_1(self): pass
            def test_2(self): assert False
            def test_3(self): pass
        tests = [FooTC('test_1'), FooTC('test_2')]
        result = self.runner.run(TestSuite(tests))
        self.assertEqual(result.testsRun, 2)
        self.assertEqual(len(result.failures), 1)
        self.assertEqual(len(result.errors), 0)


    def test_error_exit_first(self):
        class FooTC(TestCase):
            def test_1(self): pass
            def test_2(self): raise ValueError()
            def test_3(self): pass
        tests = [FooTC('test_1'), FooTC('test_2'), FooTC('test_3')]
        result = self.runner.run(TestSuite(tests))
        self.assertEqual(result.testsRun, 2)
        self.assertEqual(len(result.failures), 0)
        self.assertEqual(len(result.errors), 1)

    def test_generative_exit_first(self):
        class FooTC(TestCase):
            def test_generative(self):
                for i in xrange(10):
                    yield self.assert_, False
        result = self.runner.run(FooTC('test_generative'))
        self.assertEqual(result.testsRun, 1)
        self.assertEqual(len(result.failures), 1)
        self.assertEqual(len(result.errors), 0)


class TestLoaderTC(TestCase):
    ## internal classes for test purposes ########
    class FooTC(TestCase):
        def test_foo1(self): pass
        def test_foo2(self): pass
        def test_bar1(self): pass

    class BarTC(TestCase):
        def test_bar2(self): pass
    ##############################################

    def setUp(self):
        self.loader = NonStrictTestLoader()
        self.module = TestLoaderTC # mock_object(FooTC=TestLoaderTC.FooTC, BarTC=TestLoaderTC.BarTC)
        self.output = StringIO()
        self.runner = SkipAwareTextTestRunner(stream=self.output)

    def assertRunCount(self, pattern, module, expected_count, skipped=()):
        if pattern:
            suite = self.loader.loadTestsFromNames([pattern], module)
        else:
            suite = self.loader.loadTestsFromModule(module)
        self.runner.test_pattern = pattern
        self.runner.skipped_patterns = skipped
        result = self.runner.run(suite)
        self.runner.test_pattern = None
        self.runner.skipped_patterns = ()
        self.assertEqual(result.testsRun, expected_count)

    def test_collect_everything(self):
        """make sure we don't change the default behaviour
        for loadTestsFromModule() and loadTestsFromTestCase
        """
        testsuite = self.loader.loadTestsFromModule(self.module)
        self.assertEqual(len(testsuite._tests), 2)
        suite1, suite2 = testsuite._tests
        self.assertEqual(len(suite1._tests) + len(suite2._tests), 4)

    def test_collect_with_classname(self):
        self.assertRunCount('FooTC', self.module, 3)
        self.assertRunCount('BarTC', self.module, 1)

    def test_collect_with_classname_and_pattern(self):
        data = [('FooTC.test_foo1', 1), ('FooTC.test_foo', 2), ('FooTC.test_fo', 2),
                ('FooTC.foo1', 1), ('FooTC.foo', 2), ('FooTC.whatever', 0)
                ]
        for pattern, expected_count in data:
            yield self.assertRunCount, pattern, self.module, expected_count

    def test_collect_with_pattern(self):
        data = [('test_foo1', 1), ('test_foo', 2), ('test_bar', 2),
                ('foo1', 1), ('foo', 2), ('bar', 2), ('ba', 2),
                ('test', 4), ('ab', 0),
                ]
        for pattern, expected_count in data:
            yield self.assertRunCount, pattern, self.module, expected_count

    def test_tescase_with_custom_metaclass(self):
        class mymetaclass(type): pass
        class MyMod:
            class MyTestCase(TestCase):
                __metaclass__ = mymetaclass
                def test_foo1(self): pass
                def test_foo2(self): pass
                def test_bar(self): pass
        data = [('test_foo1', 1), ('test_foo', 2), ('test_bar', 1),
                ('foo1', 1), ('foo', 2), ('bar', 1), ('ba', 1),
                ('test', 3), ('ab', 0),
                ('MyTestCase.test_foo1', 1), ('MyTestCase.test_foo', 2),
                ('MyTestCase.test_fo', 2), ('MyTestCase.foo1', 1),
                ('MyTestCase.foo', 2), ('MyTestCase.whatever', 0)
                ]
        for pattern, expected_count in data:
            yield self.assertRunCount, pattern, MyMod, expected_count


    def test_collect_everything_and_skipped_patterns(self):
        testdata = [ (['foo1'], 3), (['foo'], 2),
                     (['foo', 'bar'], 0),
                     ]
        for skipped, expected_count in testdata:
            yield self.assertRunCount, None, self.module, expected_count, skipped


    def test_collect_specific_pattern_and_skip_some(self):
        testdata = [ ('bar', ['foo1'], 2), ('bar', [], 2),
                     ('bar', ['bar'], 0), ]

        for runpattern, skipped, expected_count in testdata:
            yield self.assertRunCount, runpattern, self.module, expected_count, skipped

    def test_skip_classname(self):
        testdata = [ (['BarTC'], 3), (['FooTC'], 1), ]
        for skipped, expected_count in testdata:
            yield self.assertRunCount, None, self.module, expected_count, skipped

    def test_skip_classname_and_specific_collect(self):
        testdata = [ ('bar', ['BarTC'], 1), ('foo', ['FooTC'], 0), ]
        for runpattern, skipped, expected_count in testdata:
            yield self.assertRunCount, runpattern, self.module, expected_count, skipped


    def test_nonregr_dotted_path(self):
        self.assertRunCount('FooTC.test_foo', self.module, 2)


    def test_inner_tests_selection(self):
        class MyMod:
            class MyTestCase(TestCase):
                def test_foo(self): pass
                def test_foobar(self):
                    for i in xrange(5):
                        if i%2 == 0:
                            yield InnerTest('even', lambda: None)
                        else:
                            yield InnerTest('odd', lambda: None)
                    yield lambda: None

        data = [('foo', 7), ('test_foobar', 6), ('even', 3), ('odd', 2),
                ]
        for pattern, expected_count in data:
            yield self.assertRunCount, pattern, MyMod, expected_count

    def test_nonregr_class_skipped_option(self):
        class MyMod:
            class MyTestCase(TestCase):
                def test_foo(self): pass
                def test_bar(self): pass
            class FooTC(TestCase):
                def test_foo(self): pass
        self.assertRunCount('foo', MyMod, 2)
        self.assertRunCount(None, MyMod, 3)
        self.loader.skipped_patterns = self.runner.skipped_patterns = ['FooTC']
        self.assertRunCount('foo', MyMod, 1)
        self.assertRunCount(None, MyMod, 2)

    def test__classes_are_ignored(self):
        class MyMod:
            class _Base(TestCase):
                def test_1(self): pass
            class MyTestCase(_Base):
                def test_2(self): pass
        self.assertRunCount(None, MyMod, 2)


def bootstrap_print(msg, output=sys.stdout):
    """sys.stdout will be evaluated at function parsing time"""
    # print msg
    output.write(msg)

class OutErrCaptureTC(TestCase):

    def setUp(self):
        sys.stdout = sys.stderr = StringIO()
        self.runner = SkipAwareTextTestRunner(stream=StringIO(), exitfirst=True, capture=True)

    def tearDown(self):
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

    @unittest.skipIf(not sys.stdout.isatty(), "need stdout")
    def test_stdout_capture(self):
        class FooTC(TestCase):
            def test_stdout(self):
                print "foo"
                self.assert_(False)
        test = FooTC('test_stdout')
        result = self.runner.run(test)
        captured_out, captured_err = test.captured_output()
        self.assertEqual(captured_out.strip(), "foo")
        self.assertEqual(captured_err.strip(), "")

    @unittest.skipIf(not sys.stderr.isatty(), "need stderr")
    def test_stderr_capture(self):
        class FooTC(TestCase):
            def test_stderr(self):
                print >> sys.stderr, "foo"
                self.assert_(False)
        test = FooTC('test_stderr')
        result = self.runner.run(test)
        captured_out, captured_err = test.captured_output()
        self.assertEqual(captured_out.strip(), "")
        self.assertEqual(captured_err.strip(), "foo")

    @unittest.skipIf(not sys.stderr.isatty(), "need stderr")
    @unittest.skipIf(not sys.stdout.isatty(), "need stdout")
    def test_both_capture(self):
        class FooTC(TestCase):
            def test_stderr(self):
                print >> sys.stderr, "foo"
                print "bar"
                self.assert_(False)
        test = FooTC('test_stderr')
        result = self.runner.run(test)
        captured_out, captured_err = test.captured_output()
        self.assertEqual(captured_out.strip(), "bar")
        self.assertEqual(captured_err.strip(), "foo")

    @unittest.skipIf(not sys.stderr.isatty(), "need stderr")
    @unittest.skipIf(not sys.stdout.isatty(), "need stdout")
    def test_no_capture(self):
        class FooTC(TestCase):
            def test_stderr(self):
                print >> sys.stderr, "foo"
                print "bar"
                self.assert_(False)
        test = FooTC('test_stderr')
        # this runner should not capture stdout / stderr
        runner = SkipAwareTextTestRunner(stream=StringIO(), exitfirst=True)
        result = runner.run(test)
        captured_out, captured_err = test.captured_output()
        self.assertEqual(captured_out.strip(), "")
        self.assertEqual(captured_err.strip(), "")

    @unittest.skipIf(not sys.stdout.isatty(), "need stdout")
    def test_capture_core(self):
        # output = capture_stdout()
        # bootstrap_print("hello", output=sys.stdout)
        # self.assertEqual(output.restore(), "hello")
        output = capture_stdout()
        bootstrap_print("hello")
        self.assertEqual(output.restore(), "hello")

    def test_unicode_non_ascii_messages(self):
        class FooTC(TestCase):
            def test_xxx(self):
                raise Exception(u'\xe9')
        test = FooTC('test_xxx')
        # run the test and make sure testlib doesn't raise an exception
        result = self.runner.run(test)

    def test_encoded_non_ascii_messages(self):
        class FooTC(TestCase):
            def test_xxx(self):
                raise Exception('\xe9')
        test = FooTC('test_xxx')
        # run the test and make sure testlib doesn't raise an exception
        result = self.runner.run(test)


class DecoratorTC(TestCase):

    @with_tempdir
    def test_tmp_dir_normal_1(self):
        tempdir = tempfile.gettempdir()
        # assert temp directory is empty
        self.assertListEqual(list(os.walk(tempdir)),
            [(tempdir,[],[])])

        witness = []

        @with_tempdir
        def createfile(list):
            fd1, fn1 = tempfile.mkstemp()
            fd2, fn2 = tempfile.mkstemp()
            dir = tempfile.mkdtemp()
            fd3, fn3 = tempfile.mkstemp(dir=dir)
            tempfile.mkdtemp()
            list.append(True)
            for fd in (fd1, fd2, fd3):
                os.close(fd)

        self.assertFalse(witness)
        createfile(witness)
        self.assertTrue(witness)

        self.assertEqual(tempfile.gettempdir(), tempdir)

        # assert temp directory is empty
        self.assertListEqual(list(os.walk(tempdir)),
            [(tempdir,[],[])])

    @with_tempdir
    def test_tmp_dir_normal_2(self):

        tempdir = tempfile.gettempdir()
        # assert temp directory is empty
        self.assertListEqual(list(os.walk(tempfile.tempdir)),
            [(tempfile.tempdir,[],[])])


        class WitnessException(Exception):
            pass

        @with_tempdir
        def createfile():
            fd1, fn1 = tempfile.mkstemp()
            fd2, fn2 = tempfile.mkstemp()
            dir = tempfile.mkdtemp()
            fd3, fn3 = tempfile.mkstemp(dir=dir)
            tempfile.mkdtemp()
            for fd in (fd1, fd2, fd3):
                os.close(fd)
            raise WitnessException()

        self.assertRaises(WitnessException, createfile)

        # assert tempdir didn't change
        self.assertEqual(tempfile.gettempdir(), tempdir)

        # assert temp directory is empty
        self.assertListEqual(list(os.walk(tempdir)),
            [(tempdir,[],[])])

    def setUp(self):
        self.pyversion = sys.version_info

    def tearDown(self):
        sys.version_info = self.pyversion

    def test_require_version_good(self):
        """ should return the same function
        """
        def func() :
            pass
        sys.version_info = (2, 5, 5, 'final', 4)
        current = sys.version_info[:3]
        compare = ('2.4', '2.5', '2.5.4', '2.5.5')
        for version in compare:
            decorator = require_version(version)
            self.assertEqual(func, decorator(func), '%s =< %s : function \
                return by the decorator should be the same.' % (version,
                '.'.join([str(element) for element in current])))

    def test_require_version_bad(self):
        """ should return a different function : skipping test
        """
        def func() :
            pass
        sys.version_info = (2, 5, 5, 'final', 4)
        current = sys.version_info[:3]
        compare = ('2.5.6', '2.6', '2.6.5')
        for version in compare:
            decorator = require_version(version)
            self.assertNotEqual(func, decorator(func), '%s >= %s : function \
                 return by the decorator should NOT be the same.'
                 % ('.'.join([str(element) for element in current]), version))

    def test_require_version_exception(self):
        """ should throw a ValueError exception
        """
        def func() :
            pass
        compare = ('2.5.a', '2.a', 'azerty')
        for version in compare:
            decorator = require_version(version)
            self.assertRaises(ValueError, decorator, func)

    def test_require_module_good(self):
        """ should return the same function
        """
        def func() :
            pass
        module = 'sys'
        decorator = require_module(module)
        self.assertEqual(func, decorator(func), 'module %s exists : function \
            return by the decorator should be the same.' % module)

    def test_require_module_bad(self):
        """ should return a different function : skipping test
        """
        def func() :
            pass
        modules = ('bla', 'blo', 'bli')
        for module in modules:
            try:
                __import__(module)
                pass
            except ImportError:
                decorator = require_module(module)
                self.assertNotEqual(func, decorator(func), 'module %s does \
                    not exist : function return by the decorator should \
                    NOT be the same.' % module)
                return
        print 'all modules in %s exist. Could not test %s' % (', '.join(modules),
            sys._getframe().f_code.co_name)

class TagTC(TestCase):

    def setUp(self):
        @tag('testing', 'bob')
        def bob(a, b, c):
            return (a + b) * c

        self.func = bob

        class TagTestTC(TestCase):
            tags = Tags('one', 'two')

            def test_one(self):
                self.assertTrue(True)

            @tag('two', 'three')
            def test_two(self):
                self.assertTrue(True)

            @tag('three', inherit=False)
            def test_three(self):
                self.assertTrue(True)
        self.cls = TagTestTC

    def test_tag_decorator(self):
        bob = self.func

        self.assertEqual(bob(2, 3, 7), 35)
        self.assertTrue(hasattr(bob, 'tags'))
        self.assertSetEqual(bob.tags, set(['testing','bob']))


    def test_tags_class(self):
        tags = self.func.tags

        self.assertTrue(tags['testing'])
        self.assertFalse(tags['Not inside'])

    def test_tags_match(self):
        tags = self.func.tags

        self.assertTrue(tags.match('testing'))
        self.assertFalse(tags.match('other'))

        self.assertFalse(tags.match('testing and coin'))
        self.assertTrue(tags.match('testing or other'))

        self.assertTrue(tags.match('not other'))

        self.assertTrue(tags.match('not other or (testing and bibi)'))
        self.assertTrue(tags.match('other or (testing and bob)'))

    def test_tagged_class(self):
        def options(tags):
            class Options(object):
                tags_pattern = tags
            return Options()

        cls = self.cls

        runner = SkipAwareTextTestRunner()
        self.assertTrue(runner.does_match_tags(cls.test_one))
        self.assertTrue(runner.does_match_tags(cls.test_two))
        self.assertTrue(runner.does_match_tags(cls.test_three))

        runner = SkipAwareTextTestRunner(options=options('one'))
        self.assertTrue(runner.does_match_tags(cls.test_one))
        self.assertTrue(runner.does_match_tags(cls.test_two))
        self.assertFalse(runner.does_match_tags(cls.test_three))

        runner = SkipAwareTextTestRunner(options=options('two'))
        self.assertTrue(runner.does_match_tags(cls.test_one))
        self.assertTrue(runner.does_match_tags(cls.test_two))
        self.assertFalse(runner.does_match_tags(cls.test_three))

        runner = SkipAwareTextTestRunner(options=options('three'))
        self.assertFalse(runner.does_match_tags(cls.test_one))
        self.assertTrue(runner.does_match_tags(cls.test_two))
        self.assertTrue(runner.does_match_tags(cls.test_three))

        runner = SkipAwareTextTestRunner(options=options('two or three'))
        self.assertTrue(runner.does_match_tags(cls.test_one))
        self.assertTrue(runner.does_match_tags(cls.test_two))
        self.assertTrue(runner.does_match_tags(cls.test_three))

        runner = SkipAwareTextTestRunner(options=options('two and three'))
        self.assertFalse(runner.does_match_tags(cls.test_one))
        self.assertTrue(runner.does_match_tags(cls.test_two))
        self.assertFalse(runner.does_match_tags(cls.test_three))



if __name__ == '__main__':
    unittest_main()
