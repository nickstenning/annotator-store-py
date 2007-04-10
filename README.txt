## Introduction

Annotater is a inline web annotation system for python built on Geof Glass'
[marginalia].

[marginalia]: http://www.geof.net/code/annotation


## Copyright and License

Copyright (c) 2006-2007 the Open Knowledge Foundation.

All parts deriving directly from Geof Glass' code are (c) Geoff Glass and
collaborators and are licensed under the GPL v2.

All other code licensed under the MIT license:

  <http://www.opensource.org/licenses/mit-license.php>


## Getting Started

You can start the demo web application:

    $ python demo/demo.py

You'll then find an annotable web page presented at <http://localhost:8080/>

Try it out.


## Technical Information

Annotater is derived into 2 parts:

1. A annotation storage backend providing a web and RESTful interface

2. A web application that uses the marginalia javascript to provide javascript
based web annoation.


### Specification of the Annotation Store

The RESTful interface is defined by python routes commmand:

map.resource('annotation')

That is, the store is mounted at url /annotation/ and supports a restful
interface as defined in the [routes docs].

[routes docs]: http://routes.groovie.org/manual.html

There are a few additions to ensure compatibility with the marginalia
javascript front-end as well as to support a better 'human' web interface.
These are most easily seen by looking at the routes commands at the top of
annotater.py.

An annotation: see the definition Annotation in model.py (the domain model
file).

