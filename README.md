greplin-twisted-utils
=====================

Greplin Twisted Utilities
----------------------------

Useful utilities for Twisted development.


### Status:

This is a very early stage project.  It works for our needs.  We haven't verified it works beyond that.  Issue reports
and patches are very much appreciated!


### Pre-requisites:

[Twisted](http://twistedmatrix.com/trac/)


### Installation

    git clone https://github.com/Greplin/greplin-twisted-utils.git

    cd greplin-twisted-utils

    python setup.py install


### Components

#### greplin.defer

Utilities for dealing with twisted.internet.Deferred objects.

  * Context management - allows setting context variables that persist across asynchronous events.  This is highly
    experimental!

  * Deferred events - pub/sub model for events.

  * Lazy map - map that lazily computes its values, possibly requiring asynchronous computation.

  * Deferred queues

  * Retry logic for deferred requests that may fail transiently

  * Time - simple utilities for deferred objects that fire after a specified time

  * Deferred wrapper - allows for success / failure to be handled at the very end of the callback chain.


#### greplin.net

  * DNS cache - avoid repeatedly resolving the same DNS names


#### greplin.testing

  * Mock implementation of greplin.defer.time


### Authors:

[Greplin, Inc.](http://www.greplin.com)
