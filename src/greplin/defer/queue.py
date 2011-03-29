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
