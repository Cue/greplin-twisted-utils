# Copyright 2010 Greplin, Inc.  All Rights Reserved.

"""Wrap a deferred to handle the final state of it."""

from twisted.python import failure, log


def wrapDeferred(deferred, ignore = None, onError = None, onSuccess = None, onComplete = None):
  """Log deferred errors and also ensure any error will be marked as handled.

  Calls the following methods in order:

  onError (if result was an error and not one in ignore)
  onSuccess (if result was not an error)
  onComplete (no matter what)

  The result is the return value of onComplete, which is passed the result from above.
  """

  def handleEndOfDeferredChain(result):
    """Errback handler that logs, adds a callback to ignore the passed through error, and returns the error."""
    if isinstance(result, failure.Failure):
      if ignore and result.check(*ignore):
        result = None
      else:
        result = onError(result)

    elif onSuccess:
      result = onSuccess(result)

    return onComplete(result)


  def addEndOfChainCallback(result):
    """Adds a callback that will be called at the end of the callback chain."""
    deferred.addBoth(handleEndOfDeferredChain)
    return result


  return deferred.addBoth(addEndOfChainCallback)


def logger(message, **context):
  """Create a logger function with the given message."""
  return lambda err: log.err(err, message, **context)
