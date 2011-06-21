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

"""PROTOTYPE: Better stacktraces for async calls.  Based on defer.inlineCallbacks."""

from twisted.internet.defer import Deferred
from twisted.python import failure

import functools
import inspect
import sys
import warnings



class AsyncFrame(object):
  """Represents a single async call frame."""

  def __init__(self, frame):
    self.bottom = frame
    self.top = None



class AsyncThread(object):
  """An asynchronous "thread"."""

  currentThread = None


  def __init__(self, name):
    self.parent = AsyncThread.currentThread
    self.children = []
    self.frames = []
    self.name = name
    self.locals = {}


  def _externalFrame(self):
    """Gets the first frame outside of this module."""
    pythonFrame = inspect.currentframe()
    while id(pythonFrame.f_globals) == id(globals()):
      pythonFrame = pythonFrame.f_back
    return pythonFrame


  def _getStackTrace(self):
    """Gets a stack trace for this thread."""
    result = []
    for asyncFrame in reversed(self.frames):
      pythonFrame = asyncFrame.top or self._externalFrame()
      while pythonFrame and pythonFrame != asyncFrame.bottom and id(pythonFrame.f_globals) != id(globals()):
        frameInfo = inspect.getframeinfo(pythonFrame)
        result.extend(reversed(['  %s' % x for x in frameInfo.code_context]))
        result.append('  File "%s", line %d, in %s\n' % (frameInfo.filename, frameInfo.lineno, frameInfo.function))
        pythonFrame = pythonFrame.f_back
    return ''.join(reversed(result))


  def getStackTrace(self):
    """Gets a stacktrace for this thread merged with its parent threads."""
    if self.parent:
      return '\n'.join((self.parent.getStackTrace(), self._getStackTrace()))
    else:
      return self._getStackTrace()


  def pushFrame(self):
    """Pushes a new frame."""
    if self.frames:
      self.frames[-1].top = self._externalFrame()
    self.frames.append(AsyncFrame(inspect.currentframe().f_back))


  def popFrame(self):
    """Pops a frame."""
    self.frames.pop()
    if self.frames:
      self.frames[-1].top = None


  def setLocal(self, key, value):
    """Sets a thread local."""
    self.locals[key] = value


  def getLocal(self, key):
    """Gets a thread local."""
    return self.locals.get(key)



AsyncThread.currentThread = AsyncThread('ROOT')



class _AsyncReturn(BaseException):
  """Return value. """

  def __init__(self, value):
    BaseException.__init__(self)
    self.value = value


def returnValue(value):
  """Return value from an L{async} generator."""
  raise _AsyncReturn(value)


def _async(result, generator, deferred, thread):
  """See L{async}."""

  AsyncThread.currentThread = thread

  waiting = [True, # waiting for result?
             None] # result

  while 1:
    try:
      # Send the last result back as the result of the yield expression.
      isFailure = isinstance(result, failure.Failure)
      if isFailure:
        result = result.throwExceptionIntoGenerator(generator)
      else:
        result = generator.send(result)
    except StopIteration:
      # fell off the end, or "return" statement
      deferred.callback(None)
      return deferred
    except _AsyncReturn, e:
      _checkBadReturnValue(sys.exc_info(), isFailure)
      deferred.callback(e.value)
      return deferred
    except:
      deferred.errback()
      return deferred

    if isinstance(result, Deferred):
      # a deferred was yielded, get the result.
      def gotResult(r):
        """Called when a deferred finishes."""
        thread.popFrame()
        if waiting[0]:
          waiting[0] = False
          waiting[1] = r
        else:
          _async(r, generator, deferred, thread)

      thread.pushFrame()
      result.addBoth(gotResult)
      if waiting[0]:
        # Haven't called back yet, set flag so that we get reinvoked
        # and return from the loop
        waiting[0] = False
        return deferred

      result = waiting[1]
      # Reset waiting to initial values for next loop.  gotResult uses
      # waiting, but this isn't a problem because gotResult is only
      # executed once, and if it hasn't been executed yet, the return
      # branch above would have been taken.

      waiting[0] = True
      waiting[1] = None

  return deferred


def _checkBadReturnValue(exc, isFailure):
  """Checks for a bad return value."""

  # returnValue() was called; time to give a result to the original
  # Deferred.  First though, let's try to identify the potentially
  # confusing situation which results when returnValue() is
  # accidentally invoked from a different function, one that wasn't
  # decorated with @inlineCallbacks.

  # The traceback starts in this frame (the one for
  # _inlineCallbacks); the next one down should be the application
  # code.
  appCodeTrace = exc[2].tb_next
  if isFailure:
    # If we invoked this generator frame by throwing an exception
    # into it, then throwExceptionIntoGenerator will consume an
    # additional stack frame itself, so we need to skip that too.
    appCodeTrace = appCodeTrace.tb_next
  # Now that we've identified the frame being exited by the
  # exception, let's figure out if returnValue was called from it
  # directly.  returnValue itself consumes a stack frame, so the
  # application code will have a tb_next, but it will *not* have a
  # second tb_next.
  if appCodeTrace.tb_next.tb_next:
    # If returnValue was invoked non-local to the frame which it is
    # exiting, identify the frame that ultimately invoked
    # returnValue so that we can warn the user, as this behavior is
    # confusing.
    ultimateTrace = appCodeTrace
    while ultimateTrace.tb_next.tb_next:
      ultimateTrace = ultimateTrace.tb_next
    filename = ultimateTrace.tb_frame.f_code.co_filename
    lineno = ultimateTrace.tb_lineno
    warnings.warn_explicit(
        'returnValue() in %r causing %r to exit: '
        'returnValue should only be invoked by functions decorated with async' %
        (ultimateTrace.tb_frame.f_code.co_name, appCodeTrace.tb_frame.f_code.co_name),
        DeprecationWarning, filename, lineno)


def async(f):
  """Wraps the given function, allowing use of the yield keyword to make asynchronous code look synchronous."""
  @functools.wraps(f)
  def unwindGenerator(*args, **kwargs):
    """Decorated version that returns the generator and sets it up to be processed asynchronously."""
    return _async(None, f(*args, **kwargs), Deferred(), AsyncThread.currentThread)


  return unwindGenerator


def stacktrace():
  """Dumps the current stacktrace as a string."""
  return AsyncThread.currentThread.getStackTrace()


def getLocal(key):
  """Gets a thread local value."""
  return AsyncThread.currentThread.getLocal(key)


def getLocals():
  """Gets all thread local values."""
  return AsyncThread.currentThread.locals


def setLocal(key, value):
  """Sets a thread local value."""
  return AsyncThread.currentThread.setLocal(key, value)
