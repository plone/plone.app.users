Testing the password form
=========================

This is about the 'change_password' form. This test will try to login as a Plone
user, change the password, logout and login with the new password.

Set up
======

    >>> from plone.app.testing import TEST_USER_NAME
    >>> from plone.app.testing import TEST_USER_PASSWORD
    >>> from plone.testing.z2 import Browser

    >>> app = layer['app']
    >>> portal = layer['portal']

    >>> view_name = '@@change-password'

    >>> browser = Browser(app)
    >>> browser.handleErrors = False

The view
========

Viewing this form should not be possible for anonymous users:

    >>> browser.open('http://nohost/plone/' + view_name)
    Traceback (most recent call last):
    ...
    Unauthorized: ...You are not authorized to access this resource...

So let's login as Plone user:
    >>> browser.open('http://nohost/plone/')
    >>> browser.getLink('Log in').click()
    >>> browser.getControl('Login Name').value = TEST_USER_NAME
    >>> browser.getControl('Password').value = TEST_USER_PASSWORD
    >>> browser.getControl('Log in').click()

Now we should be able to access the change password form:

    >>> browser.open('http://nohost/plone/' + view_name)
    >>> 'Login Name' in browser.contents
    False
    >>> browser.url.endswith(view_name)
    True

Let's try to change the password with a new one containing non-ascii chars:

    >>> browser.getControl(name='_authenticator', index=0)
    <Control name='_authenticator' type='hidden'>
    >>> browser.getControl('Current password').value = 'secret'
    >>> browser.getControl('New password').value = 'super-secrét'
    >>> browser.getControl('Confirm password').value = 'super-secrét'
    >>> browser.getControl('Change Password').click()
    >>> 'Password changed' in browser.contents
    True

Let's try to change the password with the current one containing non-ascii chars:

    >>> browser.getControl(name='_authenticator', index=0)
    <Control name='_authenticator' type='hidden'>
    >>> browser.getControl('Current password').value = 'super-secrét'
    >>> browser.getControl('New password').value = 'super-sécrét'
    >>> browser.getControl('Confirm password').value = 'super-sécrét'
    >>> browser.getControl('Change Password').click()
    >>> 'Password changed' in browser.contents
    True

Okay the password has been changed, let's logout and login again with the new password.

    >>> browser.open('http://nohost/plone/logout')
    >>> browser.open('http://nohost/plone/')
    >>> browser.getLink('Log in').click()
    >>> browser.getControl('Login Name').value = TEST_USER_NAME
    >>> browser.getControl('Password').value = 'super-sécrét'
    >>> browser.getControl('Log in').click()

If we are logged in the change password form is available

    >>> browser.open('http://nohost/plone/' + view_name)
    >>> 'Please log in' in browser.contents
    False


Password Validation Plugin
--------------------------

Now let's test using a PAS Password validation plugin. Add a test plugin.

    >>> from plone.app.users.tests.base import addParrotPasswordPolicy
    >>> addParrotPasswordPolicy(portal)

    >>> browser.open('http://nohost/plone/' + view_name)

Check that we are given instructions on what is a valid password

   >>> print browser.contents
    <...
    ...Enter your new password. Must not be dead...


Let's try to change the password with an invalid password:

    >>> browser.getControl('Current password').value = 'super-sécrét'
    >>> browser.getControl('New password').value = 'dead parrot'
    >>> browser.getControl('Confirm password').value = 'dead parrot'
    >>> browser.getControl('Change Password').click()
    >>> print browser.contents
    <...
    ...Must not be dead...

Now try a valid password

    >>> browser.getControl('Current password').value = 'super-sécrét'
    >>> browser.getControl('New password').value = 'fish'
    >>> browser.getControl('Confirm password').value = 'fish'
    >>> browser.getControl('Change Password').click()
    >>> print browser.contents
    <...
    ...Password changed...

Form Validation
---------------

Firstly try to post form without filling in any fields:

    >>> browser.open('http://nohost/plone/' + view_name)
    >>> browser.getControl('Change Password').click()
    >>> 'Required input is missing.' in browser.contents
    True

Let's try to enter not valid current password:

    >>> browser.getControl('Current password').value = 'invalid-password'
    >>> browser.getControl('Change Password').click()
    >>> 'Incorrect value for current password' in browser.contents
    True

Then post form with new password that is not equal to confirmed password:

    >>> browser.getControl('New password').value = 'new-password'
    >>> browser.getControl('Confirm password').value = 'new-password-1'
    >>> browser.getControl('Change Password').click()
    >>> 'Your password and confirmation did not match. Please try again.' in browser.contents
    True
