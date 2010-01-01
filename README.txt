Introduction
============

Annotator is a inline web annotation system designed for easy integration into
web applications.

It also providers its own web annotation service.


Getting Started
===============

Get the annotator code and install it (using pip)::

    # check out the mercurial repo
    hg clone https://knowledgeforge.net/okfn/annotator
    cd annotator
    pip -E ../pyenv install -e .

NB: All dependencies should be installed automatically. However json support is
requried. In python >= 2.6 this is part of the standard library (json) but if
you have python <= 2.5 install you should install simplejson instead.

You will also need sqlite and python db connector for it.

Try out the demo (requires PasteScript):

    paster serve demo.ini
    
Visit http://localhost:5000/


Technical Information
=====================

Annotator is derived into 2 parts:

1. A generic backend for storing annotations consisting of a RESTful interface
plus storage (DB based).

2. Frontend javascript that handles the user interface and can interact with
the backend. This is currently provided as a separate package (jsannotate -
http://github.com/nickstenning/annotator) though some integration in is done in
this library.

The two components are decoupled so each is usable on its own.


Specification of the Annotation Store
-------------------------------------

The RESTful interface is provided by the WSGI application in annotator/store.py.

It can be mounted anywhere you like and provides a RESTful resource 'annotation'.

For example if you have mounted it at '/store' you would have:

    GET /store/annotation # list annotation
    POST /store/annotation # create
    GET /store/annotation/id # get annotation
    POST /store/annotation/id # update annotation
    DELETE /store/annotation/id # delete annotation

Attributes for these methods (in particular annotation values) may be provided
either as individual query parameters or as as json payload (encoded in
standard way as argument to a parameter named json). Returned data will be json
encoded.

Annotations have the following attributes:

  * uri: document identifier
  * note: text of annotation
  * range(s): list of range objects. Each range object has:
    * format: range format (defines syntax/semantics of start end)
    * start: xpath, offset (for default html format)
    * end: xpath, offset (for default html format)
  * [optional] quote (the quoted text -- or snippet thereof)
  * [optional] created (datetime of creation)


Changelog
=========

v0.3 2009-10-18
---------------

Major release:

  * RESTful interface is JSON-based by default
  * Much improved demo with WSGI middleware
  * Switch from existing marginalia js library to new jsannotate library
  * Rename from annotater to annotator
  * Make model code easily reusable inside another project
  * Simplify and refactor code throughout

v0.2 2009-07-26
---------------

  * Significant polishing 
  * Convert backend store to use SQLAlchemy
  * Load RESTful interface at an arbitrary url
  * Last version to be based on marginalia

v0.1 2007-04-01
---------------

  * Fully functioning web annotation using marginalia
  * SQLObject based backend store
  * WSGI RESTful interface to store
  * WSGI app for mounting marginalia media (js, css etc)
  * Demo app in demo/

Copyright and License
=====================

Copyright (c) 2006-2009 the Open Knowledge Foundation.

Licensed under the MIT license:

  <http://www.opensource.org/licenses/mit-license.php>

Versions earlier than 0.3 used js code derived from Geof Glass' code which are
therefore (c) Geoff Glass and collaborators and are licensed under the GPL v2.

