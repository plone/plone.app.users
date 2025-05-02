from pathlib import Path
from setuptools import find_packages
from setuptools import setup


version = "3.1.2"

long_description = (
    f"{Path('README.rst').read_text()}\n{Path('CHANGES.rst').read_text()}"
)

extras_require = {
    "test": [
        "Products.MailHost",
        "Products.PluggableAuthService",
        "plone.app.contenttypes[test]",
        "plone.app.multilingual",
        "plone.app.robotframework",
        "plone.app.testing",
        "plone.keyring",
        "plone.testing",
    ]
}

setup(
    name="plone.app.users",
    version=version,
    description="A package for all things users and groups related (specific "
    "to plone)",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    # Get more strings from
    # https://pypi.org/classifiers/
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
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="Zope CMF Plone Users Groups",
    author="Plone Foundation",
    author_email="plone-developers@lists.sourceforge.net",
    url="https://pypi.org/project/plone.app.users",
    license="GPL version 2",
    packages=find_packages(),
    namespace_packages=["plone", "plone.app"],
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.8",
    extras_require=extras_require,
    install_requires=[
        "Acquisition",
        "Pillow",
        "Products.GenericSetup",
        "Products.PlonePAS >= 5.0.1",
        "Products.statusmessages",
        "Zope",
        "plone.autoform >= 1.2",
        "plone.app.event",
        "plone.app.vocabularies",
        "plone.base",
        "plone.formwidget.namedfile >= 1.0.3",
        "plone.i18n",
        "plone.memoize",
        "plone.namedfile",
        "plone.protect",
        "plone.registry",
        "plone.schema",
        "plone.schemaeditor",
        "plone.supermodel",
        "plone.uuid",
        "plone.z3cform",
        "setuptools",
        "z3c.form",
        "zope.annotation",
        "zope.cachedescriptors",
        "zope.component",
        "zope.event",
        "zope.interface",
        "zope.schema",
    ],
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
)
