# Copyright 2011 The greplin-twisted-utils Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for the inline.callbacks utility function."""

from greplin.defer import inline, time

from twisted.internet import defer
from twisted.trial import unittest



class InlineCallbacksTest(unittest.TestCase):
  """Tests for inlineCallbacks."""


  def testCancellation(self):
    """Tests cancellation of inlined callbacks. """
    # With old defer.inlineCallbacks, this fails the "clean reactor" checks in the base class.

    @inline.callbacks
    def sleeper():
      """Simple asynchronous function that sleeps for a long time."""
      yield time.sleep(100)

    d = sleeper()
    d.addErrback(lambda _: None)
    d.cancel()


  def testSimple(self):
    """Tests return of a simple value."""

    @inline.callbacks
    def simple():
      """Simple asynchronous function that returns a value."""
      yield time.sleep(0.01)
      defer.returnValue(5)

    return simple().addBoth(lambda result: self.assertEqual(5, result))


  def testTuple(self):
    """Tests return of a tuple."""

    @inline.callbacks
    def tupleReturn():
      """Simple asynchronous function that returns a tuple."""
      yield time.sleep(0.01)
      defer.returnValue((5, 'abc'))

    return tupleReturn().addBoth(lambda result: self.assertEqual((5, 'abc'), result))


  def testUnroll(self):
    """Tests that a large stack isn't created."""

    @inline.callbacks
    def instantYields():
      """Simple asynchronous function that has instant results for a large number of yields."""
      for i in xrange(1000):
        yield i
      defer.returnValue('done')

    return instantYields().addBoth(lambda result: self.assertEqual('done', result))


  def testYieldValues(self):
    """Tests that yields receive the proper values."""

    a = defer.Deferred()
    b = defer.succeed(2)
    c = defer.Deferred()

    @inline.callbacks
    def results():
      """Tests result handling."""
      total = yield a
      total += yield b
      x, y = yield c
      total += x + y
      defer.returnValue(total)

    out = results()
    self.assertFalse(bool(out.called))

    a.callback(1)
    self.assertFalse(bool(out.called))

    c.callback((3, 4))
    self.assertTrue(out.called)
    self.assertEqual(10, out.result)
