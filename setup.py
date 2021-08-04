# -*- coding: utf-8 -*-
from setuptools import find_packages
from setuptools import setup

version = '3.0.0a2'

long_description = u'{0}\n\n{1}'.format(
    open('README.rst').read(),
    open('CHANGES.rst').read()
)

extras_require = {
    'test': [
        'Products.MailHost',
        'plone.app.testing',
        'plone.keyring',
    ]
}

setup(
    name='plone.app.users',
    version=version,
    description='A package for all things users and groups related (specific '
                'to plone)',
    long_description=long_description,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 6.0",
        "Framework :: Plone :: Core",
        "Framework :: Zope :: 5",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    keywords='Zope CMF Plone Users Groups',
    author='Plone Foundation',
    author_email='plone-developers@lists.sourceforge.net',
    url='https://pypi.org/project/plone.app.users',
    license='GPL version 2',
    packages=find_packages(),
    namespace_packages=['plone', 'plone.app'],
    include_package_data=True,
    zip_safe=False,
    extras_require=extras_require,
    install_requires=[
        'AccessControl',
        'Acquisition',
        'Products.CMFCore',
        'Products.CMFPlone >= 5.1a2',
        'Products.PlonePAS >= 5.0.1',
        'Products.statusmessages',
        'Zope2 >= 2.12.3',
        'plone.app.layout',
        'plone.autoform >= 1.2',
        'plone.formwidget.namedfile >= 1.0.3',
        'plone.namedfile',
        'plone.protect',
        'plone.schema',
        'plone.uuid',
        'setuptools',
        'six',
        'z3c.form',
        'zope.component',
        'zope.event',
        'zope.interface',
        'zope.schema',
    ],
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
)
