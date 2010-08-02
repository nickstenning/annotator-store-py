Reference implementation backend for `Annotator` web annotation system.

Defines the reference RESTFul API and uses RDBMS storage. Python-based using
sqlalchemy and webob.

.. _Annotator: http://github.com/nickstenning/annotator

Getting Started
===============

Get the annotator code and install it (using pip)::

    # check out the git repo
    git clone git://github.com/nickstenning/annotator-store-py.git
    cd annotator
    pip -E ../pyenv install -e .

NB: All dependencies should be installed automatically. However json support is
requried. In python >= 2.6 this is part of the standard library (json) but if
you have python <= 2.5 install you should install simplejson instead.

You will also need sqlite and python db connector for it.

Try out the demo (requires PasteScript)::

    paster serve store.ini

Visit the url::

    http://localhost:5000/annotations/

Response should be the empty list [] as no annotations are in the store


RESTFul Interface
=================

The RESTful interface is provided by the WSGI application in annotator/store.py.

It can be mounted anywhere you like and provides a RESTful resource 'annotations'.

For example if you have mounted it at '/store' you would have::

    GET    /store/annotations      # list
    POST   /store/annotations      # create
    GET    /store/annotations/{id} # show
    PUT    /store/annotations/{id} # update
    DELETE /store/annotations/{id} # delete

Attributes for these methods (in particular annotation values) may be provided
either as individual query parameters or as as json payload (encoded in
standard way as argument to a parameter named json). Returned data will be
JSON encoded. If a "callback" query parameter is supplied, any response will be JSONP encoded using the value of "callback" as the name of the callback function.

Notes:

  * A create request returns a Location header redirecting to the created
    annotation.

Searching
---------

Search API is located at: {mount_point}/annotations/search

Results are returned in JSON format::

    {
        'total': number of results,
        'results': results list
    }

You can search by any annotation attribute (but not "extras"). For example to
search for annotation with a particular 'uri' field you'd visit::

    /annotations/search?uri=http://example.com

In addition to search parameters there are three additional control parameters:

  * limit=val: limit the number of results returned to val (defaults to 100 if
    not set). To have all results returned set to -1.
  * offset=val: return results from val onwards
  * all_fields=1: if absent only return ids of annotations, if present (true)
    return all fields of the annotation


Specification of Annotations
============================

Annotations have the following attributes:

  * id: usually a uuid but up to implementing backend
  * uri: document identifier
  * user: an identifier for the user who created the annotation. To avoid
    cross-application collision it is recommended that you either:
    * Generate uuids for your users stored as: urn:uuid:{uuid} (or just {uuid})
    * (or) Prefix your usernames with a unique (e.g. uuid) string (e.g.
      {uuid-identifying-application}::{your-username}
  * note: text of annotation
  * range(s): list of range objects. Each range object has:
    * [optional] format: range format (defines syntax/semantics of start end)
    * start: xpath, offset (for default html format)
    * end: xpath, offset (for default html format)
  * [optional] quote (the quoted text -- or snippet thereof)
  * [optional] created (datetime of creation)
  * "extras": you add arbitrary addtional key/value pairs to annotations



Changelog
=========


HEAD
----

  * New attributes on Annotation: user, tags
  * Support for jsonp and returning id on annotation create
  * Allow arbitrary attributes on annotation via "extras" field
  * Searching annotations (essential for multi-document annotation!)
  * Improved documentation
  * Support locating annotation RESTFul url within store (e.g.
    {store}/annotations instead {store}/annotation)


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

Copyright (c) 2006-2010 the Open Knowledge Foundation.

Licensed under the MIT license:

  <http://www.opensource.org/licenses/mit-license.php>

Versions earlier than 0.3 used js code derived from Geof Glass' code which are
therefore (c) Geoff Glass and collaborators and are licensed under the GPL v2.

