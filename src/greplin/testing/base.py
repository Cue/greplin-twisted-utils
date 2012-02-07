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

"""Utilities for testing."""

from twisted.internet import defer
from twisted.trial import unittest



class BaseDeferredTest(unittest.TestCase):
  """Base for deferred tests."""


  def _run(self, *args, **kw): # OK to be non-specific with args here.  # pylint: disable = W0221
    """For some reason, the base class doesn't like our inline.callbacks objects as return values.  Wrap it."""
    d = defer.Deferred()
    real = unittest.TestCase._run(self, *args, **kw)
    real.chainDeferred(d)
    return d
