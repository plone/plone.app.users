Introduction
============

This package provides the registration form and the user profile form.
It allows the site administrator to define the fields those forms will display.

Overriding / extending the default schema
=========================================

Manipulating the user schema through the web
--------------------------------------------

In Plone setup / Users and Groups / Member fields, we can add and modify the user fields using the `plone.schemaeditor`_ interface.

Once a new field is added, we can access its settings, and more specifically, we can choose where the field must be shown (in the registration form, in the user profile form, or in both).

The entire schema can be freely modified, but:

- the Fullname and the Email fields cannot be removed nor changed,
- we can only add one Image field (that will be used as the user portrait), and no more.

Defining the user schema in a GenericSetup profile
--------------------------------------------------

The user schema can be defined in our GenericSetup profile in a file named ``userschema.xml``.

Its content must be compliant with the `plone.supermodel`_ format. Example::

    <model
      xmlns:lingua="http://namespaces.plone.org/supermodel/lingua"
      xmlns:users="http://namespaces.plone.org/supermodel/users"
      xmlns:form="http://namespaces.plone.org/supermodel/form"
      xmlns:i18n="http://xml.zope.org/namespaces/i18n"
      xmlns:security="http://namespaces.plone.org/supermodel/security"
      xmlns:marshal="http://namespaces.plone.org/supermodel/marshal"
      xmlns="http://namespaces.plone.org/supermodel/schema"
      i18n:domain="plone">
      <schema name="member-fields">
        <field name="birthdate" type="zope.schema.Date">
          <description/>
          <required>False</required>
          <title>Birthdate</title>
        </field>
        <field name="department" type="zope.schema.Choice">
          <description/>
          <required>False</required>
          <title>Department</title>
          <values>
            <element>Marketing</element>
            <element>Production</element>
            <element>HR</element>
          </values>
        </field>
      </schema>
    </model>

This file can imported or exported using ``portal_setup``.

Note: the ``userschema.xml`` importation will automatically refresh the memberdata attributes, so the ``memberdata_properties.xml`` file is not needed.

.. _plone.schemaeditor: https://github.com/plone/plone.schemaeditor
.. _plone.supermodel: https://github.com/plone/plone.supermodel
