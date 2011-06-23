# Copyright 2011 Greplin, Inc.  All Rights Reserved.

"""Defines Twisted Web resources for "thread" reporting."""


from greplin.defer import thread

import cgi
import urllib

from twisted.web import resource



class ThreadsResource(resource.Resource):
  """Twisted web resource for a status page."""

  isLeaf = True


  def __init__(self):
    resource.Resource.__init__(self)


  def render_GET(self, request):
    """Renders a GET request, by showing this nodes stats and children."""
    if 'name' in request.args:
      name = request.args['name']
      asyncFrame = thread.AsyncFrame.byName[name[0]]
    else:
      asyncFrame = thread.ROOT_FRAME

    while len(asyncFrame.children) == 1:
      asyncFrame = iter(asyncFrame.children).next()

    ancestors = []
    ancestor = asyncFrame.parent
    while ancestor:
      ancestors.append(ancestor)
      ancestor = ancestor.parent

    for ancestor in reversed(ancestors):
      request.write('<a href="?name=%s">%s</a> ' % (cgi.escape(urllib.quote(ancestor.getName())), ancestor.getName()))

    request.write('<h1>%s</h1>' % asyncFrame.getName())
    request.write('<pre>%s</pre>' % cgi.escape(asyncFrame.stacktrace()))

    for child in asyncFrame.children:
      request.write('<p><a href="?name=%s">%s</a></p>' % (
          cgi.escape(urllib.quote(child.getName())), child.getName()))

    return ''
