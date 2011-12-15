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

"""Deferred classes for threading."""

import functools

import Queue

from twisted.internet import reactor, threads
from twisted.python import failure



class ThreadWrapper(object):
  """Object that wraps access to another object inside a thread.

  Methods on the old object can be called as originally named for blocking access.

  Alternately, a method like "doSlowWork" can be called as "asyncDoSlowWork" and will return a deferred instead.
  """

  def __init__(self, threadPool, fn, *args, **kw):
    self.__threadPool = threadPool

    self.__threadPool.threadFactory = functools.partial(self.__threadFactory, self.__threadPool.threadFactory)
    self.__threadPool.start()

    self.__target = self.__block(fn, *args, **kw)


  def __threadFactory(self, original, *args, **kw):
    """Thread factory that marks threads as daemons."""
    thread = original(*args, **kw)
    thread.daemon = True
    return thread


  def __block(self, fn, *args, **kw):
    """Calls the given function in a thread pool."""
    queue = Queue.Queue()
    self.__threadPool.callInThreadWithCallback(lambda *result: queue.put(result), fn, *args, **kw)
    result = queue.get()[1]
    if isinstance(result, failure.Failure):
      result.raiseException()
    return result


  def __getattr__(self, item):
    async = item.startswith('async')
    if async:
      item = item[5].lower() + item[6:]

    original = getattr(self.__target, item)
    if hasattr(original, '__call__'):
      if async:
        return functools.partial(threads.deferToThreadPool, reactor, self.__threadPool, original)
      else:
        return functools.partial(self.__block, original)
    else:
      return original
