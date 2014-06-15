"""
prepare in the future for real object<>rpc/db versioning
Note: This is a clone of Nova Objects

"""
#TODO: check if we need to add context with session to avoid creating new ones

import abc
import collections
import copy
import datetime
import six

from oslo import messaging

from healing import objects
from healing.objects import fields
from healing.openstack.common import log as logging
from healing.openstack.common import versionutils
from healing.openstack.common.gettextutils import _

LOG = logging.getLogger(__name__)

class NotSpecifiedSentinel:
    pass

def get_attrname(name):
    """Return the mangled name of the attribute's underlying storage."""
    return '_%s' % name


def make_class_properties(cls):
    # NOTE(danms/comstud): Inherit fields from super classes.
    # mro() returns the current class first and returns 'object' last, so
    # those can be skipped.  Also be careful to not overwrite any fields
    # that already exist.  And make sure each cls has its own copy of
    # fields and that it is not sharing the dict with a super class.
    cls.fields = dict(cls.fields)
    for supercls in cls.mro()[1:-1]:
        if not hasattr(supercls, 'fields'):
            continue
        for name, field in supercls.fields.items():
            if name not in cls.fields:
                cls.fields[name] = field
    for name, field in cls.fields.iteritems():
        if not isinstance(field, fields.Field):
            raise exception.ObjectFieldInvalid(
                field=name, objname=cls.obj_name())

        def getter(self, name=name):
            attrname = get_attrname(name)
            if not hasattr(self, attrname):
                self.obj_load_attr(name)
            return getattr(self, attrname)

        def setter(self, value, name=name, field=field):
            self._changed_fields.add(name)
            try:
                return setattr(self, get_attrname(name),
                               field.coerce(self, name, value))
            except Exception:
                attr = "%s.%s" % (self.obj_name(), name)
                LOG.exception(_('Error setting %(attr)s') %
                              {'attr': attr})
                raise

        setattr(cls, name, property(getter, setter))


class HealingObjectMetaclass(type):
    """Metaclass that allows tracking of object classes."""

    def __init__(cls, names, bases, dict_):
        if not hasattr(cls, '_obj_classes'):
            # This means this is a base class using the metaclass. I.e.,
            # the 'NovaObject' class.
            cls._obj_classes = collections.defaultdict(list)
            return

        def _vers_tuple(obj):
            return tuple([int(x) for x in obj.VERSION.split(".")])

        # Add the subclass to NovaObject._obj_classes. If the
        # same version already exists, replace it. Otherwise,
        # keep the list with newest version first.
        make_class_properties(cls)
        obj_name = cls.obj_name()
        for i, obj in enumerate(cls._obj_classes[obj_name]):
            if cls.VERSION == obj.VERSION:
                cls._obj_classes[obj_name][i] = cls
                # Update nova.objects with this newer class.
                setattr(objects, obj_name, cls)
                break
            if _vers_tuple(cls) > _vers_tuple(obj):
                # Insert before.
                cls._obj_classes[obj_name].insert(i, cls)
                if i == 0:
                    # Later version than we've seen before. Update
                    # nova.objects.
                    setattr(objects, obj_name, cls)
                break
        else:
            cls._obj_classes[obj_name].append(cls)
            # Either this is the first time we've seen the object or it's
            # an older version than anything we'e seen. Update healing.objects
            # only if it's the first time we've seen this object name.
            if not hasattr(objects, obj_name):
                setattr(objects, obj_name, cls)


@six.add_metaclass(HealingObjectMetaclass)
class HealingObject(object):
    fields = {}
    obj_extra_fields = []

    def __init__(self, context=None, **kwargs):
   	self._changed_fields = set()
        self._context = context
        for key in kwargs.keys():
            self[key] = kwargs[key]
        
    @classmethod
    def obj_name(cls):
        """Return a canonical name for this object which will be used over
        the wire for remote hydration.
        """
        return cls.__name__

    @classmethod
    def obj_class_from_name(cls, objname, objver):
        """Returns a class from the registry based on a name and version."""
        if objname not in cls._obj_classes:
            LOG.error(_('Unable to instantiate unregistered object type '
                        '%(objtype)s') % dict(objtype=objname))
            raise exceptions.UnsupportedObjectError(objtype=objname)

        # NOTE(comstud): If there's not an exact match, return the highest
        # compatible version. The objects stored in the class are sorted
        # such that highest version is first, so only set compatible_match
        # once below.
        compatible_match = None

        for objclass in cls._obj_classes[objname]:
            if objclass.VERSION == objver:
                return objclass
            if (not compatible_match and
                    versionutils.is_compatible(objver, objclass.VERSION)):
                compatible_match = objclass

        if compatible_match:
            return compatible_match

        # As mentioned above, latest version is always first in the list.
        latest_ver = cls._obj_classes[objname][0].VERSION
        raise exceptions.IncompatibleObjectVersion(objname=objname,
                                                   objver=objver,
                                                   supported=latest_ver)


    def obj_clone(self):
        return copy.deepcopy(self)

    def create(self):
        raise NotImplementedError('Cannot create anything in the base class')


    def save(self):
        raise NotImplementedError('Cannot save anything in the base class')

    def obj_what_changed(self):
        """Returns a set of fields that have been modified."""
        changes = set(self._changed_fields)
        for field in self.fields:
            if (self.obj_attr_is_set(field) and
                    isinstance(self[field], HealingObject) and
                    self[field].obj_what_changed()):
                changes.add(field)
        return changes

    def obj_get_changes(self):
        """Returns a dict of changed fields and their new values."""
        changes = {}
        for key in self.obj_what_changed():
            changes[key] = self[key]
        return changes

    def obj_reset_changes(self, fields=None):
        """Reset the list of fields that have been changed.

        Note that this is NOT "revert to previous values"
        """
        if fields:
            self._changed_fields -= set(fields)
        else:
            self._changed_fields.clear()

    def obj_attr_is_set(self, attrname):
        """Test object to see if attrname is present.

        Returns True if the named attribute has a value set, or
        False if not. Raises AttributeError if attrname is not
        a valid attribute for this object.
        """
        if attrname not in self.obj_fields:
            raise AttributeError(
                _("%(objname)s object has no attribute '%(attrname)s'") %
                {'objname': self.obj_name(), 'attrname': attrname})
        return hasattr(self, get_attrname(attrname))
    
    def obj_load_attr(self, attrname):
        """Load an additional attribute from the real object.
        This should use self._conductor, and cache any data that might
        be useful for future load operations.
        """
        raise NotImplementedError(_("Cannot load '%s' in the base class") % attrname)

    @property
    def obj_fields(self):
        return self.fields.keys() + self.obj_extra_fields

    def __getitem__(self, name):
        """For backwards-compatibility with dict-based objects.

        NOTE(danms): May be removed in the future.
        """
        return getattr(self, name)

    def __setitem__(self, name, value):
        """For backwards-compatibility with dict-based objects.

        NOTE(danms): May be removed in the future.
        """
        setattr(self, name, value)

    def __contains__(self, name):
        """For backwards-compatibility with dict-based objects.

        NOTE(danms): May be removed in the future.
        """
        try:
            return self.obj_attr_is_set(name)
        except AttributeError:
            return False

    def get(self, key, value=NotSpecifiedSentinel):
        """For backwards-compatibility with dict-based objects.

        NOTE(danms): May be removed in the future.
        """
        if key not in self.obj_fields:
            raise AttributeError("'%s' object has no attribute '%s'" % (
                    self.__class__, key))
        if value != NotSpecifiedSentinel and not self.obj_attr_is_set(key):
            return value
        else:
            return self[key]

    def update(self, updates):
        """For backwards-compatibility with dict-base objects.

        NOTE(danms): May be removed in the future.
        """
        for key, value in updates.items():
            self[key] = value

    def to_dict(self):
        ret = {}
        for x in self.fields.keys():
            ret[x] = getattr(self, x, None)
        return ret

    def obj_make_compatible(self, primitive, target_version):
        """Make an object representation compatible with a target version.

        This is responsible for taking the primitive representation of
        an object and making it suitable for the given target_version.
        This may mean converting the format of object attributes, removing
        attributes that have been added since the target version, etc.

        :param:primitive: The result of self.obj_to_primitive()
        :param:target_version: The version string requested by the recipient
                               of the object.
        :param:raises: nova.exception.UnsupportedObjectError if conversion
                       is not possible for some reason.
        """
        pass

    def obj_to_primitive(self, target_version=None):
        """Simple base-case dehydration.

        This calls to_primitive() for each item in fields.
        """
        primitive = dict()
        for name, field in self.fields.items():
            if self.obj_attr_is_set(name):
                primitive[name] = field.to_primitive(self, name,
                                                     getattr(self, name))
        if target_version:
            self.obj_make_compatible(primitive, target_version)
        obj = {'healing_object.name': self.obj_name(),
               'healing_object.namespace': 'healing',
               'healing_object.version': target_version or self.VERSION,
               'healing_object.data': primitive}
        if self.obj_what_changed():
            obj['healing_object.changes'] = list(self.obj_what_changed())
        return obj
    
    @classmethod
    def _obj_from_primitive(cls, context, objver, primitive):
        self = cls()
        self._context = context
        self.VERSION = objver
        objdata = primitive['healing_object.data']
        changes = primitive.get('healing_object.changes', [])
        for name, field in self.fields.items():
            if name in objdata:
                setattr(self, name, field.from_primitive(self, name,
                                                         objdata[name]))
        self._changed_fields = set([x for x in changes if x in self.fields])
        return self

    @classmethod
    def obj_from_primitive(cls, primitive, context=None):
        """Object field-by-field hydration."""
        print primitive
        if primitive['healing_object.namespace'] != 'healing':
            # NOTE(danms): We don't do anything with this now, but it's
            # there for "the future"
            raise exception.UnsupportedObjectError(
                objtype='%s.%s' % (primitive['nova_object.namespace'],
                                   primitive['nova_object.name']))
        objname = primitive['healing_object.name']
        objver = primitive['healing_object.version']
        objclass = cls.obj_class_from_name(objname, objver)
        return objclass._obj_from_primitive(context, objver, primitive)



class HealingPersistentObject(object):
    """Mixin class for Persistent objects.
    This adds the fields that we use in common for all persisent objects.
    """
    fields = {'created_at': fields.DateTimeField(nullable=True),
              'updated_at': fields.DateTimeField(nullable=True)}



class HealingObjectSerializer(messaging.NoOpSerializer):
    """A HealingObject-aware Serializer.

    This implements the Oslo Serializer interface and provides the
    ability to serialize and deserialize NovaObject entities. Any service
    that needs to accept or return NovaObjects as arguments or result values
    should pass this to its RPCClient and RPCServer objects.
    """
    def _process_object(self, context, objprim):
        
        objinst = HealingObject.obj_from_primitive(objprim, context=context)
        return objinst

    def _process_iterable(self, context, action_fn, values):
        """Process an iterable, taking an action on each value.
        :param:context: Request context
        :param:action_fn: Action to take on each item in values
        :param:values: Iterable container of things to take action on
        :returns: A new container of the same type (except set) with
                  items from values having had action applied.
        """
        iterable = values.__class__
        if iterable == set:
            # NOTE(danms): A set can't have an unhashable value inside, such as
            # a dict. Convert sets to tuples, which is fine, since we can't
            # send them over RPC anyway.
            iterable = tuple
        return iterable([action_fn(context, value) for value in values])

    def serialize_entity(self, context, entity):
        if isinstance(entity, (tuple, list, set)):
            entity = self._process_iterable(context, self.serialize_entity,
                                            entity)
        elif (hasattr(entity, 'obj_to_primitive') and
              callable(entity.obj_to_primitive)):
            entity = entity.obj_to_primitive()
        return entity

    def deserialize_entity(self, context, entity):
        if isinstance(entity, dict) and 'healing_object.name' in entity:
            entity = self._process_object(context, entity)
        elif isinstance(entity, (tuple, list, set)):
            entity = self._process_iterable(context, self.deserialize_entity,
                                            entity)
        return entity


