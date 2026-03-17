Extract ``generate_user_id`` and ``generate_login_name`` as standalone functions
in ``plone.app.users.utils``, enabling reuse from ``plone.api`` and ``plone.restapi``
without form view dependency.
