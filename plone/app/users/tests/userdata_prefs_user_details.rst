Admin modifies user information thru 'Users and groups'
---------------------------------------------------------------------

An admin can modify user information thru the @@user-information form in Users and Groups
config page.

So let's login as Plone admin:
    >>> self.browser.open('http://nohost/plone/')
    >>> self.browser.getLink('Log in').click()
    >>> self.browser.getControl('Login Name').value = 'admin'
    >>> self.browser.getControl('Password').value = 'secret'
    >>> self.browser.getControl('Log in').click()

Let's see if we can navigate to the user information form in Users and groups
    >>> self.browser.getLink('Site Setup').click()
    >>> self.browser.getLink('Users and Groups').click()
    >>> self.browser.getLink('test_user_1_').click()
    >>> self.browser.getLink('Personal Information').click()
    >>> self.browser.url
    'http://nohost/plone/@@user-information?userid=test_user_1_'

We have these controls in the form:

    >>> self.browser.getControl('Full Name').value
    ''
    >>> self.browser.getControl('E-mail').value
    ''

The form should be using CSRF protection:

    >>> self.browser.getControl(name='_authenticator', index=0)
    <Control name='_authenticator' type='hidden'>


Modifying user data
-------------------

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

Finally let's see if Cancel button still leaves us on selected user Personal
Information form::

    >>> self.browser.getControl('Cancel').click()
    >>> 'Changes canceled.' in self.browser.contents
    True
    >>> 'Change personal information for test_user_1_' in self.browser.contents
    True
