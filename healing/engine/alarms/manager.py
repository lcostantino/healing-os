# You need to import new alarms here , so they register again the meta
# class
from healing.engine.alarms import alarm_base as ab
#DON't remove unused class
from healing.engine.alarms import ceilometer_alarms
from healing.openstack.common import log
from healing.objects import alarm_track as alarm_obj


LOG = log.getLogger(__name__)


def get_alarm_class_for_type(alarm_type):
    # hackish... odd.
    classname = ab.AlarmMetaClass.AVAILABLE_ALARMS.get(alarm_type)
    if not classname:
        raise Exception('Not class registered for alarm type %s' % alarm_type)
    return classname


def get_all_by_type(ctx, alarm_type, kwargs=None):
    cls = get_alarm_class_for_type(alarm_type)
    obj = alarm_obj.AlarmTrack.get_all_by_type(cls.ALARM_TYPE) or []
    return [cls(ctx=ctx, alarm_object=x, kwargs=kwargs) for x in obj]


def get_by_contract_id(ctx, contract_id, kwargs=None):
    obj = alarm_obj.AlarmTrack.get_by_contract_id(contract_id)
    cls = get_alarm_class_for_type(obj.type)
    return cls(ctx=ctx, alarm_object=obj, kwargs=kwargs)


def get_by_id(ctx, alarm_track_id, kwargs=None):
    obj = alarm_obj.AlarmTrack.get_by_id(alarm_track_id)
    cls = get_alarm_class_for_type(obj.type)
    return cls(ctx=ctx, alarm_object=obj, kwargs=kwargs)


def get_by_alarm_id(ctx, alarm_id, kwargs=None):
    obj = alarm_obj.AlarmTrack.get_by_alarm_id(alarm_id)
    cls = get_alarm_class_for_type(obj.type)
    return cls(ctx=ctx, alarm_object=obj, kwargs=kwargs)


def alarm_build_by_type(ctx, alarm_type, **kwargs):
    cls = get_alarm_class_for_type(alarm_type)
    return cls(ctx=ctx, **kwargs)
