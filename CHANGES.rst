CHANGES
=======

2.3.6 (2016-05-12)
------------------

Fixes:

- Fixed KeyError email on personal preferences form.  This could
  happen when email is used as login name.  Fixes
  https://github.com/plone/plone.app.users/issues/56 and
  https://github.com/plone/Products.CMFPlone/issues/1146
  [maurits]

- Ensured partial searching utility for users in 'Search for users' page
  Fixes https://github.com/plone/Products.CMFPlone/issues/1499
  [kkhan]

- Use ProtectedEmail for Email field factory
  [ebrehault]


2.3.5 (2016-02-11)
------------------

Fixes:

- Fix bug when registering a user by adding a schema-setter to
  UserDataPanelAdapter.
  [pbauer]


2.3.4 (2015-11-28)
------------------

Fixes:

- Rerelease to fix problem on one of our testing servers.
  [maurits]


2.3.3 (2015-11-28)
------------------

Fixes:

- Updated Site Setup link in all control panels.
  Fixes https://github.com/plone/Products.CMFPlone/issues/1255
  [davilima6]


2.3.2 (2015-10-28)
------------------

Fixes:

- Do not force "In User Profile" when importing a schema from a GS profile.
  [ebrehault]


2.3.1 (2015-08-22)
------------------

- Gave upgrade step destination 1. With the previous destination '*'
  the upgrade step was always offered.
  [vanrees]

- Cache schemas in volatile attributes on portal.
  [gotcha]

- Package cleanup.
  [gotcha]

- Disable toolbar buttons on personal preferences
  [vangheem]

- Remove extra spaces in userschema.xml messages to avoid i18n extraction
  warnings.
  [vincentfretin]


2.3 (2015-07-18)
----------------

- Implement ttw editable schemas
  [ebrehault, kiorky]

- Added upgrade step to move past Plone to user editable member schema.
  [ianderso]

- Split personal information schema into required and ttw editable schemas
  [ianderso, ljb, stevem]

- Updated tests to reflect current status of the product.
  [stevem]

- Added ttw editable schema for personal information.
  [ianderso, ljb, stevem]

- Removed ext_editor and visible_ids preferences.
  [davisagli]

- Made save buttons "blue"
  [agitator]


2.2.2 (2015-06-05)
------------------

- Import ConfigurationChangedEvent from Products.CMFPlone instead of from
  plone.app.controlpanel (which will be removed in Plone 5).
  [timo]

- Fixed "Add new user" form when there are too many groups.
  Fixes https://github.com/plone/plone.app.users/issues/33
  [avoinea]


2.2.1 (2015-05-04)
------------------

- Removed CMFDefault dependency
  [tomgross]
- Fixed @@change-password to accept current password containing non-ascii chars
  [sgeulette]
- Fixed @@change-password to accept new password containing non-ascii chars
  [sgeulette]


2.2 (2015-03-13)
----------------

- Read security settings from new Plone 5 registry.
  [jure]

- Ported tests to plone.app.testing
  [gforcada, tomgross]

- Adjust navigation markup for Plone 5.
  [davisagli]

- Use email_from_address from registry (Plone 5) in tests.
  [khink]


2.1.0 (2014-10-23)
------------------

- Check the permission for the Object tab on the AccountPanelForm as configured
  in ZCML. This allows to revoke access to individual forms by changing the
  permissions via ZCML overrides.
  [thet]


2.0.3 (2014-04-19)
------------------

- Use correct timezone vocabulary in IPersonalPreferences schema. Wether
  the newer plone.app.vocabularies, the older plone.app.event one or none at
  all, depending on availability.
  [thet]


2.0.2 (2014-04-01)
------------------

- More explicit ZCML package includes. At least, the inclusion of
  plone.formwidget.namedfile fixes a problem in Dexterity-less setups, where
  the @@personal-information form couldn't be rendered because NamedBlobImage
  didn't provide IFromUnicode.
  [thet]


2.0.1 (2014-03-02)
------------------

- Fix packaging error.
  [esteele]


2.0 (2014-03-02)
----------------

- Refactor the member-search form to a browser view, using z3c.form.
  [pabo3000]

- Have a soft dependency on plone.app.event and include the timezone field only
  then in the schema, if plone.app.event is available.
  [thet]

- Migrate plone.app.users to use z3c.form instead of zope.formlib.
  [lentinj, vipod, thet]


1.3a1 (unreleased)
------------------

- Query ``ILoginNameGenerator`` utility to get a login name during registration.
  This makes it easier to override the default login name logic.
  Part of PLIP 13419.
  [maurits]

- Query ``IUserIdGenerator`` utility to get a user id during registration.
  This makes it easier to override the default user id logic.
  Part of PLIP 13419.
  [maurits]

- Support ``use_uuid_as_userid`` site property.
  Part of PLIP 13419.
  [maurits]


1.2a2 (unreleased)
------------------

- Update tests. We now check if the user can add and delete the portrait
  himself.
  [tschanzt]

- Added user timezone selection to user preferences and a dependency on
  plone.app.event for vocabulary for user timezone selection.
  [seanupton]

- Fixed i18n of new_password field in change-password view.
  [vincentfretin]

- Fix email as login validation in the personalize form (UserDataPanel).
  This is for the case when email is used as login.  It checked that a
  changed email address was valid as user id.  But the user id is
  never changed here, only the login name.  We only need to check if
  this address is not used by another user.
  [maurits]

- Fix to not break if passwords contain non-ASCII characters.
  This closes https://dev.plone.org/ticket/13114
  [davisagli]

- Ensure links on user preference panes adhere to navigation root.
  Fixes https://dev.plone.org/ticket/11909.
  [davidjb]

- Unused field "Listed in searches" removed from Personal Preferences.
  [kleist]

- Be consistent in using INavigationRoot. (Backport from 1.1.4)
  [do3cc]


1.2a1 (2012-06-29)
------------------

- Avoid direct zope.app.form dependency.
  [hannosch]

- Support redirecting to a URL specified in the 'came_from' query string
  parameter following registration.
  [davisagli]

- support a PAS plugin for validating passwords see http://dev.plone.org/ticket/10959

1.1.3 (2012-01-04)
------------------

- Setting a member data field to an empty string now works.
  Fixes http://dev.plone.org/ticket/12314
  [maurits]

- Fix for: Plone Administrator unable to edit User Data when email is
  used as login.  Fixes http://dev.plone.org/plone/ticket/12297
  [vmaksymiv, myroslav]

- Explicitly set the mail_me field as not required.
  [jcbrand]


1.1.2 (2011-08-23)
------------------

- Make sure that users with the Site Administrator role can add new users to
  groups. Fixes http://dev.plone.org/plone/ticket/11888
  [davisagli]


1.1.1 - 2011-06-02
------------------

- Check for permission when editing other users' profiles.
  This fixes http://dev.plone.org/plone/ticket/11842 and
  http://plone.org/products/plone/security/advisories/CVE-2011-1950
  [fRiSi, davisagli]

- Add MANIFEST.in
  [WouterVH]


1.1 - 2011-04-03
----------------

- Include plone.app.controlpanel configure.zcml because we use permissions
  defined in this package.
  [vincentfretin]

- Use portal object instead of self.context in AddUserForm so we can easily
  subclass the class for another context.
  [vincentfretin]


1.1b2 - 2011-03-02
------------------

- Fixed test of the default user portrait, which changed from
  defaultUser.gif to defaultUser.png in Products.PlonePAS 4.0.5.
  [maurits]


1.1b1 - 2011-01-03
------------------

- Depend on ``Products.CMFPlone`` instead of ``Plone``.
  [elro]

- Don't allow non-Managers to add new users to groups that grant the Manager
  role.
  [davisagli]

- Protect the user management forms with the
  "Plone Site Setup: Users and Groups" permission instead of the generic
  "Manage portal" and "Manage users".  This requires
  plone.app.controlpanel >= 2.1b1.
  [davisagli]

1.0.5 - 2011-06-02
------------------

- Check for permission when editing other users' profiles.
  This fixes http://dev.plone.org/plone/ticket/11842 and
  http://plone.org/products/plone/security/advisories/CVE-2011-1950
  [fRiSi, davisagli]


1.0.4 - 2011-02-25
------------------

- Fixed test of the default user portrait, which changed from defaultUser.gif to
  defaultUser.png in Products.PlonePAS 4.0.5.
  [maurits]


1.0.3 - 2011-01-03
------------------

- Don't assume that fields in the user schema will be saved in property sheets
  when a new user registers. Instead, adapt the navigation root to the user
  schema to get the same adapter as is used on the Personal Information form,
  and use it to save the values from the registration form.
  [davisagli]

- Fixed critical error on add user page
  when some groups have a non-ascii character in their title.
  Sort groups on their title normalized.
  Token and value in terms in the groups vocabulary were switched.
  This closes http://dev.plone.org/plone/ticket/11316
  [thomasdesvenain, vincentfretin, davisagli]


1.0.2 - 2010-11-24
------------------

- Don't use a custom widget just to set the description of the fullname field,
  which should be set on the field itself.
  [davisagli]


1.0.1 - 2010-07-18
------------------

- Added missing i18n:domain plone in user information template which prevented
  some translations from showing up.
  Fixes http://dev.plone.org/plone/ticket/10744
  [maurits]

- Update license to GPL version 2 only.
  [hannosch]

- Fix @@user-information to correctly get/set and delete the portrait for the
  given userid. Fixes http://dev.plone.org/plone/ticket/10731.
  [mr_savage]


1.0 - 2010-07-01
----------------

- Internationalized personal preferences form.
  Fixes http://dev.plone.org/plone/ticket/10619
  [thomasdesvenain]


1.0b9 - 2010-06-13
------------------

- Avoid deprecation warnings under Zope 2.13.
  [hannosch]

- Use the standard libraries doctest module.
  [hannosch]

- Use five.formlib.
  [hannosch]

- Retrieve properties as unicode even if they are already stored that way.
  Fixes http://dev.plone.org/plone/ticket/10509
  [davisagli]

- When the user_registration_fields property is not there, fall back
  to an empty list; this avoids a TypeError on the registration form.
  [maurits]


1.0b8 - 2010-06-03
------------------

- Fixed error when editing your personal information when using the
  email address as login.
  Fixes http://dev.plone.org/plone/ticket/10363
  [Maurits]

- Fix issue where an e-mail was sent on registration even when told not to.
  Fixes http://dev.plone.org/plone/ticket/10330
  [davisagli]


1.0b7 - 2010-05-01
------------------

- Handle encoded strings returned by PlonePAS.
  Fixes http://dev.plone.org/plone/ticket/10447
  [esteele]

- Remove unused memberdetails.py
  [esteele]

- Pin user preferences forms to INavigationRoot instead of ISiteRoot.
  Fixes http://dev.plone.org/plone/ticket/10439
  [esteele]

- Added configlet forms that inherit from personal preferences and
  personal information. These forms are used when editing user prefs
  from 'User and groups' in site setup.
  [kcleong]

- Use utility-provided UserDataSchema on @@personal-information form.
  Fixes http://dev.plone.org/plone/ticket/10258
  [khink, huub_bouma]


1.0b6 - 2010-04-07
------------------

- Update permission for the @@register view so only users with the
  ``Add Portal Member`` permission can use it to add new members.
  Update tests accordingly.
  Fixes http://dev.plone.org/plone/ticket/3739
  [dukebody]

- Fixed help_biography message.
  [vincentfretin]


1.0b5 - 2010-03-05
------------------

- Remove some unused variable definitions from browser/register.py.
  [esteele]

- Updated account-panel-bare.pt to recent markup conventions.
  References http://dev.plone.org/plone/ticket/9981
  [spliter]

- Sort groups listing alphabetically by title.
  [esteele]

- Display groups by title (id) in @@new-user.
  [esteele]

- Fix some more duplicate id's, including some done through TAL that had nothing
  dynamic and so nee not be tal:attributes.
  [rossp]


1.0b4 - 2010-02-18
------------------

- Updated memberregistration.pt to recent markup conventions.
  References http://dev.plone.org/old/plone/ticket/9981
  [spliter]

- Fixed @@register by removing unnecessary fill-slot outside of a fill-macro.
  [spliter]

- Removing redundant .documentContent markup.
  This refs http://dev.plone.org/plone/ticket/10231.
  [limi]

- Updated register_form.pt to not use fill-slot="viewlet".
  [spliter]

- Updated user registration templates to disable the columns with
  'disable_MANAGER_NAME' pattern
  [spliter]

- add views to replace personalize_form, split up into @@personal-preferences,
  @@personal-information and @@change-password.
  [khink, kcleong]


1.0b3 - 2010-02-01
------------------

- Retarget the registration and new-user forms at the navigation root.
  [mj]


1.0b2 - 2010-01-28
------------------

- Fixed tests to account for new layout of users overview pages.
  [esteele]


1.0b1 - 2009-12-27
------------------

- Fixed package dependency declarations and use getSite from zope.site.
  [hannosch]


1.0a3 - 2009-12-16
------------------

- Make the password field optional for the admin when instead an email can be sent.
  [maurits]

- On the anonymous registration form, do not offer to send an email with a link
  to reset your password if the password fields are right there on the form
  already; we were never actually sending emails with the plain password itself anyway.
  [maurits]

- Allow admins to register a user at all times, also without valid mailhost
  settings.  This means that in a fresh Plone site you can create user accounts
  immediately without having to edit any settings.
  [maurits]

- Use the proper SimpleVocabulary/SimpleTerm API instead of encouraging bad
  practice. This refs http://dev.plone.org/plone/ticket/6480.
  [hannosch]


1.0a2 - 2009-12-01
------------------

- Display a message and prevent the user from registering if there is no
  defined mailhost and users are not allowed to select their own passwords.
  [esteele]

- "User/Groups Settings" configlet view is polished visually to follow rest of
  configlets in "Users and Groups" control panel. Ref. #9825
  [spliter]

- For "User/Groups Settings" configlet highlighted "Member registration" tab
  instead of the wrong "Settings"
  [spliter]

- @@new-user form will now always show the password fields, regardless of the
  site settings.
  [esteele]

- Change registration form name @@join_form to @@register. Change class names
  accordingly. Added an "@@new-user" form to be used from the control panel.
  "Add to group" functionality now lives there. We can now get rid of the
  horrid came_from flags that we've been passing around.
  [esteele]

- Internationalized title_join_form_fields and description_join_form_fields.
  This closes http://dev.plone.org/plone/attachment/ticket/9810
  [vincentfretin]


1.0a1 - 2009-11-18
------------------

- Fixed bad use of i18n markup in joinform.py. This closes
  http://dev.plone.org/plone/ticket/9773
  [vincentfretin]

- Renamed label_groups to label_add_to_groups in joinform.py
  [vincentfretin]

- Restore the came_from_prefs check to make the join form redirect to the
  Users and Groups configlet if that's where the user started from.
  [davisagli]

- Initial release
