from importlib.resources import files
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_PASSWORD
from plone.app.users.setuphandlers import import_schema
from plone.app.users.tests.base import BaseTestCase
from plone.testing.zope import Browser
from Products.GenericSetup.tests.common import DummyImportContext

import transaction


class TestSchema(BaseTestCase):
    def setUp(self):
        super().setUp()
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
        context._files = {"userschema.xml": xml}
        import_schema(context)
        transaction.commit()

        self.browser = Browser(self.layer["app"])
        self.browser.handleErrors = False
        self.request = self.layer["request"]

    def test_schema_types(self):
        self.browser.open("http://nohost/plone/")
        self.browser.getLink("Log in").click()
        self.browser.getControl("Login Name").value = TEST_USER_NAME
        self.browser.getControl("Password").value = TEST_USER_PASSWORD
        self.browser.getControl("Log in").click()
        self.browser.open("http://nohost/plone/@@personal-information")
        self.browser.getControl("Full Name").value = "Isaac Newton"
        self.browser.getControl("Email").value = "isaac@cambridge.com"
        self.browser.getControl("Home Page").value = "http://gravity.org"
        self.browser.getControl("Biography").value = "I like apples"
        self.browser.getControl("Location").value = "Cambridge"
        path = files("plone.app.users").joinpath("tests/onepixel.jpg")
        with open(path, "rb") as file_handle:
            portrait_file = file_handle.read()
        self.browser.getControl(name="form.widgets.portrait").add_file(
            portrait_file, "image/jpg", "onepixel.# jpg"
        )
        self.browser.getControl("Age").value = "40"
        self.browser.getControl("Department").value = [
            "Marketing",
        ]
        self.browser.getControl("Skills").value = [
            "Programming",
        ]
        self.browser.getControl("Pi").value = "3.14"
        self.browser.getControl("Vegetarian").click()
        self.browser.getControl("Save").click()

        transaction.commit()
        membership = self.layer["portal"].portal_membership
        member = membership.getMemberById(TEST_USER_ID)
        self.assertTrue(isinstance(member.getProperty("fullname"), str))
        self.assertEqual(member.getProperty("fullname"), "Isaac Newton")
        self.assertTrue(isinstance(member.getProperty("email"), str))
        self.assertEqual(member.getProperty("email"), "isaac@cambridge.com")
        self.assertTrue(isinstance(member.getProperty("home_page"), str))
        self.assertEqual(member.getProperty("home_page"), "http://gravity.org")
        self.assertTrue(isinstance(member.getProperty("description"), str))
        self.assertEqual(member.getProperty("description"), "I like apples")
        self.assertTrue(isinstance(member.getProperty("location"), str))
        portrait = self.layer["portal"].portal_memberdata._getPortrait(TEST_USER_ID)
        self.assertEqual(portrait.content_type, "image/jpeg")
        self.assertEqual(portrait.width, 1)
        self.assertEqual(portrait.height, 1)
        self.assertEqual(member.getProperty("location"), "Cambridge")
        self.assertTrue(isinstance(member.getProperty("age"), int))
        self.assertEqual(member.getProperty("age"), 40)
        self.assertTrue(isinstance(member.getProperty("department"), str))
        self.assertEqual(member.getProperty("department"), "Marketing")
        self.assertTrue(isinstance(member.getProperty("skills"), tuple))
        self.assertEqual(member.getProperty("skills"), ("Programming",))
        self.assertTrue(isinstance(member.getProperty("pi"), float))
        self.assertEqual(member.getProperty("pi"), 3.14)
        self.assertTrue(isinstance(member.getProperty("vegetarian"), bool))
        self.assertEqual(member.getProperty("vegetarian"), True)

    def test_regression_76_user_information(self):
        # Test that issue 76 does not return: user info sometimes appears empty.
        # https://github.com/plone/plone.app.users/issues/76
        # Here we test as admin.
        portal_url = self.portal.absolute_url()
        self.browser.open(portal_url)
        self.browser.getLink("Log in").click()
        self.browser.getControl("Login Name").value = SITE_OWNER_NAME
        self.browser.getControl("Password").value = SITE_OWNER_PASSWORD
        self.browser.getControl("Log in").click()

        # Set information for the test user.
        info_page = f"{portal_url}/@@user-information?userid={TEST_USER_ID}"
        self.browser.open(info_page)
        self.browser.getControl("Full Name").value = "Isaac Newton"
        self.browser.getControl("Email").value = "isaac@cambridge.com"
        self.browser.getControl("Age").value = "40"
        self.browser.getControl("Save").click()

        # Open the page again, check that the information is set.
        self.browser.open(info_page)
        self.assertEqual(self.browser.getControl("Full Name").value, "Isaac Newton")
        self.assertEqual(self.browser.getControl("Email").value, "isaac@cambridge.com")
        self.assertEqual(self.browser.getControl("Age").value, "40")

        # Opening the new-user/register page used to be enough to trigger the problem.
        self.browser.open(f"{portal_url}/@@new-user")

        # Any next calls to the user or personal information pages would show empty.
        self.browser.open(info_page)
        self.assertEqual(self.browser.getControl("Full Name").value, "Isaac Newton")
        self.assertEqual(self.browser.getControl("Email").value, "isaac@cambridge.com")
        self.assertEqual(self.browser.getControl("Age").value, "40")

    def _enable_self_registration(self):
        from plone.base.interfaces import ISecuritySchema
        from plone.registry.interfaces import IRegistry
        from zope.component import getUtility

        self.portal.manage_permission("Add portal member", roles=["Anonymous"])
        registry = getUtility(IRegistry)
        security_settings = registry.forInterface(ISecuritySchema, prefix="plone")
        security_settings.enable_user_pwd_choice = True
        transaction.commit()

    def test_regression_76_personal_information(self):
        # Test that issue 76 does not return: personal info sometimes appears empty.
        # https://github.com/plone/plone.app.users/issues/76
        # Here we test as user.
        portal_url = self.portal.absolute_url()
        self.browser.open(portal_url)
        self.browser.getLink("Log in").click()
        self.browser.getControl("Login Name").value = TEST_USER_NAME
        self.browser.getControl("Password").value = TEST_USER_PASSWORD
        self.browser.getControl("Log in").click()

        # Set information for the test user.
        info_page = f"{portal_url}/@@personal-information"
        self.browser.open(info_page)
        self.browser.getControl("Full Name").value = "Isaac Newton"
        self.browser.getControl("Email").value = "isaac@cambridge.com"
        self.browser.getControl("Age").value = "40"
        self.browser.getControl("Save").click()

        # Open the page again, check that the information is set.
        self.browser.open(info_page)
        self.assertEqual(self.browser.getControl("Full Name").value, "Isaac Newton")
        self.assertEqual(self.browser.getControl("Email").value, "isaac@cambridge.com")
        self.assertEqual(self.browser.getControl("Age").value, "40")

        # Enable self registration.
        self._enable_self_registration()

        # Opening the new-user/register page used to be enough to trigger the problem.
        # Logout, try it, and login again.
        self.browser.open(f"{portal_url}/@@logout")
        self.browser.open(f"{portal_url}/@@register")
        # Check that the registration page is loading correctly.
        self.assertNotIn(
            "This site doesn't have a valid email setup", self.browser.contents
        )
        self.assertIn("Enter your new password.", self.browser.contents)

        self.browser.open(f"{portal_url}/@@login")
        self.browser.getControl("Login Name").value = TEST_USER_NAME
        self.browser.getControl("Password").value = TEST_USER_PASSWORD
        self.browser.getControl("Log in").click()

        # Any next calls to the user or personal information pages would show empty.
        self.browser.open(info_page)
        self.assertEqual(self.browser.getControl("Full Name").value, "Isaac Newton")
        self.assertEqual(self.browser.getControl("Email").value, "isaac@cambridge.com")
        self.assertEqual(self.browser.getControl("Age").value, "40")
