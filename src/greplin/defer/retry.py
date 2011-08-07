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

from greplin.defer import time

from twisted.internet import defer
from twisted.python import failure


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
  return RetryingCall(fn, failureTester, sleepManager, args, keywordArgs)



class RetryingCall(defer.Deferred):
  """Class storing necessary data for a retrying call."""

  def __init__(self, fn, failureTester, sleepManager, args, keywordArgs):
    defer.Deferred.__init__(self, self._cancelCleanly)
    self.__fn = fn
    self.__failureTester = failureTester
    self.__sleepManager = sleepManager or time.SleepManager()
    self.__args = args or []
    self.__keywordArgs = keywordArgs or {}
    self.__currentTry = None
    self.__tryCall()



  def _cancelCleanly(self, *_, **__):
    """
    Cancelled requests will throw a CancelledError wherever they were
    initiated from if they haven't yet been called. That means the canceller
    won't always be able to respond to the error (which makes HttpClient.stop a
    problem). Instead, we just mark any cancelled requests as having been
    called.
    """

    self.called = True


  def __tryCall(self, _=None):
    """Tries the call."""
    self.__currentTry = self.__fn(*self.__args, **self.__keywordArgs)
    self.__currentTry.addCallbacks(self.callback, self.__handleError)


  def cancel(self):
    """Cancels the retrying call, as well as the current try."""
    self.__currentTry.cancel()
    defer.Deferred.cancel(self)


  def __handleError(self, err):
    """Determine if the error was allowed.  If not, errback.  If so, delay and try again."""
    try:
      self.__failureTester(err)

    # pylint: disable=W0702
    except:
      self.errback(failure.Failure())
    else:
      self.__sleepManager.sleep().addCallback(self.__tryCall)
