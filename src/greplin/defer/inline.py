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

from greplin.defer import base, context

from twisted.internet import defer
from twisted.python import failure

import functools



def callbacks(fn):
  """Decorator to make asyncronous code look synchronous.  See twisted.internet.defer.inlineCallbacks."""

  isMethod = fn.__code__.co_varnames[:1] == ('self',)   # Is this a method?

  @functools.wraps(fn)
  def call(*args, **kwargs):
    """The new function."""
    # Save and restore the context afterwards so fn() doesn't interfere with other deferreds
    current = context.current()
    reprFn = None
    if args[:1] and hasattr(args[0], 'describeDeferred'):
      reprFn = args[0].describeDeferred
    className = None
    if isMethod and args:
      try:
        className = args[0].__class__.__name__
      except AttributeError:
        pass
    d = InlinedCallbacks(fn(*args, **kwargs), reprFn=reprFn, className=className)
    context.setCurrent(current)

    if d.called:
      if isinstance(d.result, failure.Failure):
        f = d.result
        d.addErrback(lambda _: None) # Eat the error so we don't get Unhandled Error In Deferred.
        f.raiseException()
      else:
        return d.result
    else:
      return d

  return call



STATE_NORMAL = 0

STATE_WAITING = 1

STATE_CANCELLED = 2



# We (sadly) actually save quite a bit of memory by always using the same empty dict and tuple objects.

EMPTY_TUPLE = tuple()

EMPTY_DICT = dict()



# pylint is just wrong about this being an old style class.  # pylint: disable=E1001
class InlinedCallbacks(base.LowMemoryDeferred):
  """Class to maintain state for an inlined callback."""

  __slots__ = ('_current', '_generator', '_state', '_context')


  def __init__(self, generator, reprFn=None, className=None):
    base.LowMemoryDeferred.__init__(self)
    self._generator = generator
    self._state = STATE_NORMAL
    self._current = None
    self._context = context.current()
    self._step(None)
    self._reprFn = reprFn
    self._className = className


  def __canceller(self, _):
    """Cancel this Deferred by cancelling the current Deferred it's waiting on."""
    self._state = STATE_CANCELLED
    if self._current:
      self._current.cancel()


  def cancel(self):
    """Custom cancel method that only bind the canceller when it's about to be used."""
    self._canceller = self.__canceller # Here it's worth it to reference the parent var.  # pylint: disable=W0201
    base.LowMemoryDeferred.cancel(self)


  def _step(self, result):
    """Takes a single step in the generator / deferred interaction."""

    # Largely based on the twisted.internet.defer.inlineCallbacks implementation.

    # This function is complicated by the need to prevent unbounded recursion
    # arising from repeatedly yielding immediately ready deferreds.  This while
    # loop and the waiting variable solve that by manually unfolding the
    # recursion.
    while self._state != STATE_CANCELLED:
      try:
        # Send the last result back as the result of the yield expression.
        if isinstance(result, failure.Failure):
          result = result.throwExceptionIntoGenerator(self._generator)
        else:
          result = self._generator.send(result)
      except StopIteration:
        # Fell off the end, or "return" statement
        if self._state != STATE_CANCELLED:
          self.callback(None)
        return
      except defer._DefGen_Return, e: # Need to access protected member for consistency. # pylint: disable=W0212
        if self._state != STATE_CANCELLED:
          context.setCurrent(self._context)
          self.callback(e.value)
        return
      except:
        self.errback()
        return

      if self._state == STATE_NORMAL and isinstance(result, defer.Deferred):
        # A deferred was yielded, get the result.
        self._current = result
        self._state = STATE_WAITING
        cb = self._handleResult
        result.addCallbacks(cb, cb, EMPTY_TUPLE, EMPTY_TUPLE, EMPTY_DICT, EMPTY_DICT)
        if self._state == STATE_WAITING:
          # Haven't called back yet, set flag so that we get reinvoked and return from the loop.
          self._state = STATE_NORMAL
          return

        result = self._current
        self._current = None


  def _handleResult(self, result):
    """Handles a result from a deferred."""
    if self._state == STATE_WAITING:
      self._state = STATE_NORMAL
      self._current = result
    else:
      self._step(result)


  def describeDeferred(self):
    """Describes this Deferred."""
    generatorName = self._generator.__name__
    if self._className is not None:
      generatorName = self._className + '.' + generatorName
    if self._reprFn:
      return '%s (%s):%s -> %s' % (generatorName, self._reprFn(), self._state,
                                   base.describeDeferred(self._current))
    else:
      return '%s:%s -> %s' % (generatorName, self._state, base.describeDeferred(self._current))
