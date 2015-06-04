Admin modifies personal preferences thru 'Users and groups'
---------------------------------------------------------------------

Set up
======

    >>> from plone.app.testing import TEST_USER_NAME
    >>> from plone.testing.z2 import Browser

    >>> app = layer['app']
    >>> portal = layer['portal']
    >>> membership = portal.portal_membership

    >>> browser = Browser(app)
    >>> browser.handleErrors = False

    >>> empty_marker = '--NOVALUE--'
    >>> def isEmptyMarker(v):
    ...     if len(v) != 1: return False
    ...     return v[0] == empty_marker

An admin can modify user preferences thru the @@user-preferences form in
Users and Groups config page.


So let's login as Plone admin:
    >>> browser.open('http://nohost/plone/')
    >>> browser.getLink('Log in').click()
    >>> browser.getControl('Login Name').value = 'admin'
    >>> browser.getControl('Password').value = 'secret'
    >>> browser.getControl('Log in').click()

Let's see if we can navigate to the user information form in Users and groups
    >>> browser.getLink('Site Setup').click()
    >>> browser.getLink('Users and Groups').click()
    >>> browser.getLink(TEST_USER_NAME).click()
    >>> browser.getLink('Personal Preferences').click()
    >>> browser.url
    'http://nohost/plone/@@user-preferences?userid=test_user_1_'

We have these controls in the form:

    >>> isEmptyMarker(browser.getControl('Wysiwyg editor').value)
    True
    >>> isEmptyMarker(browser.getControl('Language', index=0).value)
    True

The form should be using CSRF protection:

    >>> browser.getControl(name='_authenticator', index=0)
    <Control name='_authenticator' type='hidden'>


Modifying values
----------------

    >>> browser.getControl('Wysiwyg editor').value = ['TinyMCE']
    >>> browser.getControl('Language', index=0).value = ['en']
    >>> browser.getControl('Save').click()
    >>> 'Changes saved' in browser.contents
    True

Verify that the settings have actually been
changed:

    >>> member = membership.getMemberById('test_user_1_')
    >>> marker = object()
    >>> member.getProperty('wysiwyg_editor', marker)
    'TinyMCE'
    >>> member.getProperty('language', marker)
    'en'

And that the form still has the according values:

    >>> browser.open("http://nohost/plone/@@user-preferences?userid=test_user_1_")
    >>> isEmptyMarker(browser.getControl('Wysiwyg editor').value)
    False
    >>> browser.getControl('Wysiwyg editor').value
    ['TinyMCE']
    >>> browser.getControl('Language', index=0).value
    ['en']


Clearing values
---------------

Check that empty or False values do get stored.

    >>> browser.getControl('Wysiwyg editor').value = [empty_marker]
    >>> browser.getControl('Language', index=0).value = [empty_marker]
    >>> browser.getControl('Save').click()
    >>> 'Changes saved' in browser.contents
    True

Verify that the settings have actually been
changed:

    >>> member = membership.getMemberById('test_user_1_')
    >>> not member.getProperty('wysiwyg_editor', marker)
    True
    >>> not member.getProperty('language', marker)
    True

And that the form still has the according values:

    >>> browser.open("http://nohost/plone/@@user-preferences?userid=test_user_1_")
    >>> isEmptyMarker(browser.getControl('Wysiwyg editor').value)
    True
    >>> isEmptyMarker(browser.getControl('Language', index=0).value)
    True

Finally let's see if Cancel button still leaves us on selected user Preferences
form::

    >>> browser.getControl('Cancel').click()
    >>> 'Changes canceled.' in browser.contents
    True
    >>> '?userid=test_user_1_' in browser.url
    True
