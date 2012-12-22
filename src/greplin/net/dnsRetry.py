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

"""DNS resolver that uses a short lived local cache to improve performance."""

from greplin.defer import inline, time

from twisted.internet import defer, interfaces

from zope.interface import implements

import logging



class RetryingDNS(object):
  """DNS resolver that retries on failure."""
  implements(interfaces.IResolverSimple)


  def __init__(self, original, tries = 5, sleep = time.SleepManager(5, 60, 10)):
    self._original = original
    self._tries = tries
    self._sleep = sleep


  @inline.callbacks
  def getHostByName(self, name, *args):
    """Gets a host by name."""
    sleepManager = None
    for tryIndex in range(self._tries):
      try:
        result = yield self._original.getHostByName(name, *args)
        defer.returnValue(result)
      except Exception: # This is intended to catch general exceptions! # pylint: disable=W0703
        if tryIndex == self._tries - 1:
          raise
        else:
          logging.warning('Failed to resolve %s', name, exc_info = True)
      sleepManager = sleepManager or self._sleep.clone()
      yield sleepManager.sleep()
