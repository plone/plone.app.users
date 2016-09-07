from setuptools import setup, find_packages

version = '1.2.5'

setup(name='plone.app.users',
      version=version,
      description="A package for all things users and groups related (specific to plone)",
      long_description=open("README.rst").read() + "\n" +
                       open("CHANGES.rst").read(),
      classifiers=[
          "Environment :: Web Environment",
          "Framework :: Plone",
          "Framework :: Plone :: 4.3",
          "Framework :: Zope2",
          "License :: OSI Approved :: GNU General Public License (GPL)",
          "Operating System :: OS Independent",
          "Programming Language :: Python",
          "Programming Language :: Python :: 2.6",
          "Programming Language :: Python :: 2.7",
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
      extras_require=dict(
        test=[
            'zope.testing',
            'Products.PloneTestCase',
            'Pillow',
        ],
      ),
      install_requires=[
          'setuptools',
          'five.formlib',
          'plone.protect',
          'plone.app.controlpanel >=2.1b1',
          'plone.app.layout',
          'zope.component',
          'zope.formlib',
          'zope.i18nmessageid',
          'zope.interface',
          'zope.schema',
          'zope.site',
          'Products.CMFPlone',
          'Products.CMFCore',
          'Products.PlonePAS',
          'Products.statusmessages',
          'Zope2 >= 2.12.3',
          'ZODB3',
      ],
      entry_points="""
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
