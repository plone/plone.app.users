import plone.app.users.browser.schemaeditor as ttw

import logging
log = logging.getLogger("plone.app.users:upgrade")


def upgrade_to_ttw(context):
    data = context.readDataFile('userschema.xml')
    model = ttw.load_ttw_schema(data)
    smodel = ttw.serialize_ttw_schema(model)
    ttw.set_schema(smodel)
    log.info('Imported schema')
