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

"""Tests for the retry.retryCall utility function."""

from greplin.defer import retry, time

from twisted.internet import defer
from twisted.trial import unittest



class BadException(Exception):
  """Unacceptable exception."""
  pass



class OkException(Exception):
  """Ok exception."""
  pass



class LoggingSleeper(object):
  """Fake sleep manager that logs actions."""

  def __init__(self, log):
    self.log = log


  def sleep(self):
    """Fake sleep by just returning right away."""
    self.log.append('sleep')
    return time.sleep(0)



class RetryCallTest(unittest.TestCase):
  """Tests for retryCall."""


  def setUp(self):
    """Sets up the test."""
    self.log = []
    self.steps = []
    self.expectedArgs = (1, 1, 2, 3, 5, 8)
    self.expectedKeywords = {'abc': 'tuna'}


  def _function(self, *args, **keywordArgs):
    """The function we'll retry."""
    self.log.append('function')

    self.assertEquals(self.expectedArgs, args)
    self.assertEquals(self.expectedKeywords, keywordArgs)

    nextStep = self.steps.pop(0)
    if isinstance(nextStep, Exception):
      return defer.fail(nextStep)
    else:
      return defer.succeed(nextStep)


  def _checkFailure(self, err):
    """The failure checker - it allows OkException."""
    self.log.append('testFailure')
    err.trap(OkException)


  def _logFailure(self, _):
    """Logs failures."""
    self.log.append('failed')


  def _logResult(self, value):
    """Logs successes."""
    self.log.append(value)


  def checkLog(self, _, expectedLog):
    """Checks if the log matched what was expected."""
    self.assertEquals(expectedLog, self.log)


  def assertLog(self, steps, expectedLog):
    """Main function - args are the result steps of the function and the expected log that results."""
    self.steps = steps
    d = retry.retryCall(
        self._function, self.expectedArgs, self.expectedKeywords, self._checkFailure, LoggingSleeper(self.log))
    d.addCallbacks(self._logResult, self._logFailure)
    d.addCallback(self.checkLog, expectedLog)
    return d


  def testWorksOnFirstTry(self):
    """Tests the basic case of the function succeeding on the first try."""
    return self.assertLog([
      100
    ], [
        'function',
      100
    ])


  def testOkExceptions(self):
    """Tests the more interesting case of the function failing a few times before succeeding."""
    return self.assertLog([
      OkException(),
      OkException(),
      200
    ], [
      'function',
      'testFailure',
      'sleep',
      'function',
      'testFailure',
      'sleep',
      'function',
      200
    ])


  def testBadException(self):
    """Tests the more interesting case of the function failing a few times before succeeding."""
    return self.assertLog([
      BadException()
    ], [
      'function',
      'testFailure',
      'failed'
    ])


  def testOkExceptionsBeforeBad(self):
    """Tests the more interesting case of the function failing a few times before succeeding."""
    return self.assertLog([
      OkException(),
      OkException(),
      BadException()
    ], [
      'function',
      'testFailure',
      'sleep',
      'function',
      'testFailure',
      'sleep',
      'function',
      'testFailure',
      'failed'
    ])
