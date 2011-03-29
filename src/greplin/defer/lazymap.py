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
      self.__fn(key).addCallback(self.__gotItem, key).addErrback(self.__err, key)

    return result


  def __gotItem(self, value, key):
    """Handle successful item retrieval."""
    self[key] = value
    observers = self.__loading[key]
    del self.__loading[key]
    for observer in observers:
      observer.callback(value)


  def __err(self, err, key):
    """Handle an error in fn."""
    self[key] = err
    observers = self.__loading[key]
    del self.__loading[key]
    for observer in observers:
      observer.errback(err)
