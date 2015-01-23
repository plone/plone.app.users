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
    >>> browser.getControl('Home page').value
    ''
    >>> browser.getControl('Biography').value
    ''
    >>> browser.getControl(name='form.widgets.portrait').value

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

    >>> home_page = 'http://www.plone.org/'
    >>> browser.getControl('Home page').value = home_page

    >>> description = 'Far far away, behind the word mountains, far from the countries Vokalia and Consonantia, there live the blind texts.'
    >>> browser.getControl('Biography').value = description

    >>> email_address = 'person@example.com'
    >>> browser.getControl('E-mail').value = email_address

    >>> location = 'Somewhere'
    >>> browser.getControl('Location').value = location

    >>> from pkg_resources import resource_stream
    >>> portrait_file = resource_stream("plone.app.users.tests", 'onepixel.jpg')
    >>> browser.getControl(name='form.widgets.portrait').add_file(portrait_file, "image/jpg", "onepixel.jpg")

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

    >>> home_page_value = member.getProperty('home_page','')
    >>> home_page_value == home_page
    True

    >>> description_value = member.getProperty('description','')
    >>> description_value == description
    True

    >>> email_value = member.getProperty('email','')
    >>> email_value == email_address
    True

    >>> location_value = member.getProperty('location','')
    >>> location_value == location
    True

    >>> portrait_value = membership.getPersonalPortrait(TEST_USER_ID)
    >>> portrait_value
    <Image at /plone/portal_memberdata/portraits/test_user_1_>

Is the data of the created Image the same as the (scaled) orignal image?

    >>> portrait_file.seek(0)
    >>> from Products.PlonePAS.utils import scale_image
    >>> scaled_image_data = scale_image(portrait_file)[0].read()
    >>> portrait_value.data == scaled_image_data
    True


Clearing user data
------------------

If we empty all non-required inputs, the corresponding fields should
be cleared, instead of keeping their old value

    >>> browser.getControl('Full Name').value = ''
    >>> browser.getControl('Home page').value = ''
    >>> browser.getControl('Biography').value = ''
    >>> browser.getControl('Location').value = ''
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
    >>> member.getProperty('fullname', marker)
    ''
    >>> member.getProperty('home_page', marker)
    ''
    >>> member.getProperty('description', marker)
    ''
    >>> member.getProperty('email', marker) == email_address
    True
    >>> member.getProperty('location', marker)
    ''

Set the full name again:

    >>> full_name = 'Plone user'
    >>> browser.getControl('Full Name').value = full_name
    >>> browser.getControl('Save').click()
    >>> member = membership.getMemberById(TEST_USER_ID)
    >>> member.getProperty('fullname', marker) == full_name
    True

Can we delete the Image using the checkbox?

    >>> browser.getControl('Remove existing image').selected = True
    >>> browser.getControl('Save').click()
    >>> 'Changes saved.' in browser.contents
    True

Does the user have the default portrait now?  Note that this differs
slightly depending on which Plone version you have.  Products.PlonePAS
4.0.5 or higher has .png, earlier has .gif.

    >>> portrait_value = membership.getPersonalPortrait(TEST_USER_ID)
    >>> portrait_value
    <FSImage at /plone/defaultUser...>

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
