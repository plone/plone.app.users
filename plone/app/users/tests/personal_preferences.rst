Testing the personal preferences form
=====================================

    >>> empty_marker = '--NOVALUE--'
    >>> def isEmptyMarker(v):
    ...     if len(v) != 1: return False
    ...     return v[0] == empty_marker

Viewing the personal preferences
--------------------------------

This is about the 'personal-preferences' view.

    >>> view_name = '@@personal-preferences'

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

We have two controls, one for the start page and one for the language:

    >>> isEmptyMarker(self.browser.getControl('Wysiwyg editor').value)
    True
    >>> self.browser.getControl('Enable external editing').selected
    False
    >>> isEmptyMarker(self.browser.getControl('Language', index=0).value)
    True

The form should be using CSRF protection:

    >>> self.browser.getControl(name='_authenticator', index=0)
    <Control name='_authenticator' type='hidden'>

Now we click the cancel button:

    >>> self.browser.getControl('Cancel').click()
    >>> self.browser.url.endswith(view_name)
    True

There should be no changes at all:

    >>> 'Changes canceled.' in self.browser.contents
    True

Modifying values
----------------

    >>> self.browser.open('http://nohost/plone/' + view_name)
    >>> self.browser.getControl('Wysiwyg editor').value = ['TinyMCE']
    >>> self.browser.getControl('Enable external editing').selected = True
    >>> self.browser.getControl('Language', index=0).value = ['en']
    >>> self.browser.getControl('Save').click()
    >>> 'Changes saved' in self.browser.contents
    True

Verify that the settings have actually been
changed:

    >>> member = self.membership.getMemberById('test_user_1_')
    >>> marker = object
    >>> member.getProperty('wysiwyg_editor', object)
    'TinyMCE'
    >>> member.getProperty('ext_editor', object)
    True
    >>> member.getProperty('language', object)
    'en'

And that the form still has the according values:

    >>> isEmptyMarker(self.browser.getControl('Wysiwyg editor').value)
    False
    >>> self.browser.getControl('Wysiwyg editor').value
    ['TinyMCE']
    >>> self.browser.getControl('Enable external editing').selected
    True
    >>> self.browser.getControl('Language', index=0).value
    ['en']


Clearing values
---------------

Making an input empty should result in a stored empty string.

    >>> self.browser.open('http://nohost/plone/' + view_name)
    >>> self.browser.getControl('Wysiwyg editor').value = [empty_marker]
    >>> self.browser.getControl('Enable external editing').selected = False
    >>> self.browser.getControl('Language', index=0).value = [empty_marker]
    >>> self.browser.getControl('Save').click()
    >>> 'Changes saved' in self.browser.contents
    True

Verify that the settings have actually been
changed:

    >>> member = self.membership.getMemberById('test_user_1_')
    >>> marker = object
    >>> member.getProperty('wysiwyg_editor', object)
    ''
    >>> member.getProperty('ext_editor', object)
    False
    >>> member.getProperty('language', object)
    ''

And that the form still has the according values:

    >>> isEmptyMarker(self.browser.getControl('Wysiwyg editor').value)
    True
    >>> self.browser.getControl('Enable external editing').selected
    False
    >>> isEmptyMarker(self.browser.getControl('Language', index=0).value)
    True
