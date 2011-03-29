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
