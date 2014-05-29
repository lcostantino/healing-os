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

#import healing.openstack.common.exception as ex

#TODO: es mejor el formaato de nova exceptions , pasarlo aca


class HealingException(Exception):
    """Base Exception for the project

    To correctly use this class, inherit from it and define
    a 'message' and 'code' properties.
    """
    message = "An unknown exception occurred"
    code = "UNKNOWN_EXCEPTION"

    def __str__(self):
        return self.message

    def __init__(self, message=message):
        self.message = message
        super(HealingException, self).__init__(
            '%s: %s' % (self.code, self.message))


class DataAccessException(HealingException):
    def __init__(self, message=None):
        super(DataAccessException, self).__init__(message)
        if message:
            self.message = message


class NotFoundException(HealingException):
    message = "Object not found"

    def __init__(self, message=None):
        super(NotFoundException, self).__init__(message)
        if message:
            self.message = message


class InvalidSourceException(HealingException):
    message = "Source formatter invalid"

    def __init__(self, message=None):
        super(NotFoundException, self).__init__(message)
        if message:
            self.message = message


class DBDuplicateEntry(HealingException):
    message = "Database object already exists"
    code = "DB_DUPLICATE_ENTRY"

    def __init__(self, message=None):
        super(DBDuplicateEntry, self).__init__(message)
        if message:
            self.message = message


class ActionException(HealingException):
    code = "ACTION_ERROR"

    def __init__(self, message=None):
        super(HealingException, self).__init__(message)
        if message:
            self.message = message


class InvalidActionException(HealingException):
    def __init__(self, message=None):
        super(InvalidActionException, self).__init__(message)
        if message:
            self.message = message


class InvalidDataException(HealingException):
    message = "Invalid action data"
    code = "INVALID_ACTION_DATA"

    def __init__(self, message=None):
        super(InvalidDataException, self).__init__(message)
        if message:
            self.message = message


class AuthorizationException(HealingException):
    message = "Invalid credentials / token"
    code = "INVALID_AUTH"

    def __init__(self, message=None):
        super(AuthorizationException, self).__init__(message)
        if message:
            self.message = message
