import abc
from healing.openstack.common import jsonutils
from healing import exceptions
from healing.handler_plugins.base import ActionData

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
        if data and not target_resource:
            target_resource = data.get('target_resource')

        if not target_resource:
            raise  exceptions.InvalidDataException('Missing target')

        return ActionData(name, source=self.SOURCE,
                          target_resource=target_resource,
                          data=data, headers={})


