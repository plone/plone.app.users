Testing the personal information form
=====================================

Viewing the  personal information
---------------------------------

This is about the 'personal-information' view.

    >>> view_name = '@@personal-information'

Viewing user data shouldn't be possible for anonymous users:

    >>> self.browser.open("http://nohost/plone/" + view_name)
    >>> 'Login Name' in self.browser.contents
    True

So let's login as Plone user:
    >>> self.browser.open('http://nohost/plone/')
    >>> self.browser.getLink('Log in').click()
    >>> self.browser.getControl('Login Name').value = 'test_user_1_'
    >>> self.browser.getControl('Password').value = 'secret'
    >>> self.browser.getControl('Log in').click()

Now we should be able to access the user data panel:

    >>> self.browser.open("http://nohost/plone/" + view_name)
    >>> 'Login Name' in self.browser.contents
    False
    >>> self.browser.url.endswith(view_name)
    True

We have these controls in the form:

    >>> self.browser.getControl('Full Name').value
    ''
    >>> self.browser.getControl('E-mail').value
    ''

The form should be using CSRF protection:

    >>> self.browser.getControl(name='_authenticator', index=0)
    <Control name='_authenticator' type='hidden'>


Trying to save without changes
------------------------------

Now can we save this form without changes?

    >>> self.browser.getControl('Save').click()
    >>> 'Login Name' in self.browser.contents
    False
    >>> self.browser.url.endswith(view_name)
    True
    >>> self.browser.getControl('Save').click()
    >>> 'Required input is missing.' in self.browser.contents
    True

As we have a required field "email", which hasn't been pre-filled in this test,
we will get an error message. (In the real world, users would have an e-mail
address filled in.)


Modifying user data
-------------------

If we do set an e-mail address, we should be able to save the form.

    >>> full_name = 'Plone user'
    >>> self.browser.getControl('Full Name').value = full_name

    >>> email_address = 'person@example.com'
    >>> self.browser.getControl('E-mail').value = email_address

    >>> self.browser.getControl('Save').click()
    >>> 'Required input is missing.' in self.browser.contents
    False
    >>> 'No changes made.' in self.browser.contents
    False
    >>> 'Changes saved.' in self.browser.contents
    True



We should be able to check that value for email address now is the same as what
we put in.

    >>> member = self.membership.getMemberById('test_user_1_')
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

    >>> self.browser.getControl('Full Name').value = ''
    >>> self.browser.getControl('Save').click()
    >>> 'Required input is missing.' in self.browser.contents
    False
    >>> 'No changes made.' in self.browser.contents
    False
    >>> 'Changes saved.' in self.browser.contents
    True

Check the values

    >>> member = self.membership.getMemberById('test_user_1_')
    >>> marker = object()
    >>> member.getProperty('fullname', marker)
    ''
    >>> member.getProperty('email', marker) == email_address
    True

Set the full name again:

    >>> full_name = 'Plone user'
    >>> self.browser.getControl('Full Name').value = full_name
    >>> self.browser.getControl('Save').click()
    >>> member = self.membership.getMemberById('test_user_1_')
    >>> member.getProperty('fullname', marker) == full_name
    True


Modifying other users's data
----------------------------

When trying to access the personal-information of the admin user
we still get our own data

    >>> self.browser.open('http://nohost/plone/' + view_name + '?userid=admin')
    >>> self.browser.getControl('Full Name').value == full_name
    True


Modifying user data in email mode
---------------------------------

Let's switch to using Email as Login Name

    >>> self.security_settings.use_email_as_login = True
    >>> self.browser.open("http://nohost/plone/" + view_name)

Update our email and see if login name was synced:

    >>> self.browser.getControl('E-mail').value = 'my.new.email@example.com'
    >>> self.browser.getControl('Save').click()
    >>> 'Changes saved.' in self.browser.contents
    True
    >>> member = self.membership.getMemberById('test_user_1_')
    >>> member.getUserName()
    'my.new.email@example.com'

Now add another user and try to update our email to that other user id. This
should fail with validation errors.

    >>> portal.acl_users._doAddUser('user2@example.com', 'password1', ('Member',), ())
    <PloneUser 'user2@example.com'>

    >>> self.browser.open("http://nohost/plone/" + view_name)
    >>> self.browser.getControl('E-mail').value = 'user2@example.com'
    >>> self.browser.getControl('Save').click()
    >>> 'The email address you selected is already in use or is not valid as login name. Please choose another' in self.browser.contents
    True

Revert back from email mode

    >>> self.security_settings.use_email_as_login = False