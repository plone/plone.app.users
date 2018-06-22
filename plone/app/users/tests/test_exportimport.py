# -*- coding: utf-8 -*-
from plone.app.users.browser.userdatapanel import getUserDataSchema
from plone.app.users.setuphandlers import export_schema
from plone.app.users.setuphandlers import import_schema
from plone.app.users.testing import PLONE_APP_USERS_FUNCTIONAL_TESTING
from plone.app.users.tests.base import BaseTestCase
from plone.namedfile.field import NamedBlobImage
from Products.CMFCore.utils import getToolByName
from Products.GenericSetup.tests.common import DummyExportContext
from Products.GenericSetup.tests.common import DummyImportContext
from zope import schema


class TestImport(BaseTestCase):

    def setUp(self):
        super(TestImport, self).setUp()
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

    def test_import(self):
        user_schema = getUserDataSchema()
        pm = getToolByName(self.portal, "portal_memberdata")
        member_properties = pm.propertyIds()

        self.assertIn("home_page", user_schema)
        self.assertTrue(isinstance(user_schema['home_page'], schema.URI))
        self.assertIn("home_page", member_properties)
        self.assertEqual(pm.getPropertyType('home_page'), 'text')

        self.assertIn("description", user_schema)
        self.assertTrue(isinstance(user_schema['description'], schema.Text))
        self.assertIn("description", member_properties)
        self.assertEqual(pm.getPropertyType('description'), 'text')

        self.assertIn("location", user_schema)
        self.assertTrue(isinstance(user_schema['location'], schema.TextLine))
        self.assertIn("location", member_properties)
        self.assertEqual(pm.getPropertyType('location'), 'string')

        self.assertIn("portrait", user_schema)
        self.assertTrue(isinstance(user_schema['portrait'], NamedBlobImage))
        # image fields are not handled as memberdata property,
        # it is handled directly in portal_membership
        self.assertNotIn("portrait", member_properties)

        self.assertIn("birthdate", user_schema)
        self.assertTrue(isinstance(user_schema['birthdate'], schema.Date))
        self.assertIn("birthdate", member_properties)
        self.assertEqual(pm.getPropertyType('birthdate'), 'date')

        self.assertIn("another_date", user_schema)
        self.assertTrue(isinstance(user_schema['another_date'], schema.Datetime))
        self.assertIn("another_date", member_properties)
        self.assertEqual(pm.getPropertyType('another_date'), 'date')

        self.assertIn("age", user_schema)
        self.assertTrue(isinstance(user_schema['age'], schema.Int))
        self.assertIn("age", member_properties)
        self.assertEqual(pm.getPropertyType('age'), 'int')

        self.assertIn("department", user_schema)
        self.assertTrue(isinstance(user_schema['department'], schema.Choice))
        self.assertIn("department", member_properties)
        self.assertEqual(pm.getPropertyType('department'), 'string')

        self.assertIn("skills", user_schema)
        self.assertTrue(isinstance(user_schema['skills'], schema.Set))
        self.assertIn("skills", member_properties)
        self.assertEqual(pm.getPropertyType('skills'), 'lines')

        self.assertIn("pi", user_schema)
        self.assertTrue(isinstance(user_schema['pi'], schema.Float))
        self.assertIn("pi", member_properties)
        self.assertEqual(pm.getPropertyType('pi'), 'float')

        self.assertIn("vegetarian", user_schema)
        self.assertTrue(isinstance(user_schema['vegetarian'], schema.Bool))
        self.assertIn("vegetarian", member_properties)
        self.assertEqual(pm.getPropertyType('vegetarian'), 'boolean')

    def test_export(self):
        context = DummyExportContext(self.portal)
        export_schema(context)
        self.assertEqual('userschema.xml', context._wrote[0][0])
        self.assertIn(b'field name="home_page"', context._wrote[0][1])
        self.assertIn(b'field name="description"', context._wrote[0][1])
        self.assertIn(b'field name="location"', context._wrote[0][1])
        self.assertIn(b'field name="portrait"', context._wrote[0][1])
        self.assertIn(b'field name="birthdate"', context._wrote[0][1])
        self.assertIn(b'field name="another_date"', context._wrote[0][1])
        self.assertIn(b'field name="age"', context._wrote[0][1])
        self.assertIn(b'field name="department"', context._wrote[0][1])
        self.assertIn(b'field name="skills"', context._wrote[0][1])
        self.assertIn(b'field name="pi"', context._wrote[0][1])
        self.assertIn(b'field name="vegetarian"', context._wrote[0][1])
