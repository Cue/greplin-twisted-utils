# Copyright 2010 Greplin, Inc.  All Rights Reserved.

"""Tests for the DeferredMap class."""

from greplin.defer import lazymap

from twisted.internet import defer
from twisted.python import failure

import unittest



class DeferredMapTest(unittest.TestCase):
  """Tests for DeferredMap."""

  def setUp(self):
    """Clears test state."""
    self.__results = []
    self.__log = []
    self.__map = lazymap.DeferredMap(self.getDeferred)


  def getDeferred(self, key):
    """Creates a new deferred each time it is called."""
    self.logAppend('key', key)
    self.__results.append(defer.Deferred())
    return self.__results[-1]


  def logAppend(self, *args):
    """Appends args to the log."""
    self.__log.append(args)


  def assertLog(self, *events):
    """Asserts the log entries are as expected, then clears the log."""

    # Process actual, replacing failures with something we can actually compare.
    actual = []
    for entry in self.__log:
      if isinstance(entry[0], failure.Failure):
        actual.append(entry[0].value.args + entry[1:])
      else:
        actual.append(entry)

    self.assertEquals(list(events), actual)
    self.__log = []


  def getAndLog(self, key, tag):
    """Gets a value and adds callbacks to log the result."""
    result = self.__map[key]
    self.assertTrue(isinstance(result, defer.Deferred))
    result.addCallback(self.logAppend, tag, 'success')
    result.addErrback(self.logAppend, tag, 'error')
    return result


  def testBasics(self):
    """Test basics of the deferred map."""
    self.getAndLog(10, '10A')
    self.assertEquals(1, len(self.__results))

    self.assertLog(('key', 10))
    self.__results[-1].callback(100)
    self.assertLog((100, '10A', 'success'))

    self.assertEquals(100, self.__map[10])


  def testInstantResult(self):
    """Test the deferred map when results are instant."""
    self.__map = lazymap.DeferredMap(defer.succeed)

    self.assertEquals(10, self.__map[10].result)
    self.assertEquals(10, self.__map[10])
    self.assertEquals(20, self.__map[20].result)
    self.assertEquals(20, self.__map[20])


  def testSimultaneousRead(self):
    """Test when two keys are read at the same time.."""
    self.getAndLog(10, '10A')
    self.assertEquals(1, len(self.__results))
    self.assertLog(('key', 10))

    self.getAndLog(10, '10B')
    self.assertEquals(1, len(self.__results))
    self.assertLog()

    self.__results[-1].callback(100)
    self.assertLog(
        (100, '10A', 'success'),
        (100, '10B', 'success')
    )

    self.assertEquals(100, self.__map[10])


  def testTwoKeys(self):
    """Test two keys."""
    self.getAndLog(10, '10A')
    self.assertEquals(1, len(self.__results))
    self.assertLog(('key', 10))

    self.getAndLog(20, '20A')
    self.assertEquals(2, len(self.__results))
    self.assertLog(('key', 20))

    self.__results[-2].callback(100)
    self.assertLog((100, '10A', 'success'))

    self.__results[-1].errback(TypeError("AN ERROR"))
    self.assertLog(("AN ERROR", '20A', 'error'))
