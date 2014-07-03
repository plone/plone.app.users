Introduction
============

This package provide the registration form for new users using z3c.form forms.
It allows the site administrator to select fields from a schema to appear on
the registration form.

Overriding / extending the default schema
=========================================

Thanks to FormExtenders, the form can be manipulated in many ways. The
following example is from `collective.examples.userdata`_, see there for more
information.

Overriding userdata form fields
-------------------------------

We can register a IFormExtender to add fields and modify the form. First
register it in the ZCML::

  <adapter
    factory="my.customschemachema.UserDataPanelExtender"
    provides="plone.z3cform.fieldsets.interfaces.IFormExtender" />

Where the `customschemachema.py` contains::

    from zope.publisher.interfaces.browser import IDefaultBrowserLayer
    from zope.component import adapter
    from zope.interface import Interface

    from z3c.form.field import Fields

    from plone.app.users.browser.userdatapanel import UserDataPanel
    from plone.supermodel import model
    from plone.z3cform.fieldsets import extensible


    class IEnhancedUserDataSchema(model.Schema):
        . . . all the custom fields to add . . .


    @adapter(Interface, IDefaultBrowserLayer, UserDataPanel)
    class UserDataPanelExtender(extensible.FormExtender):
        def update(self):
            fields = Fields(
                IEnhancedUserDataSchema,
                prefix="IEnhancedUserDataSchema")
            self.add(fields)

Storing / retreiving custom fields
----------------------------------

To store the values alongside default fields, we need to add fields to
``profiles/default/memberdata_properties.xml``. For example::

    <?xml version="1.0"?>
    <object name="portal_memberdata" meta_type="Plone Memberdata Tool">
      <property name="country" type="string"></property>
    </object>

Before values can be read and written, there needs to be a data manager to
fetch the values. The default manager will read/write any field defined in
the schema, so most of the work is done for you::

    from plone.app.users.browser.account import AccountPanelSchemaAdapter

    class EnhancedUserDataSchemaAdapter(AccountPanelSchemaAdapter):
        schema = IEnhancedUserDataSchema

If you want to do something different, add a property for that field to
override the default behavior.

Finally, register the data manager in ZCML::

    <adapter
      provides="my.customschemachema.IEnhancedUserDataSchema"
      for="plone.app.layout.navigation.interfaces.INavigationRoot"
      factory=".adapter.EnhancedUserDataSchemaAdapter"
      />

For more information, see `collective.examples.userdata`_.

.. _formlib: http://pypi.python.org/pypi/zope.formlib
.. _plone.app.controlpanel: http://pypi.python.org/pypi/plone.app.controlpanel
.. _`collective.examples.userdata`: http://pypi.python.org/pypi/collective.examples.userdata
