# Copyright 2013 The greplin-twisted-utils Authors.
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

"""Implementation of deferToEventlet that defers to a thread that uses Eventlet."""

import collections
import functools
import Queue
import os
import threading

from remember import memoize

from twisted.internet import defer, reactor
from twisted.python import failure

import eventlet
import eventlet.greenio
import eventlet.hubs


PIPE_READ, PIPE_WRITE = os.pipe()
PIPE_READ = eventlet.greenio.GreenPipe(PIPE_READ)
QUEUE = collections.deque([])


def _loop():
  """The main loop in the Eventlet thread."""
  for option in ('epolls', 'poll', 'selects'):
    try:
      eventlet.hubs.use_hub(option)
      break
    except (ImportError, AttributeError):
      pass

  while PIPE_READ.read(1) == '1':
    fn, args, kw, out, queue = QUEUE.popleft()
    eventlet.spawn(_runOne, fn, args, kw, out, queue)


def _runOne(fn, args, kw, out, queue):
  """Runs a single eventlet task."""
  try:
    result = fn(*args, **kw)
    if out:
      reactor.callFromThread(out.callback, result)
    else:
      queue.put(result)
  except: # OK to be generic here since basically re-throw. # pylint: disable=W0702
    f = failure.Failure()
    if out:
      reactor.callFromThread(out.errback, f)
    else:
      queue.put(f)


@memoize.memoize()
def _getThread():
  """Lazy loads the eventlet thread."""
  thread = threading.Thread(target = _loop)
  thread.daemon = True # We have to set this to true since tests don't cleanly shut down the reactor.
  thread.start()
  reactor.addSystemEventTrigger('during', 'shutdown', _stopThread)
  return thread


def _stopThread():
  """Stops the thread."""
  os.write(PIPE_WRITE, '0')


def deferToEventlet(fn, *args, **kw):
  """Defers the given task to eventlet."""
  out = defer.Deferred()
  QUEUE.append((fn, args, kw, out, None))
  os.write(PIPE_WRITE, '1')
  return out


def runInEventletThreadAndWait(fn, *args, **kw):
  """Runs the given task in the eventlet thread and blocks until it is finished."""
  queue = Queue.Queue()
  QUEUE.append((fn, args, kw, None, queue))
  os.write(PIPE_WRITE, '1')
  result = queue.get()
  if isinstance(result, failure.Failure):
    result.raiseException()
  return result


def deferred(fn):
  """Decorator for functions that use eventlet and should be run in a separate thread and return a deferred."""
  @functools.wraps(fn)
  def actual(*args, **kw):
    """The actual method for deferred runs."""
    if _getThread() == threading.currentThread():
      return fn(*args, **kw)
    else:
      return deferToEventlet(fn, *args, **kw)
  return actual


def blocking(fn):
  """Decorator for functions that run in eventlet and block the calling thread until finished."""
  @functools.wraps(fn)
  def actual(*args, **kw):
    """The actual method for blocking runs."""
    if _getThread() == threading.currentThread():
      return fn(*args, **kw)
    else:
      return runInEventletThreadAndWait(fn, *args, **kw)
  return actual


def decorateMethods(obj):
  """Returns a decorated version of object that defers its methods to the eventlet thread."""
  return _EventletProxy(obj)



class _EventletProxy(object):
  """Object that wraps access to another object to run in the eventlet thread and return deferreds."""

  def __init__(self, target):
    self.__target = target


  def __getattr__(self, item):
    original = getattr(self.__target, item)
    if hasattr(original, '__call__'):
      return deferred(original)
    else:
      return original
