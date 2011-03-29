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

"""Mocks out greplin.time.sleep."""

from greplin.defer import time

from twisted.internet import defer
from twisted.python import failure



class MockSleep(object):
  """Mocks out greplin.time.sleep."""

  __oldSleep = None

  __queue = []


  def expect(self, seconds):
    """Adds an expected sleep."""
    self.__queue.append(seconds)


  def __sleep(self, seconds):
    """Substitute for time.sleep."""
    expectedSeconds = self.__queue.pop(0)
    if expectedSeconds != seconds:
      err = AssertionError("Expected sleep for %s seconds, got %s" % (expectedSeconds, seconds))
      return defer.fail(failure.Failure(err))
    return defer.succeed(None)


  def __enter__(self):
    """Installs the fake time class."""
    self.__queue = []
    self.__oldSleep = time.sleep
    time.sleep = self.__sleep
    return self


  def __exit__(self, _, __, ___):
    """Restores the real time class."""
    time.sleep = self.__oldSleep
    assert not self.__queue, "Queue not empty: %s" % self.__queue
