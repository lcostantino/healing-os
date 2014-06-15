import abc
from healing.openstack.common import jsonutils
from healing import exceptions
from healing.objects import action

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
        #expect source in action_meta
        if data and not target_resource:
            target_resource = data.get('target_resource')

        if not target_resource:
            raise  exceptions.InvalidDataException('Missing target')

        return action.Action.from_data(name, 
                                      target_resource=target_resource,
                                      data=data, headers={})



class CeilometerFormatter(CustomFormatter):
    """ We expect ceilmeter to send target_resource if calling
        handlers without SLA component.
        We could get the resource from ceilometer also based on
        alarm_id in the future
    """
    SOURCE = 'ceilometer'
