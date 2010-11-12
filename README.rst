Reference implementation backend for `Annotator` web annotation system.

Defines the reference RESTFul API and connects to a database backend to
persist annotations created by the frontend, Annotator_.

.. _Annotator: http://github.com/nickstenning/annotator

There is also an experimental CouchDB implementation. See the `couchdb` branch
of the repository.

Getting Started
===============

The following instructions assume you have a working installation of `python`
(2.6 or higher) and `sqlite` (any recent version). You will also need `pip` and
`virtualenv`, which can be installed quickly with one command::

    easy_install virtualenv

Now, you should be ok to set up annotator-store-py::

    git clone git://github.com/nickstenning/annotator-store-py.git
    cd annotator-store-py
    pip install -E pyenv -r requirements.txt -e .

If that worked ok, you should see something like::

    [...]
    Successfully installed annotator HTTPEncode httplib2 Paste PasteDeploy PasteScript routes SQLAlchemy webob wsgifilter
    Cleaning up...

You should now be able to run the demo server::

    source pyenv/bin/activate
    paster serve store.ini

You might a deprecation warning from SQLAlchemy. We're working on removing this but
in the mean time you can safely ignore it. You can take a peek at the (little)
that the backend is now doing::

    curl -i http://localhost:5000/annotations

You'll see that the store responds with "[]": there aren't any annotations in
the store at the moment. That's not surprising: you haven't created any. For that,
you'll need to go get Annotator_ and hook it up to the backend.

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

v0.4 2010-11-10
---------------

**Beta release**: this annotator store has now been successfully used in
production deployments.

  * New attributes on Annotation: user, tags
  * Support for jsonp and returning id on annotation create
  * Allow arbitrary attributes on annotations
  * Searching annotations (essential for multi-document annotation!)
  * Improved documentation
  * Support locating annotation RESTFul url within store (e.g.
    {store}/annotations instead {store}/annotation)
  * Preliminary CORS support for cross-domain requests
  * Preliminary CouchDB support

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

