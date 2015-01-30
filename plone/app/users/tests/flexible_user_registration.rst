Testing the flexible user registration
======================================

    >>> browser = self.browser
    >>> from zope.component import getUtility
    >>> from plone.keyring.interfaces import IKeyManager
    >>> import hmac
    >>> from hashlib import sha1
    >>> def getAuth():
    ...     manager = getUtility(IKeyManager)
    ...     try:
    ...         ring = manager[u'_forms']
    ...     except:
    ...         ring = manager[u'_system']
    ...     secret = ring.current
    ...     return hmac.new(secret, 'admin', sha1).hexdigest()


First things first... turn on self-registration so that we can see the
@@register form. Also, let users select their own password so we don't
depend on a mail server properly set-up:
    >>> browser.open('http://nohost/plone/login_form')
    >>> browser.getControl('Login Name').value = 'admin'
    >>> browser.getControl('Password').value = 'secret'
    >>> browser.getControl('Log in').click()
    >>> browser.open('http://nohost/plone/@@security-controlpanel')
    >>> browser.getControl('Enable self-registration').selected = True
    >>> browser.getControl('Let users select their own passwords').selected = True
    >>> browser.getControl('Save').click()
    >>> 'Changes saved' in browser.contents
    True

Check that the site admin has a link to the configlet in the control panel.
    >>> browser.open('http://nohost/plone/plone_control_panel')
    >>> browser.getLink('Users and Groups').click()
    >>> 'Member fields' in browser.contents
    True
    >>> link = browser.getLink(url='http://nohost/plone/@@member-fields')
    >>> link
    <Link ...>
    >>> link.click()
    >>> 'Edit Member Form Fields' in browser.contents
    True

Check default form fields
    >>> form = browser.getForm(action='http://nohost/plone/@@member-fields')
    >>> form_control_ids = [c.id for c in form.mech_form.controls if c.id and c.id.startswith('form-widgets')]
    >>> form_control_ids
    ['form-widgets-fullname', 'form-widgets-email']

Check "Settings" links::
    >>> 'href="http://nohost/plone/member-fields/fullname"' in browser.contents
    True

    >>> 'href="http://nohost/plone/member-fields/email"' in browser.contents
    True

Check delete links::

    >>> 'http://nohost/plone/member-fields/fullname/@@delete' in browser.contents
    False

    >>> 'http://nohost/plone/member-fields/email/@@delete' in browser.contents
    False

Let's try editing a required field::

    >>> settings_link = browser.getLink('Settings')
    >>> settings_link.url
    'http://nohost/plone/member-fields/fullname'

    >>> settings_link.click()
    >>> browser.url
    'http://nohost/plone/member-fields/fullname'
    >>> browser.getControl(label='Title').value
    'Full Name'
    >>> browser.getControl(label='Required').selected
    True

    >>> browser.getControl(label='Title').value = 'Long Name'
    >>> required = browser.getControl(label='Required')
    >>> required.click()
    >>> browser.getControl(label='Save').click()
    >>> browser.url
    'http://nohost/plone/member-fields'
    >>> self.security_settings.use_email_as_login = False

    >>> settings_link = browser.getLink('Settings')
    >>> settings_link.click()

    >>> browser.getControl(label='Title').value
    'Long Name'
    >>> browser.getControl(label='Required').selected
    True

We should be able to add a field::

    >>> browser.open('http://nohost/plone/@@member-fields')
    >>> browser.getForm(id="add-field").submit()
    >>> print browser.url
    http://nohost/plone/member-fields/@@add-field...

    >>> 'Add new field' in browser.contents
    True

Add a text string field
    >>> browser.getControl(label='Title').value = 'Favorite CMS'
    >>> browser.getControl(label='Short Name').value = 'favorite_cms'
    >>> browser.getControl(label='Help Text').value = 'Think about it'
    >>> browser.getControl(label='Add').click()

    >>> browser.url
    'http://nohost/plone/member-fields'

    >>> 'favorite_cms' in browser.contents
    True

    >>> 'Favorite CMS' in browser.contents
    True

    >>> 'Think about it' in browser.contents
    True

Check our new field's settings::

    >>> browser.getLink(url='http://nohost/plone/member-fields/favorite_cms').click()
    >>> browser.getControl(label='Title').value
    'Favorite CMS'

The new field should be editable::

    >>> browser.getControl(label='Title').value ='Favourite CMS'
    >>> browser.getControl(label='Save').click()
    >>> 'Favourite CMS' in browser.contents
    True

Let's see if our new field is actually on personal information::

    >>> browser.open('http://nohost/plone/@@personal-information')
    >>> 'Favourite CMS' in browser.contents
    True

    >>> 'Think about it' in browser.contents
    True


Log out. Assert that we now have the home_page in the join form.

    >>> browser.getLink(url='http://nohost/plone/logout').click()
    >>> 'Log in' in browser.contents
    True
    >>> browser.open('http://nohost/plone/@@register')
    >>> 'Registration form' in browser.contents
    True
    >>> 'Full Name' in browser.contents
    True
    >>> 'User Name' in browser.contents
    True
    >>> 'E-mail' in browser.contents
    True

Log in again

    >>> browser.open('http://nohost/plone/login_form')
    >>> browser.getControl('Login Name').value = 'admin'
    >>> browser.getControl('Password').value = 'secret'
    >>> browser.getControl('Log in').click()

# Check register form with portrait field.
#
#     >>> portal.portal_properties.site_properties._updateProperty('user_registration_fields', ['portrait'# ])
#     >>> browser.open('http://nohost/plone/@@register')
#     >>> 'Registration form' in browser.contents
#     True
#     >>> 'Portrait' in browser.contents
#     True
#     >>> from pkg_resources import resource_stream
#     >>> portrait_file = resource_stream("plone.app.users.tests", 'onepixel.jpg')
#     >>> browser.getControl(name='form.widgets.portrait').add_file(portrait_file, "image/jpg", "onepixel.# jpg")
#     >>> browser.getControl('User Name').value = 'testuser'
#     >>> browser.getControl('E-mail').value = 'test@example.com'
#     >>> browser.getControl('Password').value = 'testpassword'
#     >>> browser.getControl('Confirm password').value = 'testpassword'
#     >>> browser.getControl('Register').click()
#     >>> browser.contents
#     '...Welcome!...You have been registered...'
#
# Check more validation errors. Test Confirmation Password and invalid
# email, and reserved user name validations:
#
#     >>> portal.portal_properties.site_properties._updateProperty('user_registration_fields', [# 'username', 'email', 'password', 'mail_me'])
#     >>> browser.open('http://nohost/plone/@@register')
#     >>> 'Registration form' in browser.contents
#     True
#     >>> browser.getControl('User Name').value = 'plone'
#     >>> browser.getControl('E-mail').value = 'invalid email'
#     >>> browser.getControl('Password').value = 'testpassword'
#     >>> browser.getControl('Confirm password').value = 'testpassword2'
#     >>> browser.getControl('Register').click()
#     >>> browser.contents
#     '...There were errors...'
#     >>> browser.contents
#     '...This username is reserved...Invalid email address...Passwords do not match...'
#
# Now also check username which is already in use:
#
#     >>> browser.getControl('User Name').value = 'admin'
#     >>> browser.getControl('Register').click()
#     >>> browser.contents
#     '...The login name you selected is already in use...'
#