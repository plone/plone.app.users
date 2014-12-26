=============================
Test duplicate mail addresses
=============================

When email address is used as login name, duplicates are not allowed.

Use email addresses as login name.

Set up
======

    >>> from plone.app.testing import SITE_OWNER_NAME
    >>> from plone.app.testing import SITE_OWNER_PASSWORD
    >>> from plone.testing.z2 import Browser

    >>> app = layer['app']
    >>> portal = layer['portal']

    >>> user1_name = 'User one'
    >>> user1_email = 'userone@example.com'
    >>> user1_password = 'secret'

    >>> user2_name = 'User two'
    >>> user2_email = 'usertwo@example.com'
    >>> user2_password = 'secret'

    >>> browser = Browser(app)
    >>> from plone.app.users.tests.base import get_security_settings
    >>> security_settings = get_security_settings()
    >>> security_settings.use_email_as_login = True
    >>> from transaction import commit
    >>> commit()

Configure security
------------------

    >>> browser.open('http://nohost/plone/login_form')
    >>> browser.getControl('Login Name').value = SITE_OWNER_NAME
    >>> browser.getControl('Password').value = SITE_OWNER_PASSWORD
    >>> browser.getControl('Log in').click()

    >>> browser.open('http://nohost/plone/@@security-controlpanel')
    >>> browser.getControl('Use email address as login name ').selected = True
    >>> browser.getControl('Save').click()
    >>> 'Changes saved' in browser.contents
    True

Create two users
----------------

First one:

    >>> browser.open('http://nohost/plone/@@usergroup-userprefs')
    >>> browser.getLink('Add New User').click()
    >>> '@@new-user' in browser.url
    True

Fill out the form.

    >>> browser.getControl('Full Name').value = user1_name
    >>> browser.getControl('E-mail').value = user1_email
    >>> browser.getControl('Password').value = user1_password
    >>> browser.getControl('Confirm password').value = user1_password
    >>> browser.getControl('Register').click()
    >>> '@@usergroup-userprefs' in browser.url
    True
    >>> browser.contents
    '...User added...'

The second:

    >>> browser.open('http://nohost/plone/@@usergroup-userprefs')
    >>> browser.getLink('Add New User').click()
    >>> '@@new-user' in browser.url
    True

Fill out the form.

    >>> browser.getControl('Full Name').value = user2_name
    >>> browser.getControl('E-mail').value = user2_email
    >>> browser.getControl('Password').value = user2_password
    >>> browser.getControl('Confirm password').value = user2_password
    >>> browser.getControl('Register').click()
    >>> '@@usergroup-userprefs' in browser.url
    True
    >>> browser.contents
    '...User added...'

Logout:

    >>> browser.getLink(url='http://nohost/plone/logout').click()

Login
=====

Login as user two:

    >>> browser.open('http://nohost/plone/')
    >>> browser.getLink('Log in').click()

    >>> browser.getControl('Login Name').value = user2_email
    >>> browser.getControl('Password').value = user2_password
    >>> browser.getControl('Log in').click()
    >>> 'Login failed' in browser.contents
    False

Should be able to access the user data panel:

    >>> browser.open('http://nohost/plone/@@personal-information')
    >>> 'Login Name' in browser.contents
    False
    >>> browser.url.endswith('@@personal-information')
    True

Change e-mail
=============

Setting the e-mail address to an existing one should give an error message:

    >>> browser.getControl('E-mail').value = user1_email
    >>> browser.getControl('Save').click()
    >>> 'The email address you selected is already in use' in browser.contents
    True
    >>> 'Changes saved' in browser.contents
    False
