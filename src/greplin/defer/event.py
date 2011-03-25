# Copyright 2010 Greplin, Inc.  All Rights Reserved.

"""An event that can have many observers."""

from twisted.internet import defer



class DeferredEvent(object):
  """Pub-sub model for an event using Deferreds"""

  def __init__(self):
    self.__observers = []


  def addListener(self):
    """Adds a listener to the event, returning a deferred that will be fired the next time the event is fired."""
    deferred = defer.Deferred()
    self.__observers.append(deferred)
    return deferred


  def fire(self, result = None):
    """Fires the event, calling back each listener."""
    observers = self.__observers
    self.__observers = []
    for observer in observers:
      observer.callback(result)
