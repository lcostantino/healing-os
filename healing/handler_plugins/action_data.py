
# moverlo
class ActionData(object):
    def __init__(self, name, target_resource, source='custom',
                 data=None, headers=None, internal_data=None,
                 request_id=None):
        """
        :name Plugin Name
        :target_resource The resource to operate on
        :source The data source. Set by converters
        :data Data for the plugin if required.
        :internal_data Used by the plugin to track internal things.
        :request_id an Id to associate a group of actins.
        :output The output of the operation.
        """
        self.name = name
        self.target_resource = target_resource
        self.source = source
        self.action_meta = {'headers': headers, 'data': data}
        self.internal_data = internal_data
        self.request_id = request_id
        self.output = None

    def __str__(self):
        return "ActionData {0}|{1}|{2}|{3}|{4}".format(self.name, self.source,
                                                   self.target_resource,
                                                   self.action_meta,
                                                   self.request_id)
