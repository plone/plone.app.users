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
    >>> browser.getControl('Home page').value
    ''
    >>> browser.getControl('Biography').value
    ''
    >>> browser.getControl(name='form.widgets.portrait').value

The form should be using CSRF protection:

    >>> browser.getControl(name='_authenticator', index=0)
    <Control name='_authenticator' type='hidden'>


Modifying user data
-------------------

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

Is the users's portrait a newly created Image?

    >>> portrait_value = membership.getPersonalPortrait(TEST_USER_ID)
    >>> portrait_value
    <Image at /plone/portal_memberdata/portraits/test_user_1_>

Is the data of the created Image the same as the (scaled) orignal image?

    >>> portrait_file.seek(0)
    >>> from Products.PlonePAS.utils import scale_image
    >>> scaled_image_data = scale_image(portrait_file)[0].read()
    >>> portrait_value.data == scaled_image_data
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

Finally let's see if Cancel button still leaves us on selected user Personal
Information form::

    >>> browser.getControl('Cancel').click()
    >>> 'Changes canceled.' in browser.contents
    True
    >>> 'Change personal information for test_user_1_' in browser.contents
    True
