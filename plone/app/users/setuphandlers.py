import logging

import plone.app.users.browser.schemaeditor as ttw

logger = logging.getLogger('plone.app.users.setuphandlers')

FILE = 'userschema.xml'


def import_schema(context):
    """Import TTW Schema """
    data = context.readDataFile(FILE)
    if data is None:
        return
    ttw.applySchema(data)

    logger.info('Imported schema')


def export_schema(context):
    """Export TTW schema
    """
    schema = ttw.serialize_ttw_schema()
    logger.info('Exported schema')
    context.writeDataFile(FILE, schema, 'text/xml')
