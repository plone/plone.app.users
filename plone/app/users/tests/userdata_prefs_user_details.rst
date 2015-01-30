Admin modifies user information thru 'Users and groups'
---------------------------------------------------------------------

Set Up
======

    >>> from plone.app.testing import TEST_USER_ID
    >>> from plone.app.testing import TEST_USER_NAME
    >>> from plone.testing.z2 import Browser

    >>> import transaction

    >>> app = layer['app']
    >>> portal = layer['portal']
    >>> membership = portal.portal_membership

    >>> user_information_url = 'http://nohost/plone/@@user-information?userid={0}'.format(TEST_USER_ID)

    >>> browser = Browser(app)
    >>> browser.handleErrors = False

An admin can modify user information thru the @@user-information form in Users and Groups
config page.

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
    >>> browser.getLink('Personal Information').click()
    >>> browser.url == user_information_url
    True

We have these controls in the form:

    >>> browser.getControl('Full Name').value
    ''
    >>> browser.getControl('E-mail').value
    ''

The form should be using CSRF protection:

    >>> browser.getControl(name='_authenticator', index=0)
    <Control name='_authenticator' type='hidden'>


Modifying user data
-------------------

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

Finally let's see if Cancel button still leaves us on selected user Personal
Information form::

    >>> browser.getControl('Cancel').click()
    >>> 'Changes canceled.' in browser.contents
    True
    >>> 'Change personal information for test_user_1_' in browser.contents
    True
