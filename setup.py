from setuptools import setup, find_packages

from annotator import __version__, __license__, __author__

setup(
    name = 'annotator',
    version = __version__,
    packages = find_packages(),
    install_requires = [
        'SQLAlchemy>=0.4.8',
        # 'FormAlchemy>=1.0',
        'Paste >= 1.0',
        'PasteDeploy',
        'routes>=1.7',
        'wsgifilter>=0.2'
        # for tests
        # 'nose',
        ],
    scripts = [],

    # metadata for upload to PyPI
    author = __author__,
    author_email = 'rufus@rufuspollock.org',
    description = \
'Inline web annotation application and middleware using javascript and WSGI',
    long_description = \
"""
Inline javascript-based web annotation library incorporating Marginalia
(http://www.geof.net/code/annotation). Package includeds a database-backed
annotation store with RESTFul (WSGI-powered) web-interface, abstraction layer
around marginalia to make it easy to incorporate it into your web application
and all the marginalia media files (with improvements).
""",
    license = __license__,
    keywords = 'annotation web javascript',
    url = 'http://knowledgeforge.net/okfn/annotator/', 
    download_url = 'http://knowledgeforge.net/okfn/annotator/',
    zip_safe=False,
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'],
    entry_points='''
    [paste.app_factory]
    demo = annotator.demo:make_app
    ''',
)
