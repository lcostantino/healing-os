
"""Store context of the user/request."""

class Context(object):
    def __init__(self, user='admin', password=None,
                 token=None, project='admin',
                 user_id=None, roles=None, service_catalog=None, 
                 **kwargs):
        self.user = user
        self.password = password
        self.token = token
        self.user_id = user_id
        self.project = project
        self.roles = roles
        self.service_catalog = service_catalog

    def get_password_or_id(self):
        return self.user_id or self.password
    
    def to_dict(self):
        return {'user': self.user, 'token': self.token,
                'user_id': self.user_id,
                'project': self.project,
                'roles': self.roles,
                'service_catalog': self.service_catalog}
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)