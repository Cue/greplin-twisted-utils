# Copyright 2010 Greplin, Inc.  All Rights Reserved.

"""Mocks out greplin.time.sleep."""

from greplin.defer import time

from twisted.internet import defer
from twisted.python import failure



class MockSleep(object):
  """Mocks out greplin.time.sleep."""

  __oldSleep = None

  __queue = []


  def expect(self, seconds):
    """Adds an expected sleep."""
    self.__queue.append(seconds)


  def __sleep(self, seconds):
    """Substitute for time.sleep."""
    expectedSeconds = self.__queue.pop(0)
    if expectedSeconds != seconds:
      err = AssertionError("Expected sleep for %s seconds, got %s" % (expectedSeconds, seconds))
      return defer.fail(failure.Failure(err))
    return defer.succeed(None)


  def __enter__(self):
    """Installs the fake time class."""
    self.__queue = []
    self.__oldSleep = time.sleep
    time.sleep = self.__sleep
    return self


  def __exit__(self, _, __, ___):
    """Restores the real time class."""
    time.sleep = self.__oldSleep
    assert not self.__queue, "Queue not empty: %s" % self.__queue
