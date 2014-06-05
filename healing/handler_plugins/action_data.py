
# moverlo
class ActionData(object):
    def __init__(self, name, target_resource, source='custom',
                 data=None, headers=None, internal_data=None,
                 request_id=None):
        self.name = name
        self.target_resource = target_resource
        self.source = source
        self.action_meta = {'headers': headers, 'data': data}
        self.internal_data = internal_data
        self.request_id = request_id
        
    def __str__(self):
        return "ActionData {0}|{1}|{2}|{3}|{4}".format(self.name, self.source,
                                                   self.target_resource,
                                                   self.action_meta,
                                                   self.request_id)
