Testing the flexible user registration
======================================

    >>> portal = layer['portal']
    >>> from plone.testing.z2 import Browser
    >>> browser = Browser(layer['app'])
    >>> browser.open('http://nohost/plone')
    >>> list_widget_suffix = ':list'

    Self-registration is disabled, user does not see 'Register' link.
    >>> 'Register' in browser.contents
    False

    Enable self-registration
    >>> browser.open('http://nohost/plone/login_form')
    >>> browser.getControl('Login Name').value = 'admin'
    >>> browser.getControl('Password').value = 'secret'
    >>> browser.getControl('Log in').click()
    >>> browser.open('http://nohost/plone/@@security-controlpanel')
    >>> browser.getControl('Enable self-registration').selected = True
    >>> browser.getControl('Save').click()
    >>> 'Changes saved' in browser.contents
    True

    >>> browser.getLink(url='http://nohost/plone/logout').click()
    >>> 'Log in' in browser.contents
    True

    Logged out user should now see the register link.
    >>> 'Register' in browser.contents
    True

    >>> browser.getLink('Register').click()
    >>> '@@register' in browser.url
    True

    No mailhost has been set up yet. User should not be able to see the form.
    >>> browser.contents
    '...This site...valid email setup...cannot register at this time...'
    >>> 'User Name' in browser.contents
    False

    Check that the form is not displayed when no mailhost is defined and users
    cannot choose their own passwords.
    >>> 'User Name' in browser.contents
    False
    >>> 'Password' in browser.contents
    False
    >>> 'Confirm password' in browser.contents
    False

    Set up a mailhost...
    >>> from plone.app.users.tests.base import setMailHost, unsetMailHost
    >>> from plone.app.users.tests.base import set_mock_mailhost, unset_mock_mailhost
    >>> set_mock_mailhost(portal)
    >>> setMailHost()
    >>> browser.open('http://nohost/plone/@@register')

    The form should now be visible, sans password, since the user still cannot
    set it.
    >>> 'User Name' in browser.contents
    True
    >>> 'Password' in browser.contents
    False
    >>> 'Confirm password' in browser.contents
    False

    Ensure that fields are being validated
    >>> browser.getControl('Register').click()
    >>> browser.contents
    '...There were errors...User Name...Required input is missing...'
    >>> browser.contents
    '...There were errors...E-mail...Required input is missing...'

    We have to provide a valid email address
    >>> browser.open('http://nohost/plone/@@register')
    >>> browser.getControl('User Name').value = 'user1'
    >>> browser.getControl('E-mail').value = 'user1-AT-example.com'
    >>> browser.getControl('Register').click()
    >>> browser.contents
    '...There were errors...Invalid email address...'
    
    Fill out the form. 
    >>> browser.getControl('User Name').value = 'user1'
    >>> browser.getControl('E-mail').value = 'user1@example.com'
    >>> browser.getControl('Register').click()
    >>> 'Failed to create your account' not in browser.contents
    True

    Ensure that the user has, in fact, been added.
    >>> browser.open('http://nohost/plone/login_form')
    >>> browser.getControl('Login Name').value = 'admin'
    >>> browser.getControl('Password').value = 'secret'
    >>> browser.getControl('Log in').click()
    >>> browser.open('http://nohost/plone/@@usergroup-userprefs')
    >>> 'user1' in browser.contents
    True

    Disable the mailhost and enable user ability to set their own password.
    >>> unsetMailHost()
    >>> browser.open('http://nohost/plone/login_form')
    >>> browser.getControl('Login Name').value = 'admin'
    >>> browser.getControl('Password').value = 'secret'
    >>> browser.getControl('Log in').click()
    >>> browser.open('http://nohost/plone/@@security-controlpanel')
    >>> browser.getControl('Let users select their own passwords').selected = True
    >>> browser.getControl('Save').click()
    >>> 'Changes saved' in browser.contents
    True
    >>> browser.getLink(url='http://nohost/plone/logout').click()
    >>> 'Log in' in browser.contents
    True

    >>> browser.getLink('Register').click()
    >>> '@@register' in browser.url
    True

    Check that password is now displayed
    >>> 'Password' in browser.contents
    True
    >>> 'Confirm password' in browser.contents
    True

    Fill out the form.
    >>> browser.getControl('User Name').value = 'user2'
    >>> browser.getControl('E-mail').value = 'user2@example.com'
    >>> browser.getControl('Password').value = 'bigfïsh'
    >>> browser.getControl('Confirm password').value = 'bigfïsh'
    >>> browser.getControl('Register').click()
    >>> browser.contents
    '...Welcome!...You have been registered...'

    Ensure that the user has, in fact, been added.
    >>> browser.open('http://nohost/plone/login_form')
    >>> browser.getControl('Login Name').value = 'admin'
    >>> browser.getControl('Password').value = 'secret'
    >>> browser.getControl('Log in').click()
    >>> browser.open('http://nohost/plone/@@usergroup-userprefs')
    >>> 'user2' in browser.contents
    True

    Sometimes the user may be asked to register in order to access some
    particular view. Let's make sure a came_from parameter in the query
    string will be respected.

    >>> browser.open('http://nohost/plone/@@register?came_from=http://nohost/plone/news')
    >>> browser.getControl('User Name').value = 'user5'
    >>> browser.getControl('E-mail').value = 'user5@example.com'
    >>> browser.getControl('Password').value = 'secret'
    >>> browser.getControl('Confirm password').value = 'secret'
    >>> browser.getControl('Register').click()
    >>> browser.url
    'http://nohost/plone/news'

    Great! The user-facing form works. Let's try the manager's version...
    >>> browser.open('http://nohost/plone/@@usergroup-userprefs')
    >>> browser.getLink('Add New User').click()
    >>> '@@new-user' in browser.url
    True

    Check that password and groups are displayed.
    >>> 'Password' in browser.contents
    True
    >>> 'Confirm password' in browser.contents
    True
    >>> 'Add to the following groups' in browser.contents
    True

    Check that the mail prompt is not displayed, as the mailhost is
    not setup correctly.
    >>> 'Send a confirmation mail with a link to set the password' in browser.contents
    False

    Turn off the ability for users to set their own passwords.  We are
    now back to the default settings.
    >>> browser.open('http://nohost/plone/@@security-controlpanel')
    >>> browser.getControl('Let users select their own passwords').selected = False
    >>> browser.getControl('Save').click()
    >>> 'Changes saved' in browser.contents
    True

    Most fields are displayed again:
    >>> browser.open('http://nohost/plone/@@new-user')
    >>> 'Password' in browser.contents
    True
    >>> 'Confirm password' in browser.contents
    True
    >>> 'Add to the following groups' in browser.contents
    True

    We do not offer the opportunity to send an email though, as the
    mailhost is not set up.
    >>> 'Send a confirmation mail with a link to set the password' in browser.contents
    False

    We have to provide a valid email address
    >>> browser.open('http://nohost/plone/@@new-user')
    >>> browser.getControl('User Name').value = 'user2a'
    >>> browser.getControl('E-mail').value = 'user2a-AT-example.com'
    >>> browser.getControl('Password').value = 'secret'
    >>> browser.getControl('Confirm password').value = 'secret'
    >>> browser.getControl('Register').click()
    >>> browser.contents
    '...There were errors...Invalid email address...'

    Fill out the form.
    >>> browser.open('http://nohost/plone/@@new-user')
    >>> browser.getControl('User Name').value = 'user3'
    >>> browser.getControl('E-mail').value = 'user3@example.com'
    >>> browser.getControl('Password').value = 'secret'
    >>> browser.getControl('Confirm password').value = 'secret'
    >>> browser.getControl('Register').click()
    >>> '@@usergroup-userprefs' in browser.url
    True

    TODO Since the MockMailHost doesn't flip out over missing mail settings, we
    won't see our error message here Figure out a way to do so.

    We should get a warning because no mail could be sent, but the user is
    created anyway.
    Original test was "
    browser.contents
    '...This account has been created, but we were unable to send...'"

    >>> browser.contents
    '...User added...user3...'

    We can really get the new user.
    >>> browser.getLink('user3').click()

    Set up the mailhost and try again.
    >>> setMailHost()
    >>> browser.open('http://nohost/plone/@@new-user')
    >>> 'Password' in browser.contents
    True
    >>> 'Confirm password' in browser.contents
    True
    >>> 'Add to the following groups' in browser.contents
    True

    Check that the mail prompt is displayed correctly now.  Note that
    we never send passwords in the email, only a password reset link.
    >>> 'Send a mail with the password' in browser.contents
    False
    >>> 'Send a confirmation mail with a link to set the password' in browser.contents
    True

    Fill out the form.
    >>> browser.getControl('User Name').value = 'user4'
    >>> browser.getControl('E-mail').value = 'user4@example.com'
    >>> browser.getControl('Reviewers').selected = True

    But, at first, let's try to check form validation a bit. Do not set 'mail me' and 'password' fields.

    By Default Mail Me is checked.
    >>> browser.getControl(name='form.widgets.mail_me' + list_widget_suffix).value in (True, ['selected'])
    True
    >>> browser.getControl(name='form.widgets.mail_me' + list_widget_suffix).value = False
    >>> browser.getControl('Register').click()
    >>> browser.contents
    '...You must set a password or choose to send an email...'

    As we want to validate emails. The password fields have become optional.
    >>> browser.getControl(name='form.widgets.mail_me' + list_widget_suffix).value = True
    >>> browser.getControl('Register').click()
    >>> print browser.url
    http://...@@usergroup-userprefs...
    >>> print browser.contents
    <...User added...user4...

    Check that at least this one error does not show up:
    >>> "Failed to create your account" in browser.contents
    False

    Check that the selected group has been applied to the new user.
    >>> browser.getLink('user4').click()
    >>> browser.getLink('Group Memberships').click()
    >>> browser.contents
    '...Current group memberships...
    ...Reviewers...'


    Now let's test using a PAS Password validation plugin. Add a test plugin.

    >>> from plone.app.users.tests.base import addParrotPasswordPolicy
    >>> addParrotPasswordPolicy(portal)

    Enable setting own password

    Disable the mailhost and enable user ability to set their own password.
    >>> unsetMailHost()
    >>> browser.open('http://nohost/plone/login_form')
    >>> browser.getControl('Login Name').value = 'admin'
    >>> browser.getControl('Password').value = 'secret'
    >>> browser.getControl('Log in').click()
    >>> browser.open('http://nohost/plone/@@security-controlpanel')
    >>> browser.getControl('Let users select their own passwords').selected = True
    >>> browser.getControl('Save').click()
    >>> 'Changes saved' in browser.contents
    True


    Logout and register as a new user

    >>> browser.getLink(url='http://nohost/plone/logout').click()
    >>> 'Log in' in browser.contents
    True

    >>> browser.getLink('Register').click()
    >>> '@@register' in browser.url
    True


    Check that we are given instructions on what is a valid password

    >>> print browser.contents
    <...
    ...Enter your new password. Must not be dead...

    And we no longer see the default message
    >>> 'Minimum 5 characters.' not in browser.contents
    True


    We'll enter an invalid password

    Fill out the form.
    >>> browser.getControl('User Name').value = 'user5pas'
    >>> browser.getControl('E-mail').value = 'user5@example.com'
    >>> browser.getControl('Password').value = 'dead parrot'
    >>> browser.getControl('Confirm password').value = 'dead parrot'
    >>> browser.getControl('Register').click()

    >>> print browser.contents
    <...<div class="fieldErrorBox">...Must not be dead...</div>...


    Now try a valid password

    >>> browser.getControl('Password').value = 'fish'
    >>> browser.getControl('Confirm password').value = 'fish'

    >>> browser.getControl('Register').click()
    >>> browser.contents
    '...Welcome!...You have been registered...'

    Ensure that the user has, in fact, been added.
    >>> browser.open('http://nohost/plone/login_form')
    >>> browser.getControl('Login Name').value = 'admin'
    >>> browser.getControl('Password').value = 'secret'
    >>> browser.getControl('Log in').click()
    >>> browser.open('http://nohost/plone/@@usergroup-userprefs')
    >>> 'user5pas' in browser.contents
    True

    Add the default policy back in so we can test two plugins at once
    >>> from plone.app.users.tests.base import activateDefaultPasswordPolicy
    >>> activateDefaultPasswordPolicy(portal)
    >>> import transaction
    >>> transaction.commit()

    >>> browser.getLink(url='http://nohost/plone/logout').click()
    >>> 'Log in' in browser.contents
    True

    >>> browser.getLink('Register').click()
    >>> '@@register' in browser.url
    True


    Check that we are given instructions on what is a valid password

    >>> print browser.getControl("Password").mech_control.get_labels()[0]._text
    Password...Enter your new password. Must not be dead. Minimum 5 characters...

    We'll enter an invalid password

    Fill out the form.
    >>> browser.getControl('User Name').value = 'user6pas'
    >>> browser.getControl('E-mail').value = 'user6@example.com'
    >>> browser.getControl('Password').value = 'dead'
    >>> browser.getControl('Confirm password').value = 'dead'
    >>> browser.getControl('Register').click()

    >>> print browser.contents
    <...<div class="fieldErrorBox">...Must not be dead. Your password must contain at least 5 characters....</div>...

    Now try a valid password -- and we'll make sure non-ASCII characters are
    handled too.

    >>> browser.getControl('Password').value = 'bigfïsh'
    >>> browser.getControl('Confirm password').value = 'bigfïsh'

    >>> browser.getControl('Register').click()
    >>> browser.contents
    '...Welcome!...You have been registered...'

    Ensure that the user has, in fact, been added.
    >>> browser.open('http://nohost/plone/login_form')
    >>> browser.getControl('Login Name').value = 'admin'
    >>> browser.getControl('Password').value = 'secret'
    >>> browser.getControl('Log in').click()
    >>> browser.open('http://nohost/plone/@@usergroup-userprefs')
    >>> 'user6pas' in browser.contents
    True


    >>> unset_mock_mailhost(portal)
