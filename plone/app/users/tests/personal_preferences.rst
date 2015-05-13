Testing the personal preferences form
=====================================

This is about the 'personal-preferences' view.

Set up
======

    >>> from plone.app.testing import TEST_USER_NAME
    >>> from plone.app.testing import TEST_USER_PASSWORD
    >>> from plone.testing.z2 import Browser

    >>> app = layer['app']
    >>> portal = layer['portal']
    >>> membership = portal.portal_membership

    >>> view_name = '@@personal-preferences'

    >>> browser = Browser(app)
    >>> browser.handleErrors = False

    >>> empty_marker = '--NOVALUE--'
    >>> def isEmptyMarker(v):
    ...     if len(v) != 1: return False
    ...     return v[0] == empty_marker

Viewing the personal preferences
--------------------------------

Viewing user data shouldn't be possible for anonymous users:

    >>> browser.open("http://nohost/plone/" + view_name)
    Traceback (most recent call last):
    ...
    Unauthorized: ...You are not authorized to access this resource...

So let's login as Plone user:
    >>> browser.open('http://nohost/plone/')
    >>> browser.getLink('Log in').click()
    >>> browser.getControl('Login Name').value = TEST_USER_NAME
    >>> browser.getControl('Password').value = TEST_USER_PASSWORD
    >>> browser.getControl('Log in').click()

Now we should be able to access the user data panel:

    >>> browser.open("http://nohost/plone/" + view_name)
    >>> 'Login Name' in browser.contents
    False
    >>> browser.url.endswith(view_name)
    True

We have two controls, one for the editor and one for the language:

    >>> isEmptyMarker(browser.getControl('Wysiwyg editor').value)
    True
    >>> isEmptyMarker(browser.getControl('Language', index=0).value)
    True

The form should be using CSRF protection:

    >>> browser.getControl(name='_authenticator', index=0)
    <Control name='_authenticator' type='hidden'>

Now we click the cancel button:

    >>> browser.getControl('Cancel').click()
    >>> browser.url.endswith(view_name)
    True

There should be no changes at all:

    >>> 'Changes canceled.' in browser.contents
    True

Modifying values
----------------

    >>> browser.open('http://nohost/plone/' + view_name)
    >>> browser.getControl('Wysiwyg editor').value = ['TinyMCE']
    >>> browser.getControl('Language', index=0).value = ['en']
    >>> browser.getControl('Save').click()
    >>> 'Changes saved' in browser.contents
    True

Verify that the settings have actually been
changed:

    >>> member = membership.getMemberById('test_user_1_')
    >>> marker = object
    >>> member.getProperty('wysiwyg_editor', object)
    'TinyMCE'
    >>> member.getProperty('language', object)
    'en'

And that the form still has the according values:

    >>> isEmptyMarker(browser.getControl('Wysiwyg editor').value)
    False
    >>> browser.getControl('Wysiwyg editor').value
    ['TinyMCE']
    >>> browser.getControl('Language', index=0).value
    ['en']


Clearing values
---------------

Making an input empty should result in a stored empty string.

    >>> browser.open('http://nohost/plone/' + view_name)
    >>> browser.getControl('Wysiwyg editor').value = [empty_marker]
    >>> browser.getControl('Language', index=0).value = [empty_marker]
    >>> browser.getControl('Save').click()
    >>> 'Changes saved' in browser.contents
    True

Verify that the settings have actually been
changed:

    >>> member = membership.getMemberById('test_user_1_')
    >>> marker = object
    >>> not member.getProperty('wysiwyg_editor', object)
    True
    >>> not member.getProperty('language', object)
    True

And that the form still has the according values:

    >>> isEmptyMarker(browser.getControl('Wysiwyg editor').value)
    True
    >>> isEmptyMarker(browser.getControl('Language', index=0).value)
    True
