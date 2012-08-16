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
  return Context.currentContext.values[key]


def all():
  """Gets all context values."""
  return Context.currentContext.values


def has(key):
  """Checks if the current context contains the given key."""
  return not not (key in Context.currentContext.values)


# ------------------------------ #
# Implementation details follow. #
# ------------------------------ #

# First, we define a class to represent the current context.


class Context(object):
  """Represents a single context level."""

  currentContext = None


  def __init__(self, values = None):
    self.parent = None
    self.values = Context.currentContext.values.copy() if Context.currentContext else {}
    if values:
      self.values.update(values)


  def __enter__(self):
    """Enters this context."""
    self.parent = Context.currentContext
    Context.currentContext = self


  def __exit__(self, *_):
    """Leaves this context."""

    Context.currentContext = self.parent
    self.parent = None



# Initialize the root context.

Context.currentContext = Context()


# Now we define a utility function for wrapping a function to include the current context.

def wrapped(fn):
  """Returns a wrapped version of fn that installs the current context and then calls fn."""
  context = Context.currentContext

  def wrappedFn(*args, **kw):
    """Wrapped version of the function."""
    Context.currentContext = context
    fn(*args, **kw)

  return wrappedFn



# Define the patched reactor.

# pylint: disable=C0103
BaseReactor = type(reactor)



class ContextTrackingReactor(BaseReactor):
  """Adds context tracking to the reactor."""


  def addReader(self, reader):
    """Overrides addReader to attach the current context."""
    # pylint: disable=W0212
    reader.__context = Context.currentContext
    BaseReactor.addReader(self, reader)


  def addWriter(self, writer):
    """Overrides addWriter to attach the current context."""
    # pylint: disable=W0212
    writer.__context = Context.currentContext
    BaseReactor.addWriter(self, writer)


  # pylint: disable=C0103
  def _doReadOrWrite(self, selectable, *args, **kw):
    """Overrides _doReadOrWrite to restore the context at the time of selectable creation."""
    # pylint: disable=W0212
    Context.currentContext = selectable.__context
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
    if Context.currentContext.values:
      originalResult += ' %r' % Context.currentContext.values
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
