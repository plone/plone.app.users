from setuptools import setup, find_packages

version = '2.0.3'

setup(
    name='plone.app.users',
    version=version,
    description="A package for all things users and groups related (specific "
                "to plone)",
    long_description=open("README.rst").read() + "\n" +
                     open("CHANGES.rst").read(),
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Zope2",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
    keywords='Zope CMF Plone Users Groups',
    author='Plone Foundation',
    author_email='plone-developers@lists.sourceforge.net',
    url='http://pypi.python.org/pypi/plone.app.users',
    license='GPL version 2',
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=['plone', 'plone.app'],
    include_package_data=True,
    zip_safe=False,
    extras_require=dict(
        test=[
            'Products.MailHost',
            'Products.PloneTestCase',
            'plone.keyring',
        ],
    ),
    install_requires=[
        'setuptools',
        'AccessControl',
        'Acquisition',
        'Products.CMFCore',
        'Products.CMFDefault',
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
        'plone.uuid',
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
