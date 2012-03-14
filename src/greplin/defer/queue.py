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

"""Deferred queue classes."""


from collections import deque

from greplin.defer import event

from twisted.internet import defer

import heapq



class MaxSizeQueue(object):
  """A queue with a maximum size.  When full, puts return a deferred that should be waited on before adding more."""

  def __init__(self, maxSize):
    self.__maxSize = maxSize
    self.__queue = deque()
    self.__queueTooFullEvent = None


  def _waitForSpace(self):
    """Gets a defer that represents the queue being too full."""
    self.__queueTooFullEvent = self.__queueTooFullEvent or event.DeferredEvent()
    return self.__queueTooFullEvent.addListener()


  def waitForSpace(self):
    """If the queue is overfull, waits until it is less full."""
    if self.isFull():
      return self._waitForSpace()


  def isEmpty(self):
    """Returns whether the queue is empty."""
    return len(self.__queue) == 0


  def isFull(self):
    """Returns true if there are more items in the queue that the maximum allowed."""
    return len(self.__queue) >= self.__maxSize


  def clear(self):
    """Clears the queue."""
    self.__queue.clear()
    self.__checkIfNoLongerFull()


  def push(self, *items):
    """Push the following items asynchronously.  Will defer if the queue is particularly full."""
    self.__queue.extend(items)
    if self.isFull():
      return self._waitForSpace()
    else:
      return None


  def peek(self):
    """Peek at the front item."""
    return self.__queue[0]


  def shift(self):
    """Pop an item and return it.  This may also callback the queue too full defer."""
    result = self.__queue.popleft()
    self.__checkIfNoLongerFull()
    return result


  def shiftMany(self, n):
    """Pop n items and return them.  This may also callback the queue too full defer."""
    if len(self.__queue) > n:
      result = [self.__queue.popleft() for _ in xrange(n)]
    else:
      result = tuple(self.__queue)
      self.__queue.clear()
    self.__checkIfNoLongerFull()
    return result


  def __checkIfNoLongerFull(self):
    """Checks if the queue is no longer full, firing the no longer full event if so."""
    if self.__queueTooFullEvent and len(self.__queue) < self.__maxSize:
      # If the queue is small enough again, let the fetchers continue working.
      d = self.__queueTooFullEvent
      self.__queueTooFullEvent = None
      d.fire(None)


  def __len__(self):
    """Returns the length of the queue."""
    return len(self.__queue)



class MaxSizeDeferredQueue(MaxSizeQueue):
  """A queue with a maximum size and the ability to wait for items."""

  def __init__(self, maxSize, backlog = 0):
    MaxSizeQueue.__init__(self, maxSize)
    self.__backlogSize = backlog
    self.__backlog = deque()


  def push(self, *items):
    """Push the following items asynchronously.  Will defer if the queue is particularly full."""
    result = MaxSizeQueue.push(self, *items)
    while not self.isEmpty() and self.__backlog:
      deferred = self.__backlog.popleft()
      deferred.callback(self.shift())
    return result


  def shift(self):
    """Pop an item and return it.  Return a deferred if empty.  This may also callback the queue too full defer."""
    if self.isEmpty():
      if len(self.__backlog) == self.__backlogSize:
        raise defer.QueueUnderflow()
      deferred = defer.Deferred()
      self.__backlog.append(deferred)
      return deferred
    else:
      return MaxSizeQueue.shift(self)



class DeferredPriorityQueue(object):
  """Similar to DeferredQueue
     - http://twistedmatrix.com/trac/browser/tags/releases/twisted-11.1.0/twisted/internet/defer.py#L1372
     Objects may be added as usual to this queue.  When an attempt is
     made to retrieve an object when the queue is empty, a L{Deferred} is
     returned which will fire when an object becomes available.

    @ivar sortKey: The function used to sort this priority queue

    @ivar size: The maximum number of objects to allow into the queue
    at a time.  When an attempt to add a new object would exceed this
    limit, L{QueueOverflow} is raised synchronously.  C{None} for no limit.

    @ivar backlog: The maximum number of L{Deferred} gets to allow at
    one time.  When an attempt is made to get an object which would
    exceed this limit, L{QueueUnderflow} is raised synchronously.  C{None}
    for no limit.
  """


  def __init__(self, sortKey=None, size=None, backlog=None):
    self.waiting = []
    self.pending = [] #This is le heap
    self.size = size
    self.backlog = backlog
    self.sortKey = sortKey


  def _cancelGet(self, d):
    """
    Remove a deferred d from our waiting list, as the deferred has been
    canceled.

    Note: We do not need to wrap this in a try/except to catch d not
    being in self.waiting because this canceller will not be called if
    d has fired. put() pops a deferred out of self.waiting and calls
    it, so the canceller will no longer be called.

    @param d: The deferred that has been canceled.
    """
    self.waiting.remove(d)


  def put(self, obj):
    """
    Add an object to this queue.

    @raise QueueOverflow: Too many objects are in this queue.
    """
    if self.waiting:
      self.waiting.pop(0).callback(obj)
    elif self.size is None or len(self.pending) < self.size:
      heapq.heappush(self.pending, (self.sortKey(obj), obj))
    else:
      raise defer.QueueOverflow()


  def get(self):
    """
    Attempt to retrieve and remove an object from the queue.

    @return: a L{Deferred} which fires with the next object available in
    the queue.

    @raise QueueUnderflow: Too many (more than C{backlog})
    L{Deferred}s are already waiting for an object from this queue.
    """
    if self.pending:
      return defer.succeed(heapq.heappop(self.pending)[1])
    elif self.backlog is None or len(self.waiting) < self.backlog:
      d = defer.Deferred(canceller=self._cancelGet)
      self.waiting.append(d)
      return d
    else:
      raise defer.QueueUnderflow()


  def clear(self):
    """Clear this queue."""
    if self.pending:
      self.pending = []
