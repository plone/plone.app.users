===================================
Testing email address as login name
===================================

Set up
======

    >>> from plone.app.testing import SITE_OWNER_NAME
    >>> from plone.app.testing import SITE_OWNER_PASSWORD
    >>> from plone.testing.z2 import Browser

    >>> app = layer['app']
    >>> portal = layer['portal']

Browsers
--------

    >>> browser = Browser(app)
    >>> browser.handleErrors = False

Configure security
------------------

    >>> browser.open('http://nohost/plone/login_form')
    >>> browser.getControl('Login Name').value = SITE_OWNER_NAME
    >>> browser.getControl('Password').value = SITE_OWNER_PASSWORD
    >>> browser.getControl('Log in').click()

    >>> browser.open('http://nohost/plone/@@security-controlpanel')
    >>> browser.getControl('Enable self-registration').selected = True
    >>> browser.getControl('Let users select their own passwords').selected = True
    >>> browser.getControl('Use email address as login name ').selected = True
    >>> browser.getControl('Save').click()
    >>> 'Changes saved' in browser.contents
    True

    >>> browser.getLink(url='http://nohost/plone/logout').click()
    >>> 'Log in' in browser.contents
    True

Visitors can register
=====================

Logged out user should now see the register link.

    >>> 'Register' in browser.contents
    True

The form should now be visible, without the user name field.

    >>> browser.open('http://nohost/plone/@@register')
    >>> 'User Name' in browser.contents
    False

The form should be using CSRF protection.

    >>> browser.getControl(name='_authenticator')
    <Control name='_authenticator' type='hidden'>

Fill out the form, using an odd email address that should not give problems.

    >>> browser.getControl('Full Name').value = 'Bob Jones'
    >>> browser.getControl('E-mail').value = 'bob-jones+test@example.com'
    >>> browser.getControl('Password').value = 'secret'
    >>> browser.getControl('Confirm password').value = 'secret'
    >>> browser.getControl('Register').click()
    >>> 'Failed to create your account' in browser.contents
    False

    We can login immediately.
    >>> 'Click the button to log in immediately.' in browser.contents
    True
    >>> browser.getControl('Log in').click()
    >>> 'You are now logged in' in browser.contents
    True
    >>> browser.open('http://nohost/plone/@@personal-information')
    >>> 'Bob Jones' in browser.contents
    True
    >>> 'bob-jones+test@example.com' in browser.contents
    True
    >>> browser.getLink(url='http://nohost/plone/logout').click()

    We login as manager. The login form now has a different label for
    the login name.
    >>> browser.open('http://nohost/plone/login_form')
    >>> browser.getControl('E-mail').value = SITE_OWNER_NAME
    >>> browser.getControl('Password').value = SITE_OWNER_PASSWORD
    >>> browser.getControl('Log in').click()

The user id is now bob-jones, based on the full name:

    >>> browser.open('http://nohost/plone/@@user-information?userid=bob-jones')
    >>> 'Bob Jones' in browser.contents
    True

Manager adds a new member
=========================

Great! The user-facing form works. Let's try the manager's version...

    >>> browser.open('http://nohost/plone/@@usergroup-userprefs')
    >>> browser.getLink('Add New User').click()
    >>> '@@new-user' in browser.url
    True

The form should be using CSRF protection.

    >>> browser.getControl(name='_authenticator', index=0)
    <Control name='_authenticator' type='hidden'>

Check that user name is not displayed.

    >>> 'User Name' in browser.contents
    False

Fill out the form.
Use the same full name as before, to test that we get a different user id.

    >>> browser.getControl('Full Name').value = 'Bob Jones'
    >>> browser.getControl('E-mail').value = 'bob-jones+test2@example.com'
    >>> browser.getControl('Password').value = 'secret'
    >>> browser.getControl('Confirm password').value = 'secret'
    >>> browser.getControl('Register').click()
    >>> '@@usergroup-userprefs' in browser.url
    True
    >>> browser.contents
    '...User added...bob-jones-1...'

We can really get the new user.

    >>> browser.getControl('Show all').click()
    >>> browser.getLink(url='bob-jones-1').click()
    >>> '@@user-information?userid=bob-jones-1' in browser.url
    True
