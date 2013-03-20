# Copyright 2013 The greplin-twisted-utils Authors.
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

"""Tests for implementation of deferToEventlet that defers to a thread that uses Eventlet."""

from eventlet.green import time as greenTime

from greplin.defer import inline, time, twistlet

from twisted.internet import defer
from twisted.trial import unittest



class DeferToEventletTest(unittest.TestCase):
  """Tests for defer to eventlet."""

  _messages = None


  def setUp(self):
    """Sets up for each test case."""
    self._messages = []


  @inline.callbacks
  def _deferSleepAndAppend(self, amount, message):
    """Runs a sleep in Twisted."""
    yield time.sleep(amount)
    self._messages.append(message)


  @twistlet.deferred
  def _greenSleepAndAppend(self, amount, message):
    """Runs a sleep in eventlet."""
    greenTime.sleep(amount)
    self._messages.append(message)


  @inline.callbacks
  def testInterleave(self):
    """Test interleaved green and twisted sleeps."""
    yield defer.DeferredList([
      self._deferSleepAndAppend(0.1, 'd1'),
      self._greenSleepAndAppend(0.05, 'g1'),
      self._deferSleepAndAppend(0.15, 'd2')
    ])
    self.assertEqual(['g1', 'd1', 'd2'], self._messages)


  @inline.callbacks
  def testInterleaveOtherWay(self):
    """Test interleaved green and twisted sleeps in the opposite order."""
    yield defer.DeferredList([
      self._greenSleepAndAppend(0.1, 'g1'),
      self._deferSleepAndAppend(0.05, 'd1'),
      self._greenSleepAndAppend(0.15, 'g2')
    ])
    self.assertEqual(['d1', 'g1', 'g2'], self._messages)
