import logging

import plone.app.users.browser.schemaeditor as ttw

logger = logging.getLogger('plone.app.users.setuphandlers')

FILE = 'userschema.xml'


def import_schema(context):
    """Import TTW Schema """
    data = context.readDataFile(FILE)
    if data is None:
        return
    model = ttw.load_ttw_schema(data)
    smodel = ttw.serialize_ttw_schema(model)

    # put imported field in user profile form by default
    ttw.set_schema(smodel)
    schema = ttw.get_ttw_edited_schema()
    for field_id in schema:
        schema[field_id].forms_selection = [u'In User Profile', ]
    new_model = ttw.serialize_ttw_schema(schema)
    ttw.applySchema(new_model)

    logger.info('Imported schema')


def export_schema(context):
    """Export TTW schema
    """
    schema = ttw.serialize_ttw_schema()
    logger.info('Exported schema')
    context.writeDataFile(FILE, schema, 'text/xml')
