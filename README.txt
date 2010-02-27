Introduction
============

Annotator is a inline web annotation system designed for easy integration into
web applications.


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

Specification of Annotations
----------------------------

Annotations have the following attributes:

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
  * created (datetime of creation)
  * "extras": you add arbitrary addtional key/value pairs to annotations

Annotation Store: RESTFul Interface
-----------------------------------

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

Notes:
  * CREATE: In standard RESTFul fashion, CREATE returns a Location
    header pointing to created annotation. For convenience, it also returns a
    JSON body with a id of newly created object as the single key/value.
    Furthermore, there is also JSONP support via a 'callback' parameter -- if
    there is a callback=function_name in parameters then we return javascript
    of form: `function_name({'id': id})`

Searching
---------

Search API is located at: {mount-point}/search

Results are returned in JSON format::

    {
        'total': total-number-of-results,
        'results': list-of-results-in-json-format
    }

You can search by any annotation attribute (but not "extras"). For example to
search for annotation with a particular doc uri "our-doc-uri" you'd visit::

    .../search?uri=our-doc-uri

In addition to search parameters there are three additional control parameters:

  * limit=val: limit the number of results returned to val (defaults to 100 if
    not set). To have all results returned set to -1.
  * offset=val: return results from val onwards
  * all_fields=1: if absent only return ids of annotations, if present (true)
    return all fields of the annotation


Changelog
=========


HEAD
----

  * New attributes on Annotation: user, tags
  * Support for jsonp and returning id on annotation create
  * Allow arbitrary attributes on annotation via "extras" field
  * Searching annotations (essential for multi-document annotation!)
  * Improved documentation
  * Support locating locating annotation RESTFul url within store (e.g.
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

