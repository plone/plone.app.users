======================================
Testing the flexible user registration
======================================

    >>> from plone.testing.z2 import Browser
    >>> import transaction
    >>> app = layer['app']
    >>> portal = layer['portal']
    >>> browser = Browser(app)
    >>> browser.handleErrors = False
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
    >>> 'Member Registration' in browser.contents
    True
    >>> link = browser.getLink(url='http://nohost/plone/@@member-registration')
    >>> link
    <Link ...>
    >>> link.click()
    >>> 'Registration settings' in browser.contents
    True

"Location" and "Home page" are not in the form by default.

    >>> form = browser.getForm(action='http://nohost/plone/@@member-registration')
    >>> user_registration_fields = form.getControl(name='form.widgets.user_registration_fields.to')
    >>> 'location' in user_registration_fields.displayOptions
    False
    >>> 'home_page' in user_registration_fields.displayOptions
    False

    >>> browser.getControl(name='_authenticator', index=0)
    <Control name='_authenticator' type='hidden'>

Let's add home_page to the list of registration form fields.
(Setting this by hand since add/remove widget doesn't work properly without javascript)
    >>> portal.portal_properties.site_properties._updateProperty('user_registration_fields', ['fullname', 'username', 'email', 'password', 'home_page'])
    >>> transaction.commit()

It should show up at the end of the form.
    >>> browser.open('http://nohost/plone/@@register')
    >>> browser.contents
    '...User Name...Home page...'

Check that 'home_page' is now in the right box (enabled registration form fields).

    >>> browser.open('http://nohost/plone/@@member-registration')
    >>> form = browser.getForm(action='http://nohost/plone/@@member-registration')
    >>> enabled_fields = form.getControl(name='form.widgets.user_registration_fields.to')
    >>> 'home_page' in enabled_fields.displayOptions
    True

Log out. Assert that we now have the home_page in the join form.

    >>> browser.getLink(url='http://nohost/plone/logout').click()
    >>> 'Log in' in browser.contents
    True
    >>> browser.open('http://nohost/plone/@@register')
    >>> 'Registration form' in browser.contents
    True
    >>> 'Home page' in browser.contents
    True

Rearrange the fields
(Setting this by hand since add/remove widget doesn't work properly without javascript)
    >>> portal.portal_properties.site_properties._updateProperty('user_registration_fields', ['fullname', 'username', 'password', 'home_page', 'email'])
    >>> transaction.commit()
    >>> browser.open('http://nohost/plone/@@register')
    >>> browser.contents
    '...Home page...E-mail...'

Now remove all required fields from registration fields and check that we still
get all required fields on registration form.

    >>> browser.open('http://nohost/plone/login_form')
    >>> browser.getControl('Login Name').value = 'admin'
    >>> browser.getControl('Password').value = 'secret'
    >>> browser.getControl('Log in').click()
    >>> data = '&'.join([
    ...     'form.widgets.user_registration_fields:list=fullname',
    ...     'form.actions.save=Save',
    ...     'form.buttons.save=Save',
    ...     '_authenticator=' + getAuth()])
    >>> browser.open('http://nohost/plone/@@member-registration', data)
    >>> 'Changes saved.' in browser.contents
    True

    >>> browser.getLink(url='http://nohost/plone/logout').click()
    >>> 'Log in' in browser.contents
    True
    >>> browser.open('http://nohost/plone/@@register')
    >>> 'Registration form' in browser.contents
    True
    >>> browser.contents
    '...User Name...'
    >>> browser.contents
    '...Password...'
    >>> browser.contents
    '...Confirm password...'
    >>> browser.contents
    '...Full Name...'
    >>> browser.contents
    '...E-mail...'


Check render register form in 'Use Email As Login' mode.

    >>> from plone.app.users.tests.base import get_security_settings
    >>> security_settings = get_security_settings()
    >>> security_settings.use_email_as_login = True
    >>> portal.portal_properties.site_properties._updateProperty('user_registration_fields', ['username'])
    >>> transaction.commit()
    >>> browser.open('http://nohost/plone/@@register')
    >>> 'Registration form' in browser.contents
    True
    >>> browser.contents
    '...E-mail...Password...Confirm password...'
    >>> browser.getControl('E-mail').value = 'test1@example.com'
    >>> browser.getControl('Password').value = 'testpassword'
    >>> browser.getControl('Confirm password').value = 'testpassword'
    >>> browser.getControl('Register').click()
    >>> browser.contents
    '...Welcome!...You have been registered...'

Revert email mode.

    >>> security_settings.use_email_as_login = False

Check register form with portrait field.

    >>> portal.portal_properties.site_properties._updateProperty('user_registration_fields', ['portrait'])
    >>> transaction.commit()

    >>> browser.open('http://nohost/plone/@@register')
    >>> 'Registration form' in browser.contents
    True
    >>> 'Portrait' in browser.contents
    True
    >>> from pkg_resources import resource_stream
    >>> portrait_file = resource_stream("plone.app.users.tests", 'onepixel.jpg')
    >>> browser.getControl(name='form.widgets.portrait').add_file(portrait_file, "image/jpg", "onepixel.jpg")
    >>> browser.getControl('User Name').value = 'testuser'
    >>> browser.getControl('E-mail').value = 'test@example.com'
    >>> browser.getControl('Password').value = 'testpassword'
    >>> browser.getControl('Confirm password').value = 'testpassword'
    >>> browser.getControl('Register').click()
    >>> browser.contents
    '...Welcome!...You have been registered...'

Check more validation errors. Test Confirmation Password and invalid
email, and reserved user name validations:

    >>> portal.portal_properties.site_properties._updateProperty('user_registration_fields', ['username', 'email', 'password', 'mail_me'])
    >>> transaction.commit()

    >>> browser.open('http://nohost/plone/@@register')
    >>> 'Registration form' in browser.contents
    True
    >>> browser.getControl('User Name').value = 'plone'
    >>> browser.getControl('E-mail').value = 'invalid email'
    >>> browser.getControl('Password').value = 'testpassword'
    >>> browser.getControl('Confirm password').value = 'testpassword2'
    >>> browser.getControl('Register').click()
    >>> browser.contents
    '...There were errors...'
    >>> browser.contents
    '...This username is reserved...Invalid email address...Passwords do not match...'

Now also check username which is already in use:

    >>> browser.getControl('User Name').value = 'admin'
    >>> browser.getControl('Register').click()
    >>> browser.contents
    '...The login name you selected is already in use...'

More Tests for Control Panel Form
---------------------------------

What if we do not do any changes but click submit button?

We do this with 'open' method as our list widget uses javascript that is not
supported by our test browser.

Set list of registration fields:

    >>> portal.portal_properties.site_properties._updateProperty('user_registration_fields', ['username', 'email'])
    >>> transaction.commit()

Login as admin.

    >>> browser.open('http://nohost/plone/login_form')
    >>> browser.getControl('Login Name').value = 'admin'
    >>> browser.getControl('Password').value = 'secret'
    >>> browser.getControl('Log in').click()

Open up control panel form.

    >>> browser.open('http://nohost/plone/@@member-registration')
    >>> 'Registration settings' in browser.contents
    True

Submit form with the same set of fields:

    >>> data = '&'.join([
    ...     'form.widgets.user_registration_fields:list=username',
    ...     'form.widgets.user_registration_fields:list=email',
    ...     'form.actions.save=Save',
    ...     'form.buttons.save=Save',
    ...     '_authenticator=' + getAuth()])
    >>> browser.open('http://nohost/plone/@@member-registration', data)
    >>> 'No changes made.' in browser.contents
    True

Now let's test Cancel button:

    >>> browser.getControl('Cancel').click()
    >>> browser.url
    'http://nohost/plone/plone_control_panel'
    >>> 'Changes canceled.' in browser.contents
    True
