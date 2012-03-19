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

"""Tests for deferred semaphores."""

from greplin.defer import semaphore

from twisted.internet import defer

import unittest

import functools



class PrioritySemaphoreTest(unittest.TestCase):
  """Tests for deferred priority semaphore"""


  def setUp(self):
    """Sets up the test."""
    self.log = []
    self.queue = semaphore.DeferredPrioritySemaphore(tokens=3)


  def call(self, fn, *args):
    """Calls the function with the given name and args and logs various related events."""
    desc = ' '.join([fn] + list(str(ai) for ai in args))
    self.log.append(desc)
    result = getattr(self.queue, fn)(*args)
    if isinstance(result, defer.Deferred):
      self.log.append('result: Deferred')
      result.addCallback(lambda _: self.log.append('callback ' + desc))
    else:
      self.log.append('result: %s' % result)


  def testBasics(self):
    """Test the basics of a deferred priority semaphore."""
    acq, rel = functools.partial(self.call, 'acquire'), functools.partial(self.call, 'release')
    acq(3)
    acq(4)
    acq(1)
    acq(0)
    acq(5)
    acq(6)
    acq(4)
    rel()
    rel()
    rel()
    acq(0)
    acq(9)
    acq(2)
    rel()
    rel()
    rel()
    rel()
    rel()
    rel()
    rel()

    self.assertEquals(["acquire 3",
                       "result: Deferred",
                       "callback acquire 3",
                       "acquire 4",
                       "result: Deferred",
                       "callback acquire 4",
                       "acquire 1",
                       "result: Deferred",
                       "callback acquire 1",
                       "acquire 0",
                       "result: Deferred",
                       "acquire 5",
                       "result: Deferred",
                       "acquire 6",
                       "result: Deferred",
                       "acquire 4",
                       "result: Deferred",
                       "release",
                       "callback acquire 0",
                       "result: None",
                       "release",
                       "callback acquire 4",
                       "result: None",
                       "release",
                       "callback acquire 5",
                       "result: None",
                       "acquire 0",
                       "result: Deferred",
                       "acquire 9",
                       "result: Deferred",
                       "acquire 2",
                       "result: Deferred",
                       "release",
                       "callback acquire 0",
                       "result: None",
                       "release",
                       "callback acquire 2",
                       "result: None",
                       "release",
                       "callback acquire 6",
                       "result: None",
                       "release",
                       "callback acquire 9",
                       "result: None",
                       "release",
                       "result: None",
                       "release",
                       "result: None",
                       "release",
                       "result: None"
                      ], self.log)

