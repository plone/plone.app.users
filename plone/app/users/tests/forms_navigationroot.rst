==================================================
Test form links against different navigation roots
==================================================

Links that are present within each of the forms should adhere to
the current navigation root for the site.

Set up
======

    >>> from Products.Five.utilities.marker import mark
    >>> from plone.app.layout.navigation.interfaces import INavigationRoot
    >>> from plone.app.testing import SITE_OWNER_NAME
    >>> from plone.app.testing import SITE_OWNER_PASSWORD
    >>> from plone.testing.z2 import Browser

    >>> app = layer['app']
    >>> portal = layer['portal']

    >>> browser = Browser(app)
    >>> browser.handleErrors = False

Create a folder
---------------

We'll create the test context and have the relevant navigation root marker
interface ready to be applied:

    >>> from plone.app.testing import setRoles
    >>> from plone.app.testing import TEST_USER_ID
    >>> setRoles(portal, TEST_USER_ID, ['Manager'])
    >>> portal.invokeFactory('Folder', id='folder_navroot', title="Navroot")
    'folder_navroot'
    >>> from transaction import commit
    >>> commit()

Let's see if we can navigate to the user information and options forms
in the 'Users and Groups' settings. Each of the 3 forms all use the
same base class so if the fix works on one, it works on them all.

    >>> browser.open('http://nohost/plone/login_form')
    >>> browser.getControl('Login Name').value = SITE_OWNER_NAME
    >>> browser.getControl('Password').value = SITE_OWNER_PASSWORD
    >>> browser.getControl('Log in').click()

    >>> browser.getLink('Navroot').click()

    >>> browser.getLink('Preferences').click()
    >>> browser.url
    'http://nohost/plone/@@personal-preferences'

Check the existance and links for a standard site context (navigation root
is the Plone site itself since the marker interface isn't applied here
yet).

    >>> browser.getLink('Personal Information').url
    'http://nohost/plone/@@personal-information'
    >>> browser.getLink('Personal Preferences').url
    'http://nohost/plone/@@personal-preferences'

Now, let's mark this folder and see what happens.  All links should
now be rooted to the given folder and not the Plone site proper.

    >>> mark(portal.folder_navroot, INavigationRoot)
    >>> commit()

    >>> browser.getLink('Navroot').click()

    >>> browser.getLink('Preferences').click()
    >>> browser.url
    'http://nohost/plone/folder_navroot/@@personal-preferences'

    >>> browser.getLink('Personal Information').url
    'http://nohost/plone/folder_navroot/@@personal-information'
    >>> browser.getLink('Personal Preferences').url
    'http://nohost/plone/folder_navroot/@@personal-preferences'


