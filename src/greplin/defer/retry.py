# Copyright 2010 Greplin, Inc.  All Rights Reserved.

"""Call that automatically retries."""

from greplin.defer import time

from twisted.internet import defer


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
    defer.Deferred.__init__(self)
    self.__fn = fn
    self.__failureTester = failureTester
    self.__sleepManager = sleepManager or time.SleepManager()
    self.__args = args or []
    self.__keywordArgs = keywordArgs or {}
    self.__currentTry = None
    self.__tryCall()


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
      self.errback(err)
    else:
      self.__sleepManager.sleep().addCallback(self.__tryCall)
