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

"""Decorator to make asyncronous code look synchronous.  See twisted.internet.defer.inlineCallbacks."""

from twisted.internet import defer
from twisted.python import failure

import functools



def callbacks(fn):
  """Decorator to make asyncronous code look synchronous.  See twisted.internet.defer.inlineCallbacks."""

  @functools.wraps(fn)
  def call(*args, **kwargs):
    """The new function."""
    return InlinedCallbacks(fn(*args, **kwargs)).deferred

  return call



class InlinedCallbacks(object):
  """Class to maintain state for an inlined callback."""

  __slots__ = ('_current', 'deferred', '_generator', '_waiting')


  def __init__(self, generator):
    self._generator = generator
    self.deferred = defer.Deferred(self._canceller)
    self._waiting = True
    self._current = None
    self._step(None)


  def _canceller(self, _):
    """Cancel this Deferred by cancelling the current Deferred it's waiting on."""
    self._current.cancel()


  def _step(self, result):
    """Takes a single step in the generator / deferred interaction."""

    # Largely based on the twisted.internet.defer.inlineCallbacks implementation.

    # This function is complicated by the need to prevent unbounded recursion
    # arising from repeatedly yielding immediately ready deferreds.  This while
    # loop and the waiting variable solve that by manually unfolding the
    # recursion.

    while 1:
      try:
        # Send the last result back as the result of the yield expression.
        if isinstance(result, failure.Failure):
          result = result.throwExceptionIntoGenerator(self._generator)
        else:
          result = self._generator.send(result)
      except StopIteration:
        # Fell off the end, or "return" statement
        self.deferred.callback(None)
        return
      except defer._DefGen_Return, e: # Need to access protected member for consistency. # pylint: disable=W0212
        self.deferred.callback(e.value)
        return
      except:
        self.deferred.errback()
        return

      if isinstance(result, defer.Deferred):
        # A deferred was yielded, get the result.
        self._current = result
        self._waiting = True
        result.addBoth(self._handleResult)
        if self._waiting:
          # Haven't called back yet, set flag so that we get reinvoked and return from the loop.
          self._waiting = False
          return

        result = self._current
        self._current = None


  def _handleResult(self, result):
    """Handles a result from a deferred."""
    if self._waiting:
      self._waiting = False
      self._current = result
    else:
      self._step(result)
