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

"""Twisted database connection pools."""

from twisted.enterprise import adbapi
from twisted.python import log

import MySQLdb



class ReconnectingConnectionPool(adbapi.ConnectionPool):
  """Reconnecting adbapi connection pool for MySQL."""

  def _runInteraction(self, interaction, *args, **kw):
    """Overrides the superclass interaction method to reconnect and retry when the connection is lost."""
    try:
      return adbapi.ConnectionPool._runInteraction(self, interaction, *args, **kw)

    # pylint: disable=E1101
    except MySQLdb.OperationalError, e:
      if e[0] not in (2006, 2013):
        raise
      log.msg("ReconnectingConnectionPool: got error %s, retrying operation" % e)
      conn = self.connections.get(self.threadID())
      self.disconnect(conn)
      # Try the interaction again.
      return adbapi.ConnectionPool._runInteraction(self, interaction, *args, **kw)



POOLS = {}


def getSharedDbPool(dbapiName, host, db, user, password, minConnections, maxConnections):
  """Creates a shared DB pool based on the given parameters.

  Each unique set of parameters gets a different pool, so make sure they are consistent!
  """
  assert dbapiName == 'MySQLdb' # TODO: support other databases by catching appropriate errors above

  key = (dbapiName, host, db, user, password, minConnections, maxConnections)

  if key not in POOLS:
    POOLS[key] = ReconnectingConnectionPool(
        dbapiName,
        host=host,
        db=db,
        user=user,
        passwd=password,
        cp_reconnect = True,
        cp_min = minConnections,
        cp_max = maxConnections,
        use_unicode = True,
        init_command='SET NAMES utf8')

  return POOLS[key]
