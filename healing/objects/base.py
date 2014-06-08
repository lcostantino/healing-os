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

class HealingPersistentObject(object):
    """Mixin class for Persistent objects.
    This adds the fields that we use in common for all persisent objects.
    """
    fields = {'created_at': fields.DateTimeField(nullable=True),
              'updated_at': fields.DateTimeField(nullable=True)}
