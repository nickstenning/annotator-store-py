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
    install_requires = [ 'SQLObject >= 0.7' ],
    scripts = [],

    # metadata for upload to PyPI
    author = 'Rufus Pollock (Open Knowledge Foundation)',
    author_email = 'rufus@rufuspollock.org',
    description = \
"Web-based inline annotation of a web resource.",
    long_description = \
"""
""",
    license = 'MIT',
    keywords = 'annotation web javascript',
    url = 'http://p.knowledgeforge.net/shakespeare/svn/annotater/', 
    download_url = 'http://p.knowledgeforge.net/shakespeare/svn/annotater/trunk',
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'],
)
