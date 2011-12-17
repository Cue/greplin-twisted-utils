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

"""Wrap a deferred to handle the final state of it."""

from twisted.python import failure, log



class _Wrapper(object):
  """Helper object for wrapping Deferred objects."""

  __slots__ = ('deferred', 'ignore', 'onError', 'onSuccess', 'onComplete')


  def __init__(self, deferred, ignore, onError, onSuccess, onComplete):
    self.deferred = deferred
    self.ignore = ignore
    self.onError = onError
    self.onSuccess = onSuccess
    self.onComplete = onComplete


  def handleResult(self, result):
    """Handles the initial result of the deferred."""
    self.deferred.addBoth(self.handleEndOfDeferredChain)
    return result


  def handleEndOfDeferredChain(self, result):
    """Handles the end of the deferred chain."""
    if isinstance(result, failure.Failure):
      if self.ignore and result.check(*self.ignore):
        result = None
      elif self.onError:
        result = self.onError(result)

    elif self.onSuccess:
      result = self.onSuccess(result)

    return self.onComplete(result) if self.onComplete else result


def wrapDeferred(deferred, ignore = None, onError = None, onSuccess = None, onComplete = None):
  """Log deferred errors and also ensure any error will be marked as handled.

  Calls the following methods in order:

  onError (if result was an error and not one in ignore)
  onSuccess (if result was not an error)
  onComplete (no matter what)

  The result is the return value of onComplete, which is passed the result from above.
  """
  return deferred.addBoth(_Wrapper(deferred, ignore, onError, onSuccess, onComplete).handleResult)


def logger(message, **context):
  """Create a logger function with the given message."""
  return lambda err: log.err(err, message, **context)
