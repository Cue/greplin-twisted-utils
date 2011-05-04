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

"""DeferredMap class."""


from twisted.internet import defer



class DeferredMap(dict):
  """Calls the given function on each of the items added to the queue.  Each item can itself be deferred."""

  def __init__(self, fn):
    dict.__init__(self)
    self.__fn = fn
    self.__loading = {}


  def refresh(self, key):
    """Forces a refresh of the given item.  If it is currently loading or not loaded, this does nothing."""
    if key in self and not isinstance(dict.__getitem__(self, key), defer.Deferred):
      dict.__delitem__(self, key)


  def __getitem__(self, key):
    """Override getitem to lazily load items.  Returns a deferred if the item is not ready, or the item otherwise."""
    if key in self:
      return dict.__getitem__(self, key)

    isNewRequest = key not in self.__loading

    if isNewRequest:
      self.__loading[key] = []

    result = defer.Deferred()
    self.__loading[key].append(result)

    if isNewRequest:
      self.__fn(key).addBoth(self.__gotResult, key)

    return result


  def __isActive(self, key):
    """Checks if the given key is active."""
    return self.__loading.get(key)


  def __set(self, key, result):
    """Calls back the observers for the given key."""
    dict.__setitem__(self, key, result)
    observers = self.__loading.get(key)
    if observers:
      del self.__loading[key]
      for observer in observers:
        observer.callback(result)


  def __setitem__(self, key, value):
    """Proactively sets an item. If the item was loading, any callbacks are called and loading will be canceled."""
    oldValue = key in self and dict.__getitem__(self, key)
    self.__set(key, value)
    if isinstance(oldValue, defer.Deferred):
      oldValue.cancel()


  def __gotResult(self, result, key):
    """Handle a result."""
    if self.__isActive(key):
      self.__set(key, result)
