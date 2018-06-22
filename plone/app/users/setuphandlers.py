# -*- coding: utf-8 -*-
from Products.CMFPlone.utils import safe_encode

import logging
import plone.app.users.browser.schemaeditor as ttw
import six

logger = logging.getLogger('plone.app.users.setuphandlers')

FILE = 'userschema.xml'


def import_schema(context):
    """Import TTW Schema
    """
    data = context.readDataFile(FILE)
    if data is None:
        return
    if six.PY3 and isinstance(data, bytes):
        data = data.decode('utf-8')
    ttw.applySchema(data)
    logger.info('Imported schema')


def export_schema(context):
    """Export TTW schema
    """
    schema = ttw.serialize_ttw_schema()
    context.writeDataFile(FILE, safe_encode(schema), 'text/xml')
    logger.info('Exported schema')
