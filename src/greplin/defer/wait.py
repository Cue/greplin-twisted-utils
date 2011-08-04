# Copyright 2010 Greplin, Inc.  All Rights Reserved.

"""Mixin for waiting on deferreds, and cancelling them if needed."""



class WaitMixin(object):
  """Mixin for waiting on deferreds, and cancelling them if needed."""

  __currentWait = None


  def _wait(self, deferred):
    """Waits for the given deferred."""
    self.__currentWait = deferred
    if deferred:
      return deferred.addBoth(self.__clearWait)


  def __clearWait(self, _):
    """Clears the current wait."""
    self.__currentWait = None


  def _cancelWait(self):
    """Cancels the deferred currently being waited for."""
    if self.__currentWait:
      self.__currentWait.cancel()
