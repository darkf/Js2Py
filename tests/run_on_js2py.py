from __future__ import print_function

import sys

sys.path.insert(0, "..")
import js2py
from js2py.base import PyJsException, PyExceptionToJs
import os, sys, re, traceback, threading, ctypes, time, six
from distutils.version import LooseVersion

def load(path):
    with open(path, 'r') as f:
        return f.read()

def terminate_thread(thread):
    """Terminates a python thread from another thread.

    :param thread: a threading.Thread instance
    """
    if not thread.isAlive():
        return

    exc = ctypes.py_object(SystemExit)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(thread.ident), exc)
    if res == 0:
        raise ValueError("nonexistent thread id")
    elif res > 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.ident, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")

TEST_TIMEOUT = 10
INCLUDE_PATH = 'includes/'
TEST_PATH = 'test_cases/'
INIT = load(os.path.join(INCLUDE_PATH, 'init.js'))

class TestCase:
    description = None
    includes = None
    author = None
    es5id = None
    negative = None
    info = None
    flags = []
    CATEGORY_REQUIRES_SPLIT = {'flags', 'includes'}

    def __init__(self, path):

        self.path = path
        self.full_path = os.path.abspath(self.path)
        self.clear_name = '/'.join(self.full_path.split(os.sep)[-3 - ('prototype' in self.full_path):-1])
        self.raw = load(self.path)

        self._parse_test_info()

        self.init = INIT

        if self.includes:
            for include in self.includes:
                self.init += load(os.path.join(INCLUDE_PATH, include))
        if 'onlyStrict' in self.flags:
            self.strict_only = True
        else:
            self.strict_only = False

        self.code = self.init + self.raw

    def _parse_test_info(self):
        self.raw_info = re.search('/\*---(.+)---\*/', self.raw, re.DOTALL).groups()[0].strip()
        category = None
        category_content = None
        for line in self.raw_info.splitlines() + ['END:']:
            if line.startswith(' '):
                if category is None:
                    raise RuntimeError('Could not parse test case info! %s' % self.path)
                category_content += '\n' + line.lstrip()
            else:
                if category is not None:
                    content = category_content.strip()
                    content = content if not category in self.CATEGORY_REQUIRES_SPLIT else self._content_split(content)
                    setattr(self, category, content)
                start_index = line.index(':')
                category = line[:start_index]
                category_content = line[start_index + 1:].lstrip(' >\n')

    def _content_split(self, content):
        res = []
        for c in content.splitlines():
            cand = c.strip('[] -')
            if cand:
                if ', ' in cand:
                    for e in cand.split(','):
                        res.append(e.strip())
                else:
                    res.append(cand)
        return res

    def run(self):
        # labels: 'PASSED', 'FAILED', 'CRASHED', 'NOT_IMPLEMENTED', 'NO_FAIL'
        errors = True
        crashed = True
        label = None
        try:
            js2py.eval_js(self.code)
            errors = False
            crashed = False

        except NotImplementedError:
            tb = sys.exc_info()[-1]
            stk = traceback.extract_tb(tb)
            fname = stk[-1][2]
            passed = False
            reason = 'Not implemented - "%s"' % fname
            full_error = traceback.format_exc()
            label = 'NOT_IMPLEMENTED'

        except PyJsException as e:
            crashed = False
            full_error = traceback.format_exc()
            if self.negative:
                passed = True
            else:
                passed = False
                reason = PyExceptionToJs(e).get('message').to_python()
                label = 'FAILED'


        except SyntaxError as e:
            full_error = traceback.format_exc()
            if self.negative == 'SyntaxError':
                passed = True
            else:
                passed = False
                reason = 'Could not parse'
                label = 'CRASHED'

        except:
            full_error = traceback.format_exc()
            passed = False
            reason = 'UNKNOWN - URGENT, FIX NOW!'
            label = 'CRASHED'

        if not errors:
            if self.negative:
                passed = False
                reason = "???"
                label = "NO_FAIL"
                full_error = ''
            else:
                passed = True

        if passed:
            label = "PASSED"
            reason = ''
            full_error = ''

        self.passed, self.label, self.reason, self.full_error = passed, label, reason, full_error

def all_tests(path):
    for dirpath, _, filenames in os.walk(path):
        yield from (os.path.join(dirpath, filename) for filename in filenames if filename.endswith(".js"))

def test_all(path):
    files = list(all_tests(path))
    num_tests = len(files)

    for i,filename in enumerate(files):
        try:
            test = TestCase(filename)
            if test.strict_only:
                continue

            thread = threading.Thread(target=test.run)
            timeout_time = time.time() + TEST_TIMEOUT
            thread.start()
            while thread.is_alive() and time.time() < timeout_time:
                time.sleep(0.001)
            if thread.is_alive():
                terminate_thread(thread)
                test.passed = False
                test.full_error = 'TERMINATED'
                test.label = 'TIMEOUT'
                test.reason = '?'

            print("[%d/%d]" % (i, num_tests), test.clear_name, test.es5id, test.label, test.reason,
                  '\nFile "%s", line 1' % test.full_path if test.label == 'CRASHED' else '')
        except:
            print(traceback.format_exc())
            print(filename)
            input()

if __name__ == "__main__":
    test_all(TEST_PATH)
