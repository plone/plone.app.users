Testing the password form
=========================

This is about the 'change_password' form. This test will try to login as a Plone
user, change the password, logout and login with the new password.

    >>> view_name = '@@change-password'

Viewing this form should not be possible for anonymous users:

    >>> self.browser.open('http://nohost/plone/' + view_name)
    >>> 'Login Name' in self.browser.contents
    True


So let's login as Plone user:
    >>> self.browser.open('http://nohost/plone/')
    >>> self.browser.getLink('Log in').click()
    >>> self.browser.getControl('Login Name').value = 'test_user_1_'
    >>> self.browser.getControl('Password').value = 'secret'
    >>> self.browser.getControl('Log in').click()

Now we should be able to access the change password form:

    >>> self.browser.open('http://nohost/plone/' + view_name)
    >>> 'Login Name' in self.browser.contents
    False
    >>> self.browser.url.endswith(view_name)
    True

Let's try to change the password:

    >>> self.browser.getControl(name='_authenticator', index=0)
    <Control name='_authenticator' type='hidden'>
    >>> self.browser.getControl('Current password').value = 'secret'
    >>> self.browser.getControl('New password').value = 'super-secret'
    >>> self.browser.getControl('Confirm password').value = 'super-secret'
    >>> self.browser.getControl('Change Password').click()
    >>> 'Password changed' in self.browser.contents
    True

Okay the password has been changed, let's logout and login again with the new password.

    >>> self.browser.open('http://nohost/plone/logout')
    >>> self.browser.open('http://nohost/plone/')
    >>> self.browser.getLink('Log in').click()
    >>> self.browser.getControl('Login Name').value = 'test_user_1_'
    >>> self.browser.getControl('Password').value = 'super-secret'
    >>> self.browser.getControl('Log in').click()

If we are logged in the change password form is available

    >>> self.browser.open('http://nohost/plone/' + view_name)
    >>> 'Please log in' in self.browser.contents
    False


Password Validation Plugin
--------------------------

Now let's test using a PAS Password validation plugin. Add a test plugin.

    >>> self.addParrotPasswordPolicy()

    >>> self.browser.open('http://nohost/plone/' + view_name)

Check that we are given instructions on what is a valid password

   >>> print self.browser.contents
    <...
    ...Enter your new password. Must not be dead...


Let's try to change the password with an invalid password:

    >>> self.browser.getControl('Current password').value = 'super-secret'
    >>> self.browser.getControl('New password').value = 'dead parrot'
    >>> self.browser.getControl('Confirm password').value = 'dead parrot'
    >>> self.browser.getControl('Change Password').click()
    >>> print self.browser.contents
    <...
    ...Must not be dead...

Now try a valid password

    >>> self.browser.getControl('Current password').value = 'super-secret'
    >>> self.browser.getControl('New password').value = 'fish'
    >>> self.browser.getControl('Confirm password').value = 'fish'
    >>> self.browser.getControl('Change Password').click()
    >>> print self.browser.contents
    <...
    ...Password changed...

Form Validation
---------------

Firstly try to post form without filling in any fields:

    >>> self.browser.open('http://nohost/plone/' + view_name)
    >>> self.browser.getControl('Change Password').click()
    >>> 'Required input is missing.' in self.browser.contents
    True

Let's try to enter not valid current password:

    >>> self.browser.getControl('Current password').value = 'invalid-password'
    >>> self.browser.getControl('Change Password').click()
    >>> 'Incorrect value for current password' in self.browser.contents
    True

Then post form with new password that is not equal to confirmed password:

    >>> self.browser.getControl('New password').value = 'new-password'
    >>> self.browser.getControl('Confirm password').value = 'new-password-1'
    >>> self.browser.getControl('Change Password').click()
    >>> 'Your password and confirmation did not match. Please try again.' in self.browser.contents
    True
