# Copyright 2010 Greplin, Inc.  All Rights Reserved.

"""Mixin for waiting on deferreds, and cancelling them if needed."""

from twisted.internet import defer



class WaitMixin():
  """Mixin for waiting on deferreds, and cancelling them if needed.

    The isRunning() method can be overridden for subclasses that want to reject waits once stopped.
    """

  __currentWait = None


  def isRunning(self):
    """The base implementation is always running."""
    return True


  def _wait(self, deferred):
    """Waits for the given deferred."""
    if self.isRunning():
      if deferred:
        self.__currentWait = deferred
        return deferred.addBoth(self.__clearWait)
    else:
      if deferred:
        deferred.cancel()
      raise defer.CancelledError


  def __clearWait(self, result):
    """Clears the current wait."""
    self.__currentWait = None
    return result


  def _cancelWait(self):
    """Cancels the deferred currently being waited for."""
    if self.__currentWait:
      self.__currentWait.cancel()
