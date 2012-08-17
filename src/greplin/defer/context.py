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

"""Context tracking across deferred callbacks."""
import threading

from twisted.internet import reactor, threads
from twisted.python import log

import sys


# Methods used to update / read from the context.  This is the official API of this module.

# pylint: disable=W0622
def set(**args):
  """Creates a 'with'-compatible context with the given values set."""
  return Context(args)


def get(key):
  """Gets context values from the current context."""
  return current().values[key]


def all():
  """Gets all context values."""
  return current().values


def has(key):
  """Checks if the current context contains the given key."""
  return not not (key in current().values)


# ------------------------------ #
# Implementation details follow. #
# ------------------------------ #

# First, we define a class to represent the current context.

THREAD_CONTEXT = threading.local()
ROOT_CONTEXT = None # Forward declaration


def current():
  """Returns the current context for this thread."""
  try:
    THREAD_CONTEXT.current # does it exist?
  except AttributeError:
    if not ROOT_CONTEXT:
      return None
    THREAD_CONTEXT.current = ROOT_CONTEXT

  return THREAD_CONTEXT.current


def setCurrent(ctx):
  """Updates the current context"""
  THREAD_CONTEXT.current = ctx



class Context(object):
  """Represents a single context level."""

  def __init__(self, values = None):
    self.parent = None
    self.values = all().copy() if current() else {}
    if values:
      self.values.update(values)


  def __enter__(self):
    """Enters this context."""
    self.parent = current()
    setCurrent(self)


  def __exit__(self, *_):
    """Leaves this context."""

    setCurrent(self.parent)
    self.parent = None


# Initialize the root context.
ROOT_CONTEXT = Context()


# Now we define a utility function for wrapping a function to include the current context.

def wrapped(fn):
  """Returns a wrapped version of fn that installs the current context and then calls fn."""
  context = current()

  def wrappedFn(*args, **kw):
    """Wrapped version of the function."""
    setCurrent(context)
    fn(*args, **kw)

  return wrappedFn



# Define the patched reactor.

# pylint: disable=C0103
BaseReactor = type(reactor)



class ContextTrackingReactor(BaseReactor):
  """Adds context tracking to the reactor."""


  def addReader(self, reader):
    """Overrides addReader to attach the current context."""
    # This accesses private variables on purpose
    # pylint: disable=W0212
    reader.__context = current()
    BaseReactor.addReader(self, reader)


  def addWriter(self, writer):
    """Overrides addWriter to attach the current context."""
    # This accesses private variables on purpose
    # pylint: disable=W0212
    writer.__context = current()
    BaseReactor.addWriter(self, writer)


  # pylint: disable=C0103
  def _doReadOrWrite(self, selectable, *args, **kw):
    """Overrides _doReadOrWrite to restore the context at the time of selectable creation."""
    # pylint: disable=W0212
    setCurrent(selectable.__context)
    BaseReactor._doReadOrWrite(self, selectable, *args, **kw)


  def callLater(self, _seconds, _f, *args, **kw):
    """Wraps call later functions with the context."""
    return BaseReactor.callLater(self, _seconds, wrapped(_f), *args, **kw)


# Last piece of the official API - function to install the patches.

def install():
  """Install the context tracking reactor."""

  # Install logging patches.
  originalFormatter = log.textFromEventDict

  def newFormatter(*args, **kw):
    """Augmented log formatter that includes context information."""
    originalResult = originalFormatter(*args, **kw)
    if all():
      originalResult += ' %r' % all()
    return originalResult

  log.textFromEventDict = newFormatter


  # Patch threads.deferToThread(Pool)
  originalDeferToThreadPool = threads.deferToThreadPool

  def deferToThreadPool(*args, **kw):
    """Patches defer to thread pool to install the context when running the callback."""
    deferred = originalDeferToThreadPool(*args, **kw)
    # pylint: disable=W0212
    deferred._startRunCallbacks = wrapped(deferred._startRunCallbacks)
    return deferred

  threads.deferToThreadPool = deferToThreadPool


  # Overwrite the reactor.
  del sys.modules['twisted.internet.reactor']
  r = ContextTrackingReactor()
  from twisted.internet.main import installReactor
  installReactor(r)
