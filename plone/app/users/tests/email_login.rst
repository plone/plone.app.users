===================================
Testing email address as login name
===================================

Set up
======

    >>> from plone.app.testing import SITE_OWNER_NAME
    >>> from plone.app.testing import SITE_OWNER_PASSWORD
    >>> from plone.app.testing import TEST_USER_PASSWORD
    >>> from plone.testing.zope import Browser

    >>> app = layer['app']
    >>> portal = layer['portal']

Browsers
--------

    >>> browser = Browser(app)
    >>> browser.handleErrors = False

Configure security
------------------

    >>> browser.open('http://nohost/plone/login_form')
    >>> browser.getControl(name='__ac_name').value = SITE_OWNER_NAME
    >>> browser.getControl(name='__ac_password').value = SITE_OWNER_PASSWORD
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
    >>> browser.getControl('Email').value = 'bob-jones+test@example.com'
    >>> browser.getControl('Password').value = TEST_USER_PASSWORD
    >>> browser.getControl('Confirm password').value = TEST_USER_PASSWORD
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
    >>> browser.getControl(name='__ac_name').value = SITE_OWNER_NAME
    >>> browser.getControl(name='__ac_password').value = SITE_OWNER_PASSWORD
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
    >>> browser.getControl('Email').value = 'bob-jones+test2@example.com'
    >>> browser.getControl('Password').value = TEST_USER_PASSWORD
    >>> browser.getControl('Confirm password').value = TEST_USER_PASSWORD
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

Saving this form without changes should work, without complaint that this login name is already taken.

    >>> browser.getControl('Save').click()
    >>> browser.contents
    '...Changes saved...'

Pick a different email address.

    >>> browser.getControl('Email').value = "different@example.com"
    >>> browser.getControl('Save').click()
    >>> browser.contents
    '...Changes saved...'

Pick a valid email address with a format that may cause problems.
This needs plone.schema 2.0.2, with a better email validation.
This also needs a Products.CMFPlone release where the RegistrationTool has the principal_id_or_login_name_exists method.
This is expected in 6.0.15, 6.1.1, and 6.2.0a1.
TODO: enable this test after we have those releases.

    .. >>> browser.getControl('Email').value = "o'hara@example.com"
    .. >>> browser.getControl('Save').click()
    .. >>> browser.contents
    .. '...Changes saved...'
