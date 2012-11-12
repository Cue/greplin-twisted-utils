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

"""Call that automatically retries."""

from greplin.defer import inline, time

from twisted.internet import defer
from twisted.python import failure


@inline.callbacks
def retryCall(fn, args=None, keywordArgs=None, failureTester=None, sleepManager=None):
  """Calls the given function, automatically retrying as necessary.

  Arguments:
    fn: The function to call.
    failureTester: Function called with a failure.  The failure should be re-raised if it is not allowable.
    sleepManager: A sleep manager to control how long to sleep between retries.
    args: Args to pass to the function.
    keywordArgs: keywordArgs to pass to the function.

  Returns:
    A deferred that will be called on success.
  """
  sleepManager = sleepManager or time.SleepManager()
  while True:
    try:
      result = yield fn(*args, **keywordArgs)
      defer.returnValue(result)
    except Exception: # pylint: disable=W0703
      failureTester(failure.Failure())
      yield sleepManager.sleep()



class RetryCall(object):
  """Identical functionality to retryCall, but tracks the number of iterations and description of the last error"""


  def __init__(self):
    self.iteration = 0
    self.lastError = None


  @inline.callbacks
  def __call__(self, fn, args=None, keywordArgs=None, failureTester=None, sleepManager=None):
    """Calls the given function, automatically retrying as necessary.

    Arguments:
      fn: The function to call.
      failureTester: Function called with a failure.  The failure should be re-raised if it is not allowable.
      sleepManager: A sleep manager to control how long to sleep between retries.
      args: Args to pass to the function.
      keywordArgs: keywordArgs to pass to the function.

    Returns:
      A deferred that will be called on success.
    """
    sleepManager = sleepManager or time.SleepManager()
    while True:
      try:
        result = yield fn(*args, **keywordArgs)
        defer.returnValue(result)
      except Exception as e: # pylint: disable=W0703
        self.lastError = e
        failureTester(failure.Failure())
        yield sleepManager.sleep()
      finally:
        self.iteration += 1


  def describeDeferred(self):
    """Prints a description of what's going on in the retry call"""
    return "RetryCall(iteration=%s, lastError=%s)" % (self.iteration, self.lastError)

