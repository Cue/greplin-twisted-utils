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

"""Priority Deferred Semaphore object."""


from twisted.internet import defer

import heapq



class DeferredPrioritySemaphore(defer._ConcurrencyPrimitive): #pylint: disable=W0212
  """
  A semaphore for event driven systems.

  @ivar tokens: At most this many users may acquire this semaphore at
      once.
  @type tokens: C{int}

  @ivar limit: The difference between C{tokens} and the number of users
      which have currently acquired this semaphore.
  @type limit: C{int}
  """

  def __init__(self, tokens):
    defer._ConcurrencyPrimitive.__init__(self) #pylint: disable=W0212
    if tokens < 1:
      raise ValueError("DeferredSemaphore requires tokens >= 1")
    self.tokens = tokens
    self.limit = tokens


  def _cancelAcquire(self, d):
    """
    Remove a deferred d from our waiting list, as the deferred has been
    canceled.

    Note: We do not need to wrap this in a try/except to catch d not
    being in self.waiting because this canceller will not be called if
    d has fired. release() pops a deferred out of self.waiting and
    calls it, so the canceller will no longer be called.

    @param d: The deferred that has been canceled.
    """
    for e in self.waiting:
      if e[1] == d:
        self.waiting.remove(e)
        #TODO - Improve from O(n * log(n))
        heapq.heapify(self.waiting)
        break



  def acquire(self, priority=0):
    """
    Attempt to acquire the token.

    @param priority: Priority by default is 0.

    @return: a L{Deferred} which fires on token acquisition.
    """
    assert self.tokens >= 0, "Internal inconsistency?? Tokens should never be negative"
    d = defer.Deferred(canceller=self._cancelAcquire)
    if not self.tokens:
      heapq.heappush(self.waiting, (priority, d))
    else:
      self.tokens = self.tokens - 1
      d.callback(self)
    return d


  def release(self):
    """
    Release the token.

    Should be called by whoever did the L{acquire}() when the shared
    resource is free.
    """
    assert self.tokens < self.limit, "Someone released me too many times: too many tokens!"
    self.tokens = self.tokens + 1
    if self.waiting:
      # someone is waiting to acquire token
      self.tokens = self.tokens - 1
      _, d = heapq.heappop(self.waiting)
      d.callback(self)

