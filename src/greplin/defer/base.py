# Copyright 2012 The greplin-twisted-utils Authors.
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

"""Lower memory verion of a Deferred object."""

from __future__ import absolute_import

from twisted.internet import defer

import time


DEFERRED_ATTRIBUTES = tuple([name for name in dir(defer.Deferred)
                             if not name.startswith('__') and not hasattr(getattr(defer.Deferred, name), '__call__')])



class LowMemoryDeferred(object, defer.Deferred):
  """Lower memory verion of a Deferred object."""

  __slots__ = DEFERRED_ATTRIBUTES + ('callbacks', '_canceller', 'result', 'startTime')


  def __init__(self, *args):
    for attr in DEFERRED_ATTRIBUTES:
      setattr(self, attr, getattr(defer.Deferred, attr))
    self.result = getattr(defer, '_NO_RESULT', None)
    self.startTime = time.time()
    defer.Deferred.__init__(self, *args)



def describeDeferred(d):
  """Provide a textual description of a Deferred instance."""
  if isinstance(d, defer.Deferred):
    if hasattr(d, 'describeDeferred'):
      result = d.describeDeferred()
    else:
      result = 'Deferred(%x)' % id(d)
    if d.called:
      result = '*' + result
    if isinstance(d, LowMemoryDeferred):
      result = '[%0.1fs] %s' % (time.time() - d.startTime, result)
    return result
  else:
    return repr(d)
