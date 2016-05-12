# -*- coding: utf-8 -*-
from setuptools import find_packages
from setuptools import setup

version = '2.3.6'

long_description = '{0}\n{1}'.format(open('README.rst').read(),
                                     open('CHANGES.rst').read())


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
        'Environment :: Web Environment',
        'Framework :: Plone',
        'Framework :: Plone :: 5.0',
        'Framework :: Zope2',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
    ],
    keywords='Zope CMF Plone Users Groups',
    author='Plone Foundation',
    author_email='plone-developers@lists.sourceforge.net',
    url='https://pypi.python.org/pypi/plone.app.users',
    license='GPL version 2',
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=['plone', 'plone.app'],
    include_package_data=True,
    zip_safe=False,
    extras_require=extras_require,
    install_requires=[
        'AccessControl',
        'Acquisition',
        'Products.CMFCore',
        'Products.CMFPlone',
        'Products.PlonePAS',
        'Products.statusmessages',
        'ZODB3',
        'Zope2 >= 2.12.3',
        'plone.app.controlpanel >=2.1b1',
        'plone.app.layout',
        'plone.autoform >= 1.2',
        'plone.formwidget.namedfile >= 1.0.3',
        'plone.namedfile',
        'plone.protect',
        'plone.schema',
        'plone.uuid',
        'setuptools',
        'z3c.form',
        'zope.component',
        'zope.event',
        'zope.interface',
        'zope.schema',
        'zope.site',
    ],
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
)
