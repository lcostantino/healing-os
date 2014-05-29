import abc
from healing.openstack.common import jsonutils
from healing import exceptions

class FormatterBase(object):
    """Format data based on source
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        pass

    @classmethod
    def get_formatter(cls, source):
        for subclass in cls.__subclasses__():
            if subclass.SOURCE == source:
                return subclass()
        raise exceptions.InvalidSourceException()

    #TOO: overwrite class to return customFormatter if source == custom
    @abc.abstractmethod
    def format(self, name, data, target_resource=None, headers=None):
        """start action for data."""


class CustomFormatter(FormatterBase):
    SOURCE = 'custom'

    def format(self, name, data, target_resource=None, headers=None):
        #expect target_resource in action_meta
        target_resource = target_resource or data.get('target_resource')
        if not target_resource:
            raise Exception('Missing mandatory data')

        action_data = {'name': name,
                       'source': self.SOURCE,
                       'target_resource': target_resource,
                        'action_meta': {'headers': {},
                                        'data': data}}
        return action_data

