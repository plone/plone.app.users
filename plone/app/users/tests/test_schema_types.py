# -*- coding: utf-8 -*-
from pkg_resources import resource_stream
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_PASSWORD
from plone.app.users.setuphandlers import import_schema
from plone.app.users.testing import PLONE_APP_USERS_FUNCTIONAL_TESTING
from plone.testing.z2 import Browser
from Products.GenericSetup.tests.common import DummyImportContext
from plone.app.users.tests.base import BaseTestCase

import transaction


class TestSchema(BaseTestCase):

    def setUp(self):
        super(TestSchema, self).setUp()
        xml = """<model xmlns:lingua="http://namespaces.plone.org/supermodel/lingua" xmlns:users="http://namespaces.plone.org/supermodel/users" xmlns:form="http://namespaces.plone.org/supermodel/form" xmlns:i18n="http://xml.zope.org/namespaces/i18n" xmlns:security="http://namespaces.plone.org/supermodel/security" xmlns:marshal="http://namespaces.plone.org/supermodel/marshal" xmlns="http://namespaces.plone.org/supermodel/schema" i18n:domain="plone">
  <schema name="member-fields">
    <field name="home_page" type="zope.schema.URI" users:forms="In User Profile">
      <description i18n:translate="help_homepage">
          The URL for your external home page, if you have one.
      </description>
      <required>False</required>
      <title i18n:translate="label_homepage">Home Page</title>
    </field>
    <field name="description" type="zope.schema.Text" users:forms="In User Profile">
      <description i18n:translate="help_biography">
          A short overview of who you are and what you do. Will be displayed
          on your author page, linked from the items you create.
      </description>
      <required>False</required>
      <title i18n:translate="label_biography">Biography</title>
    </field>
    <field name="location" type="zope.schema.TextLine" users:forms="In User Profile">
      <description i18n:translate="help_location">
          Your location - either city and country - or in
          a company setting, where your office is located.
      </description>
      <required>False</required>
      <title i18n:translate="label_biography">Location</title>
    </field>
    <field name="portrait" type="plone.namedfile.field.NamedBlobImage" users:forms="In User Profile">
      <description i18n:translate="help_portrait">
          To add or change the portrait: click the "Browse" button; select a
          picture of yourself. Recommended image size is 75 pixels wide by
          100 pixels tall.
      </description>
      <required>False</required>
      <title i18n:translate="label_portrait">Portrait</title>
    </field>
    <field name="birthdate" type="zope.schema.Date" users:forms="In User Profile">
      <description/>
      <required>False</required>
      <title>Birthdate</title>
    </field>
    <field name="another_date" type="zope.schema.Datetime" users:forms="In User Profile">
      <description/>
      <required>False</required>
      <title>Another date</title>
    </field>
    <field name="age" type="zope.schema.Int" users:forms="In User Profile">
      <description/>
      <required>False</required>
      <title>Age</title>
    </field>
    <field name="department" type="zope.schema.Choice" users:forms="In User Profile">
      <description/>
      <required>False</required>
      <title>Department</title>
      <values>
        <element>Marketing</element>
        <element>Production</element>
        <element>HR</element>
      </values>
    </field>
    <field name="skills" type="zope.schema.Set" users:forms="In User Profile">
      <description/>
      <required>False</required>
      <title>Skills</title>
      <value_type type="zope.schema.Choice">
        <values>
          <element>Programming</element>
          <element>Management</element>
        </values>
      </value_type>
    </field>
    <field name="pi" type="zope.schema.Float" users:forms="In User Profile">
      <description/>
      <required>False</required>
      <title>Pi</title>
    </field>
    <field name="vegetarian" type="zope.schema.Bool" users:forms="In User Profile">
      <description/>
      <required>False</required>
      <title>Vegetarian</title>
    </field>
  </schema>
</model>
"""
        context = DummyImportContext(self.portal, purge=False)
        context._files = {'userschema.xml': xml}
        import_schema(context)
        transaction.commit()

        self.browser = Browser(self.layer['app'])
        self.request = self.layer['request']

    def test_schema_types(self):
        self.browser.open('http://nohost/plone/')
        self.browser.getLink('Log in').click()
        self.browser.getControl('Login Name').value = TEST_USER_NAME
        self.browser.getControl('Password').value = TEST_USER_PASSWORD
        self.browser.getControl('Log in').click()
        self.browser.open("http://nohost/plone/@@personal-information")
        self.browser.getControl('Full Name').value = 'Isaac Newton'
        self.browser.getControl('Email').value = 'isaac@cambridge.com'
        self.browser.getControl('Home Page').value = 'http://gravity.org'
        self.browser.getControl('Biography').value = 'I like apples'
        self.browser.getControl('Location').value = 'Cambridge'
        portrait_file = resource_stream("plone.app.users.tests", 'onepixel.jpg')
        self.browser.getControl(name='form.widgets.portrait').add_file(portrait_file, "image/jpg", "onepixel.# jpg")
        self.browser.getControl('Age').value = '40'
        self.browser.getControl('Department').value = ['Marketing', ]
        self.browser.getControl('Skills').value = ['Programming', ]
        self.browser.getControl('Pi').value = '3.14'
        self.browser.getControl('Vegetarian').click()
        self.browser.getControl('Save').click()

        transaction.commit()
        membership = self.layer['portal'].portal_membership
        member = membership.getMemberById(TEST_USER_ID)
        self.assertTrue(isinstance(member.getProperty('fullname'), str))
        self.assertEqual(member.getProperty('fullname'), 'Isaac Newton')
        self.assertTrue(isinstance(member.getProperty('email'), str))
        self.assertEqual(member.getProperty('email'), 'isaac@cambridge.com')
        self.assertTrue(isinstance(member.getProperty('home_page'), str))
        self.assertEqual(member.getProperty('home_page'), 'http://gravity.org')
        self.assertTrue(isinstance(member.getProperty('description'), str))
        self.assertEqual(member.getProperty('description'), 'I like apples')
        self.assertTrue(isinstance(member.getProperty('location'), str))
        portrait = self.layer['portal'].portal_memberdata._getPortrait(TEST_USER_ID)
        self.assertEqual(portrait.content_type, 'image/jpeg')
        self.assertEqual(portrait.width, 1)
        self.assertEqual(portrait.height, 1)
        self.assertEqual(member.getProperty('location'), 'Cambridge')
        self.assertTrue(isinstance(member.getProperty('age'), int))
        self.assertEqual(member.getProperty('age'), 40)
        self.assertTrue(isinstance(member.getProperty('department'), str))
        self.assertEqual(member.getProperty('department'), 'Marketing')
        self.assertTrue(isinstance(member.getProperty('skills'), tuple))
        self.assertEqual(member.getProperty('skills'), ('Programming', ))
        self.assertTrue(isinstance(member.getProperty('pi'), float))
        self.assertEqual(member.getProperty('pi'), 3.14)
        self.assertTrue(isinstance(member.getProperty('vegetarian'), bool))
        self.assertEqual(member.getProperty('vegetarian'), True)
