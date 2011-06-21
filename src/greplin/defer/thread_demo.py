#!/usr/bin/env python
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

"""PROTOTYPE: Demo of better stacktraces for async calls.  Based on defer.inlineCallbacks."""

from greplin.defer import time
from greplin.defer.thread import async, stacktrace

from twisted.internet import reactor


@async
def demo():
  """Main demo function."""
  yield countdown(4)


@async
def countdown(i):
  """Countdown function to generate chained asynchronous calls."""
  if not i:
    reactor.stop()
    return

  print 'i is %d' % i

  yield time.sleep(0.01)

  print 'done sleeping'

  nestAndPrint()

  yield anotherFunction(i - 1)


@async
def anotherFunction(i):
  """Another function to try to make this even more interesting."""
  yield countdown(i)


def nestAndPrint():
  """Adds a python function frame and then prints the stacktrace."""
  # Python's traceback is not so useful.
  # import traceback; traceback.print_stack()

  # Ours is a bit better.
  print stacktrace()

  print '\n\n\n'



reactor.callWhenRunning(demo)
reactor.run()
