
"""Store context of the user/request."""

class Context(object):
    def __init__(self, user='admin', password=None,
                 token=None, project='admin',
                 user_id=None, roles=None, service_catalog=None):
        self.user = user
        self.password = password
        self.token = token
        self.user_id = user_id
        self.project = project
        self.roles = roles
        self.service_catalog = service_catalog

    def get_password_or_id(self):
        return self.user_id or self.password

