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

"""Net enabled tests for context tracking."""

from greplin.defer import context, time
context.install()

from twisted.internet import defer, threads
from twisted.web import client

import unittest




class ContextTrackerTest(unittest.TestCase):
  """Test the context tracking system."""

  @defer.inlineCallbacks
  def testInlineCallbacks(self):
    """Test context saving across I/O."""
    with context.set(someValue = 12345):
      yield time.sleep(0.001)
      self.assertFalse(context.has('anotherValue'))
      self.assertEqual(12345, context.get('someValue'))
      self.assertTrue(context.has('someValue'))

      with context.set(anotherValue = 'abcde'):
        yield client.getPage('http://greplin.com')
        self.assertEqual('abcde', context.get('anotherValue'))
        self.assertEqual(12345, context.get('someValue'))

      yield threads.deferToThread(lambda: None)
      self.assertFalse(context.has('anotherValue'))
      self.assertEqual(12345, context.get('someValue'))
      self.assertTrue(context.has('someValue'))

    self.assertFalse(context.has('someValue'))


  def testFromRequest(self):
    """Test saving context across a socket request."""
    with context.set(source = 'page'):
      return client.getPage('http://greplin.com').addCallback(lambda _: self.assertEqual('page', context.get('source')))


  def testFromThread(self):
    """Test saving context across a thread deferment."""
    with context.set(source = 'thread'):
      return threads.deferToThread(lambda: None). \
          addCallback(lambda _: self.assertEqual('thread', context.get('source')))


  def testFromDelay(self):
    """Test saving context across a delayed call."""
    with context.set(source = 'delay'):
      return time.sleep(0.001).addCallback(lambda _: self.assertEqual('delay', context.get('source')))
