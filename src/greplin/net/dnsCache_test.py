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

from greplin.net import dnsCache

from twisted.internet import defer, error
from twisted.python import failure



class CachingDNSTest(unittest.TestCase):
  """Tests for caching DNS."""

  def testFallback(self):
    """Test a cache with fallback."""
    original = mox.MockAnything()
    original.getHostByName('google.com').AndReturn(
        defer.succeed('1.2.3.4'))
    original.getHostByName('google.com').AndReturn(
        defer.fail(failure.Failure(error.DNSLookupError('Fake DNS failure'))))
    original.getHostByName('google.com').AndReturn(
        defer.succeed('9.8.7.6'))
    mox.Replay(original)

    cache = dnsCache.CachingDNS(original, timeout = 0)
    result = cache.getHostByName('google.com')
    self.assertEquals(result.result, '1.2.3.4')
    result = cache.getHostByName('google.com')
    self.assertEquals(result.result, '1.2.3.4')
    result = cache.getHostByName('google.com')
    self.assertEquals(result.result, '9.8.7.6')
    mox.Verify(original)


  def testNoFallback(self):
    """Test a cache with fallback."""
    original = mox.MockAnything()
    original.getHostByName('google.com').AndReturn(
        defer.succeed('1.2.3.4'))
    original.getHostByName('google.com').AndReturn(
        defer.fail(failure.Failure(error.DNSLookupError('Fake DNS failure'))))
    original.getHostByName('google.com').AndReturn(
        defer.succeed('9.8.7.6'))
    mox.Replay(original)

    cache = dnsCache.CachingDNS(original, timeout = 0, useFallback = False)
    result = cache.getHostByName('google.com')
    self.assertEquals(result.result, '1.2.3.4')
    result = cache.getHostByName('google.com')
    self.assertTrue(isinstance(result.result, failure.Failure))
    result.addErrback(lambda _: None) # Consume the error.
    result = cache.getHostByName('google.com')
    self.assertEquals(result.result, '9.8.7.6')
    mox.Verify(original)
