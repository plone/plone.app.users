from Products.GenericSetup.tests.common import DummyImportContext
from Products.GenericSetup.tests.common import DummyExportContext
from plone.app.testing.bbb import PloneTestCase
from plone.app.users.schema import IUserDataSchemaProvider
from plone.app.users.setuphandlers import import_schema, export_schema
from plone.app.users.testing import PLONE_APP_USERS_FUNCTIONAL_TESTING
from zope.component import getUtility


class TestImport(PloneTestCase):

    layer = PLONE_APP_USERS_FUNCTIONAL_TESTING

    def afterSetUp(self):
        xml = """<model xmlns:i18n="http://xml.zope.org/namespaces/i18n" xmlns:security="http://namespaces.plone.org/supermodel/security" xmlns:users="http://namespaces.plone.org/supermodel/users" xmlns:form="http://namespaces.plone.org/supermodel/form" xmlns:marshal="http://namespaces.plone.org/supermodel/marshal" xmlns="http://namespaces.plone.org/supermodel/schema">
  <schema name="member-fields">
    <field name="office_name" type="zope.schema.TextLine" users:forms="On Registration|In User Profile">
      <description/>
      <title>Office name</title>
    </field>
  </schema>
</model>
"""
        context = DummyImportContext(self.portal, purge=False)
        context._files = {'userschema.xml': xml}
        import_schema(context)

    def test_import(self):
        schema = getUtility(IUserDataSchemaProvider).getSchema()
        self.assertIn("office_name", schema)

    def test_export(self):
        context = DummyExportContext(self.portal)
        export_schema(context)
        self.assertEqual('userschema.xml', context._wrote[0][0])
        self.assertIn('field name="office_name"', context._wrote[0][1])
