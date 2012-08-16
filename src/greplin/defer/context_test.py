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

from greplin.defer import context, inline
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



class ADeferToThreadContextTest(BaseDeferredTest):
  """Tests for context with deferToThread"""


  @inline.callbacks
  def crashy(self):
    """A deferred function that throws"""
    assert False


  @inline.callbacks
  def testContextIsRestoredWhenExceptionsThrown(self):
    """
    When an error occurs in a deferred, context should be restored appropriately
    This test has a follow up (testD..) that imposes an ordering requirement based on method name.
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
