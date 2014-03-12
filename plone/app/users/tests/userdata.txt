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
    >>> self.browser.getControl('Home page').value
    ''
    >>> self.browser.getControl('Biography').value
    ''
    >>> self.browser.getControl(name='form.widgets.portrait').value

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

    >>> home_page = 'http://www.plone.org/'
    >>> self.browser.getControl('Home page').value = home_page

    >>> description = 'Far far away, behind the word mountains, far from the countries Vokalia and Consonantia, there live the blind texts.'
    >>> self.browser.getControl('Biography').value = description

    >>> email_address = 'person@example.com'
    >>> self.browser.getControl('E-mail').value = email_address

    >>> location = 'Somewhere'
    >>> self.browser.getControl('Location').value = location

    >>> from pkg_resources import resource_stream
    >>> portrait_file = resource_stream("plone.app.users.tests", 'onepixel.jpg')
    >>> self.browser.getControl(name='form.widgets.portrait').add_file(portrait_file, "image/jpg", "onepixel.jpg")

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

    >>> portrait_value = self.membership.getPersonalPortrait('test_user_1_')
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

    >>> self.browser.getControl('Full Name').value = ''
    >>> self.browser.getControl('Home page').value = ''
    >>> self.browser.getControl('Biography').value = ''
    >>> self.browser.getControl('Location').value = ''
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
    >>> self.browser.getControl('Full Name').value = full_name
    >>> self.browser.getControl('Save').click()
    >>> member = self.membership.getMemberById('test_user_1_')
    >>> member.getProperty('fullname', marker) == full_name
    True

Can we delete the Image using the checkbox?

    >>> self.browser.getControl('Remove existing image').selected = True
    >>> self.browser.getControl('Save').click()
    >>> 'Changes saved.' in self.browser.contents
    True

Does the user have the default portrait now?  Note that this differs
slightly depending on which Plone version you have.  Products.PlonePAS
4.0.5 or higher has .png, earlier has .gif.

    >>> portrait_value = self.membership.getPersonalPortrait('test_user_1_')
    >>> portrait_value
    <FSImage at /plone/defaultUser...>

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

    >>> portal.portal_properties.site_properties._updateProperty('use_email_as_login', True)
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

    >>> portal.portal_properties.site_properties._updateProperty('use_email_as_login', False)
