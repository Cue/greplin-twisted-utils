# Copyright 2012 The greplin-twisted-utils Authors.
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

"""Tests for context storage and restoration."""
from twisted.internet.defer import DeferredList

from greplin.defer import context, inline
from greplin.defer.time import sleep
from greplin.testing.base import BaseDeferredTest

context.install()

from twisted.internet import threads



class ContextTest(BaseDeferredTest):
  """Tests for the context free functions"""


  def testSettingGettingAndHavingContext(self):
    """Should be able to set context, get it, and check for membership"""
    self.assertRaises(KeyError, context.get, 'foo')

    with context.set(foo='bar'):
      self.assertEquals('bar', context.get('foo'))

    self.assertFalse(context.has('foo'))



class ConcurrentContextTests(BaseDeferredTest):
  """Tests for context with deferreds"""


  @inline.callbacks
  def crashy(self):
    """A deferred function that throws"""
    assert False


  @inline.callbacks
  def testContextIsRestoredWhenExceptionsThrown(self):
    """
    When an error occurs in a deferred, context should be restored appropriately
    This test has a follow up that imposes an ordering requirement based on method name.
    """
    self.assertFalse(context.has('foo'))
    try:
      with context.set(foo='bar'):
        self.assert_(context.has('foo'))
        yield threads.deferToThread(self.crashy)
    except AssertionError:
      pass
    self.assertFalse(context.has('foo'))


  @inline.callbacks
  def testContextIsRestoredWhenExceptionsThrownZ(self):
    """This is actually confirmation that testContextIsRestoredWhenExceptionsThrown didn't much about in the parent
    context. The Z in the test name is to ensure it goes afterwards."""
    yield self.assertRaises(KeyError, context.get, 'foo')


  @inline.callbacks
  def notCrashySleep(self, sleepFor, **kwargs):
    """Sleeps for sleepFor seconds and asserts that kwargs is equal to the stored context variables"""
    with context.set(**kwargs):
      yield sleep(sleepFor)
      self.assertEquals(kwargs, context.all())


  @inline.callbacks
  def testDoesntMingleContextAcrossUnyieldedDeferred(self):
    """Deferreds that exist at the same time should not have interacting contexts"""
    self.assertFalse(context.has('a'))
    self.assertFalse(context.has('b'))
    a = self.notCrashySleep(0.01, a=1)
    self.assertFalse(context.has('a'))
    self.assertFalse(context.has('b'))
    b = self.notCrashySleep(0.001, b=2)
    self.assertFalse(context.has('a'))
    self.assertFalse(context.has('b'))

    yield sleep(0.02)
    yield DeferredList([a, b])


  @inline.callbacks
  def notCrashySleepWithNonRootContext(self, sleepFor, parentCtx, **kwargs):
    """Sleeps for sleepFor seconds and then asserts that kwargs + parentCtx is the current context"""
    expected = {}
    expected.update(parentCtx)
    expected.update(kwargs)
    with context.set(**kwargs):
      yield sleep(sleepFor)
      self.assertEquals(expected, context.all())


  @inline.callbacks
  def testMaintainsNonRootContextAcrossUnyieldedDeferred(self):
    """Deferreds that exist at the same time under a parent context should not interfere and have that parent context"""

    with context.set(parent=1):
      a = self.notCrashySleepWithNonRootContext(0.01, {'parent': 1}, a=1)
      b = self.notCrashySleepWithNonRootContext(0.001, {'parent': 1}, b=2)

    yield sleep(0.02)
    yield DeferredList([a, b])

