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

from greplin.defer import thread, time
thread.install()

from twisted.internet import defer, threads
from twisted.web import client

import unittest




class ContextTrackerTest(unittest.TestCase):
  """Test the context tracking system."""

  @defer.inlineCallbacks
  def testInlineCallbacks(self):
    """Test context saving across I/O."""
    with thread.locals(someValue = 12345):
      yield time.sleep(0.001)
      self.assertEqual(None, thread.getLocal('anotherValue'))
      self.assertEqual(12345, thread.getLocal('someValue'))

      with thread.locals(anotherValue = 'abcde'):
        yield client.getPage('http://greplin.com')
        self.assertEqual('abcde', thread.getLocal('anotherValue'))
        self.assertEqual(12345, thread.getLocal('someValue'))

      yield threads.deferToThread(lambda: None)
      self.assertEqual(None, thread.getLocal('anotherValue'))
      self.assertEqual(12345, thread.getLocal('someValue'))

    self.assertEqual(None, thread.getLocal('someValue'))


  def testFromRequest(self):
    """Test saving context across a socket request."""
    with thread.locals(source = 'page'):
      return client.getPage('http://greplin.com').addCallback(
          lambda _: self.assertEqual('page', thread.getLocal('source')))


  def testFromThread(self):
    """Test saving context across a thread deferment."""
    with thread.locals(source = 'thread'):
      return threads.deferToThread(lambda: None). \
          addCallback(lambda _: self.assertEqual('thread', thread.getLocal('source')))


  def testFromDelay(self):
    """Test saving context across a delayed call."""
    with thread.locals(source = 'delay'):
      return time.sleep(0.001).addCallback(lambda _: self.assertEqual('delay', thread.getLocal('source')))
