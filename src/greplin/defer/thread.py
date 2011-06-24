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

from twisted.internet import reactor, threads
from twisted.python import log

import inspect
import itertools
import sys
import weakref


# TODO: monkey patch tracebacks
# TODO: how to handle exception tracebacks?
# TODO: performance impact?


ID_GENERATOR = itertools.count(1)



class AsyncFrame(object):
  """Represents a single async call frame."""

  currentFrame = None

  byName = weakref.WeakValueDictionary()


  def __init__(self, parent, frame, kind = 'Frame'):
    self.parent = parent
    self.children = weakref.WeakKeyDictionary()

    self.frames = []
    if frame:
      while frame and frame != AsyncFrame.currentFrame.reentry:
        self.frames.append(inspect.getframeinfo(frame))
        frame = frame.f_back

    self.reentry = None

    self.locals = None

    self.kind = kind


  def createChild(self, kind = 'Frame'):
    """Creates a child frame."""
    frame = AsyncFrame(self, _externalFrame(), kind)
    self.children[frame] = 1
    return frame


  def getName(self):
    """Returns the name of this frame, generating one if necessary."""
    if not self.locals or 'name' not in self.locals:
      self.setName('%s %d' % (self.kind, ID_GENERATOR.next()))
    return self.getLocal('name')


  def setName(self, name):
    """Sets the name of this frame."""
    self.setLocal('name', name)


  def setLocal(self, key, value):
    """Sets a value that is local to this frame or its ancestors."""
    self.locals = self.locals or {}
    self.locals[key] = value
    if key == 'name':
      AsyncFrame.byName[value] = self


  def getLocal(self, key):
    """Gets a value that is local to this frame or its ancestors."""
    if self.locals and key in self.locals:
      return self.locals[key]
    elif self.parent:
      return self.parent.getLocal(key)


  def getLocals(self):
    """Gets all locals from this frame and its ancestors."""
    if self.parent:
      combination = self.parent.getLocals()
    else:
      combination = {}
    if self.locals:
      combination.update(self.locals)
    return combination


  def stacktrace(self, reverse = False):
    """Generates a stacktrace."""
    result = []
    asyncFrame = self
    while asyncFrame:
      for frameInfo in asyncFrame.frames:
        frameLines = []
        if not frameInfo.filename.endswith('twisted/internet/defer.py'):
          frameLines.extend(reversed(['      %s\n' % x.strip() for x in frameInfo.code_context]))
        frameLines.append('  File "%s", line %d, in %s\n' % (frameInfo.filename, frameInfo.lineno, frameInfo.function))
        result.extend(reversed(frameLines) if reverse else frameLines)
      result.append('--- async %s ---\n' % asyncFrame.getName())
      asyncFrame = asyncFrame.parent
    return ''.join(result if reverse else reversed(result))


ROOT_FRAME = AsyncFrame.currentFrame = AsyncFrame(None, None)
AsyncFrame.currentFrame.setName('ROOT')


def _externalFrame():
  """Gets the first frame outside of this module."""
  pythonFrame = inspect.currentframe()
  while id(pythonFrame.f_globals) == id(globals()):
    pythonFrame = pythonFrame.f_back
  return pythonFrame


def stacktrace():
  """Gets a stack trace for this thread."""
  return AsyncFrame.currentFrame.createChild().stacktrace()


def getCurrentFrame():
  """Gets the current frame."""
  return AsyncFrame.currentFrame


def getLocal(key):
  """Gets a thread local value."""
  return AsyncFrame.currentFrame.getLocal(key)


def getLocals():
  """Gets all thread local values."""
  return AsyncFrame.currentFrame.getLocals()


def setLocal(key, value):
  """Sets a thread local value."""
  return AsyncFrame.currentFrame.setLocal(key, value)



class Locals(object):
  """Represents a set of locals."""

  currentContext = None


  def __init__(self, values = None):
    self.parent = None
    self.values = values


  def __enter__(self):
    """Enters this context."""
    AsyncFrame.currentFrame = AsyncFrame.currentFrame.createChild('Set Locals')
    for key, value in self.values.items():
      AsyncFrame.currentFrame.setLocal(key, value)


  def __exit__(self, *_):
    """Leaves this context."""
    AsyncFrame.currentFrame = AsyncFrame.currentFrame.parent


def locals(**values): # pylint: disable=W0622
  """Sets thread locals in a context."""
  return Locals(values)



# ------------------------------- #
# Beware - monkey patching ahead. #
# ------------------------------- #


# Now we define a utility function for wrapping a function to restore the current frame.

def wrapped(fn, kind):
  """Returns a wrapped version of fn that installs the current context and then calls fn."""
  frame = AsyncFrame.currentFrame.createChild(kind)

  def wrappedFn(*args, **kw):
    """Wrapped version of the function."""
    AsyncFrame.currentFrame = frame
    frame.reentry = inspect.currentframe()
    fn(*args, **kw)

  return wrappedFn



# Define the patched reactor.

# pylint: disable=C0103
BaseReactor = type(reactor)



class FrameTrackingReactor(BaseReactor):
  """Adds frame tracking to the reactor."""


  def addReader(self, reader):
    """Overrides addReader to attach the current context."""
    reader.__frame = AsyncFrame.currentFrame.createChild('Reader')
    BaseReactor.addReader(self, reader)


  def addWriter(self, writer):
    """Overrides addWriter to attach the current context."""
    writer.__frame = AsyncFrame.currentFrame.createChild('Writer')
    BaseReactor.addWriter(self, writer)


  # pylint: disable=C0103
  def _doReadOrWrite(self, selectable, *args, **kw):
    """Overrides _doReadOrWrite to restore the context at the time of selectable creation."""
    # pylint: disable=W0212
    AsyncFrame.currentFrame.reentry = inspect.currentframe()
    BaseReactor._doReadOrWrite(self, selectable, *args, **kw)


  def callLater(self, _seconds, _f, *args, **kw):
    """Wraps call later functions with the context."""
    return BaseReactor.callLater(self, _seconds, wrapped(_f, 'Timer'), *args, **kw)


# Last piece of the official API - function to install the patches.

def install():
  """Install the context tracking reactor."""

  # Install logging patches.
  originalFormatter = log.textFromEventDict

  def newFormatter(*args, **kw):
    """Augmented log formatter that includes context information."""
    originalResult = originalFormatter(*args, **kw)
    values = AsyncFrame.currentFrame.getLocals()
    if values:
      originalResult += ' %r' % values
    return originalResult

  log.textFromEventDict = newFormatter


  # Patch threads.deferToThread(Pool)
  originalDeferToThreadPool = threads.deferToThreadPool

  def deferToThreadPool(*args, **kw):
    """Patches defer to thread pool to install the context when running the callback."""
    deferred = originalDeferToThreadPool(*args, **kw)
    # pylint: disable=W0212
    deferred._startRunCallbacks = wrapped(deferred._startRunCallbacks, 'Thread')
    return deferred

  threads.deferToThreadPool = deferToThreadPool


  # Overwrite the reactor.
  del sys.modules['twisted.internet.reactor']
  r = FrameTrackingReactor()
  from twisted.internet.main import installReactor
  installReactor(r)
