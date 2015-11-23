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
    >>> browser.open('http://nohost/plone/@@overview-controlpanel')
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
    ['form-widgets-fullname', 'form-widgets-email', 'form-widgets-home_page', 'form-widgets-description', 'form-widgets-location', 'form-widgets-portrait-input']

Check default form fields are not editable::
    >>> 'href="http://nohost/plone/member-fields/fullname"' in browser.contents
    False

    >>> 'href="http://nohost/plone/member-fields/email"' in browser.contents
    False

Let's add favorite_cms to the list of registration form fields.
(Setting this by hand since add/remove widget doesn't work properly without javascript)


We should be able to add a field::

    >>> browser.open('http://nohost/plone/@@member-fields')
    >>> browser.getLink(id="add-field").click()
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
    'http://nohost/plone/member-fields/@@add-field'

    >>> browser.open('http://nohost/plone/@@member-fields')
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

We make it appear in both registration and user profile::

    >>> chkboxes = browser.getControl(name='form.widgets.IUserFormSelection.forms:list')
    >>> chkboxes.controls[0].selected = True
    >>> chkboxes.controls[1].selected = True
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
    >>> browser.contents
    '...E-mail...Password...Confirm password...'
    >>> browser.getControl('User Name').value = 'test1'
    >>> browser.getControl('Full Name').value = 'Mister test1'
    >>> browser.getControl('E-mail').value = 'test1@example.com'
    >>> browser.getControl('Password').value = 'testpassword'
    >>> browser.getControl('Confirm password').value = 'testpassword'
    >>> browser.getControl('Register').click()
    >>> browser.contents
    '...Welcome!...You have been registered...'

Log in again

    >>> browser.open('http://nohost/plone/login_form')
    >>> browser.getControl('Login Name').value = 'admin'
    >>> browser.getControl('Password').value = 'secret'
    >>> browser.getControl('Log in').click()

Add portrait to registration form

    >>> browser.open('http://nohost/plone/@@member-fields')
    >>> browser.getLink(url='http://nohost/plone/member-fields/portrait').click()
    >>> chkboxes = browser.getControl(name='form.widgets.IUserFormSelection.forms:list')
    >>> chkboxes.controls[0].selected = True
    >>> chkboxes.controls[1].selected = True
    >>> browser.getControl(label='Save').click()

Check register form with portrait field.

    >>> browser.open('http://nohost/plone/logout')
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
    '...Invalid email address...This username is reserved...Passwords do not match...'

Now also check username which is already in use:
    >>> browser.getControl('User Name').value = 'admin'
    >>> browser.getControl('Register').click()
    >>> browser.contents
    '...The login name you selected is already in use...'
