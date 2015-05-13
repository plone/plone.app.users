=====================================
Testing the personal information form
=====================================

Set Up
======

    >>> from plone.app.testing import TEST_USER_ID
    >>> from plone.app.testing import TEST_USER_NAME
    >>> from plone.app.testing import TEST_USER_PASSWORD
    >>> from plone.testing.z2 import Browser

    >>> import transaction

    >>> app = layer['app']
    >>> portal = layer['portal']
    >>> membership = portal.portal_membership

    >>> browser = Browser(app)
    >>> browser.handleErrors = False

Viewing the  personal information
---------------------------------

This is about the 'personal-information' view.

    >>> view_name = '@@personal-information'
    >>> view_url = 'http://nohost/plone/{0}'.format(view_name)

Viewing user data shouldn't be possible for anonymous users:

    >>> browser.open(view_url)
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

    >>> browser.open(view_url)
    >>> 'Login Name' in browser.contents
    False
    >>> browser.url.endswith(view_name)
    True

We have these controls in the form:

    >>> browser.getControl('Full Name').value
    ''
    >>> browser.getControl('E-mail').value
    ''

The form should be using CSRF protection:

    >>> browser.getControl(name='_authenticator', index=0)
    <Control name='_authenticator' type='hidden'>


Trying to save without changes
------------------------------

Now can we save this form without changes?

    >>> browser.getControl('Save').click()
    >>> 'Login Name' in browser.contents
    False
    >>> browser.url.endswith(view_name)
    True
    >>> browser.getControl('Save').click()
    >>> 'Required input is missing.' in browser.contents
    True

As we have a required field "email", which hasn't been pre-filled in this test,
we will get an error message. (In the real world, users would have an e-mail
address filled in.)


Modifying user data
-------------------

If we do set an e-mail address, we should be able to save the form.

    >>> full_name = 'Plone user'
    >>> browser.getControl('Full Name').value = full_name

    >>> email_address = 'person@example.com'
    >>> browser.getControl('E-mail').value = email_address

    >>> browser.getControl('Save').click()
    >>> 'Required input is missing.' in browser.contents
    False
    >>> 'No changes made.' in browser.contents
    False
    >>> 'Changes saved.' in browser.contents
    True



We should be able to check that value for email address now is the same as what
we put in.

    >>> member = membership.getMemberById(TEST_USER_ID)
    >>> fullname_value = member.getProperty('fullname','')
    >>> fullname_value == full_name
    True

    >>> email_value = member.getProperty('email','')
    >>> email_value == email_address
    True


Clearing user data
------------------

If we empty all non-required inputs, the corresponding fields should
be cleared, instead of keeping their old value

    >>> browser.getControl('Full Name').value = ''
    >>> browser.getControl('Save').click()
    >>> 'Required input is missing.' in browser.contents
    False
    >>> 'No changes made.' in browser.contents
    False
    >>> 'Changes saved.' in browser.contents
    True

Check the values

    >>> member = membership.getMemberById(TEST_USER_ID)
    >>> marker = object()
    >>> not member.getProperty('fullname', marker)
    True
    >>> member.getProperty('email', marker) == email_address
    True

Set the full name again:

    >>> full_name = 'Plone user'
    >>> browser.getControl('Full Name').value = full_name
    >>> browser.getControl('Save').click()
    >>> member = membership.getMemberById(TEST_USER_ID)
    >>> member.getProperty('fullname', marker) == full_name
    True


Modifying other users's data
----------------------------

When trying to access the personal-information of the admin user
we still get our own data

    >>> browser.open('http://nohost/plone/' + view_name + '?userid=admin')
    >>> browser.getControl('Full Name').value == full_name
    True


Modifying user data in email mode
---------------------------------

Let's switch to using Email as Login Name

    >>> from plone.app.users.tests.base import get_security_settings
    >>> security_settings = get_security_settings()
    >>> security_settings.use_email_as_login = True
    >>> transaction.commit()
    >>> browser.open("http://nohost/plone/" + view_name)

Update our email and see if login name was synced:

    >>> browser.getControl('E-mail').value = 'my.new.email@example.com'
    >>> browser.getControl('Save').click()
    >>> 'Changes saved.' in browser.contents
    True
    >>> member = membership.getMemberById(TEST_USER_ID)
    >>> member.getUserName()
    'my.new.email@example.com'

Now add another user and try to update our email to that other user id. This
should fail with validation errors.

    >>> portal.acl_users._doAddUser('user2@example.com', 'password1', ('Member',), ())
    <PloneUser 'user2@example.com'>
    >>> transaction.commit()

    >>> browser.open(view_url)
    >>> browser.getControl('E-mail').value = 'user2@example.com'
    >>> browser.getControl('Save').click()
    >>> 'The email address you selected is already in use or is not valid as login name. Please choose another' in browser.contents
    True

Revert back from email mode

    >>> security_settings.use_email_as_login = False
