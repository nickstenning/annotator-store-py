from setuptools import setup, find_packages

from annotater import __version__

setup(
    name = 'annotater',
    version = __version__,
    packages = find_packages(),
    # WARNING: package_data is broken for sdist
    # see
    # http://mail.python.org/pipermail/distutils-sig/2007-February/007216.html
    # package_data = {
    #    'annotater.marginalia' : ['*.js', '*.css', 'lang/*' ],
    #    },
    install_requires = [
        'SQLAlchemy>=0.5',
        'FormAlchemy>=1.0',
        'Paste >= 1.0',
        'PasteDeploy',
        'nose',
        'routes>=1.7',
        ],
    scripts = [],

    # metadata for upload to PyPI
    author = 'Rufus Pollock (Open Knowledge Foundation)',
    author_email = 'rufus@rufuspollock.org',
    description = \
"Inline javascript-based web annotation.",
    long_description = \
"""
Inline javascript-based web annotation library incorporating Marginalia
(http://www.geof.net/code/annotation). Package includeds a database-backed
annotation store with RESTFul (WSGI-powered) web-interface, abstraction layer
around marginalia to make it easy to incorporate it into your web application
and all the marginalia media files (with improvements).
""",
    license = 'MIT',
    keywords = 'annotation web javascript',
    url = 'http://p.knowledgeforge.net/shakespeare/svn/annotater/', 
    download_url = 'http://p.knowledgeforge.net/shakespeare/svn/annotater/trunk',
    zip_safe=False,
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'],
)
