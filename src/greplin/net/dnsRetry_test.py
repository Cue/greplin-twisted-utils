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

import mox
import unittest

from greplin.defer import time
from greplin.net import dnsRetry

from twisted.internet import defer, error
from twisted.python import failure



class RetryingDNSTest(unittest.TestCase):
  """Tests for retrying DNS."""

  def testOneTry(self):
    """Test a single try cache."""
    original = mox.MockAnything()
    original.getHostByName('google.com').AndReturn(
        defer.fail(failure.Failure(error.DNSLookupError('Fake DNS failure'))))
    original.getHostByName('google.com').AndReturn(
        defer.succeed('1.2.3.4'))
    mox.Replay(original)

    cache = dnsRetry.RetryingDNS(original, tries=1)
    self.assertRaises(error.DNSLookupError, cache.getHostByName, 'google.com')

    result = cache.getHostByName('google.com')
    self.assertEquals(result, '1.2.3.4')
    mox.Verify(original)


  def testTwoTries(self):
    """Test a two try cache."""
    original = mox.MockAnything()
    original.getHostByName('google.com').AndReturn(
        defer.fail(failure.Failure(error.DNSLookupError('Fake DNS failure'))))
    original.getHostByName('google.com').AndReturn(
        defer.succeed('1.2.3.4'))
    mox.Replay(original)

    cache = dnsRetry.RetryingDNS(original, tries=2, sleep=time.SleepManager(0, 0, 0))
    result = cache.getHostByName('google.com')
    self.assertEquals(result, '1.2.3.4')
    mox.Verify(original)
