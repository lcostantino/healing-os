# -*- coding: utf-8 -*-
#
# Copyright 2014 - Intel
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

# TODO: es mejor el formaato de nova exceptions , pasarlo aca
# BaseNovaException

class HealingException(Exception):
    """Base Exception for the project

    To correctly use this class, inherit from it and define
    a 'message' and 'code' properties.
    """
    GENERIC_MESSAGE = "An unknown exception occurred"
    code = 500

    def __str__(self):
        return self.message

    def __init__(self, message=GENERIC_MESSAGE):
        self.message = message
        super(HealingException, self).__init__(
            '%s: %s' % (self.code, self.message))


class DataAccessException(HealingException):
    message= "Data access exception"


class NotFoundException(HealingException):
    message = "Object not found"
    code = 400

class InvalidSourceException(HealingException):
    message = "Source formatter invalid"


class DBDuplicateEntry(HealingException):
    message = "Database object already exists"
    code = "DB_DUPLICATE_ENTRY"


class ActionException(HealingException):
    code = "ACTION_ERROR"


class InvalidActionException(HealingException):
    message = "Invalid Action Exception"
    code = "INVALID_ACTION"


class InvalidDataException(HealingException):
    message = "Invalid action data"
    code = 400

class AuthorizationException(HealingException):
    message = "Invalid credentials / token"



class ActionInProgress(HealingException):
    message = "Action in progress or in time range"
    code = 202


class CannotStartPlugin(HealingException):
    message = "Plugin %(name)s cannot be started"
    code = 'PLUGIN_ERROR'

    def __init__(self, name):
        message = self.message % {'name': name}
        super(CannotStartPlugin, self).__init__(message=message)


class AlarmCreateOrUpdateException(HealingException):
    message = "Error creating/updating alarms"
    code = "ALARM_CREATE_UPDATE_ERROR"

class ExternalAlarmAlreadyExists(HealingException):
    message = "Duplicated alarm"
    code = 409

class IncompatibleObjectVersion(HealingException):
    message = "Incompatible object version"
    code = 500
    
    def __init__(self, objname, objver, supported):
        super(IncompatibleObjectVersion, self).__init__(message=self.message)

class UnsupportedObjectError(HealingException):
    message = "unsupported object"
    code = 500
    
    def __init__(self, objname):
        super(UnsupportedObjectError, self).__init__(message=self.message)

