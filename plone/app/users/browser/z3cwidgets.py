from zope.interface import implementsOnly
from z3c.form import field
from z3c.form.interfaces import IWidgets


class EmptyPrefixFieldWidgets(field.FieldWidgets):
    """Override default Field Widgets to get rid of prefix"""
    implementsOnly(IWidgets)
    prefix = ''
