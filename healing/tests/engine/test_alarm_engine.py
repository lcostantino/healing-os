# -*- coding: utf-8 -*-

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import mock

from healing.engine.alarms import alarm_base
from healing.engine.alarms import ceilometer_alarms
from healing.engine.alarms import manager
from healing.objects import alarm_track
from healing.tests import base




import ceilometerclient

def get_alarm_data(ctx=None, meter=u'meter', period=u'10',
                   threshold=u'22', query=None, alarm_id=None,
                   contract_id=1, options=None, alarm_object=None,
                   operator=u'eq', evaluation_period=None, **kwargs):
    return {'meter': meter, 'period': period,
            'threshold': threshold, 'query': query,
            'contract_id': contract_id,
            'remote_alarm_id': alarm_id,
            'evaluation_period': evaluation_period,
            'alarm_id': alarm_id,  #just for object
            'alarm_object': alarm_object,
            'operator': operator, 'ctx': ctx}

def fake_alarm_object(fake_id=None, **data):
    obj = alarm_track.AlarmTrack(**data)
    obj.id = fake_id or 'dummy'
        
    obj.create = mock.Mock()
    obj.save = mock.Mock()
    obj.delete = mock.Mock()
    return obj

class FakeAlarmCeilometer:
    alarm_id = 111
    
def get_fake_alarm_ceilometer(alarm_id):
    fk = FakeAlarmCeilometer()
    fk.alarm_id = alarm_id
    return fk
    
@mock.patch('healing.utils.get_ceilometer_client')
class TestCeilometerAlarm(base.TestCase):

    def setUp(self):
        super(TestCeilometerAlarm, self).setUp()
        
    def test_alarm_create(self, get_client_mock):
        cmeter_mock = mock.MagicMock(set_specs=ceilometerclient.client.Client)
        get_client_mock.return_value = cmeter_mock
        cmeter_mock.alarms.create.return_value = get_fake_alarm_ceilometer(111)
        
        data = get_alarm_data()
        am = ceilometer_alarms.CeilometerAlarm(**data)
        am.alarm_track = fake_alarm_object(**data)
        am.create()
        self.assertTrue(cmeter_mock.alarms.create.called)

    
    def test_alarm_delete(self, get_client_mock):
        cmeter_mock = mock.MagicMock(set_specs=ceilometerclient.client.Client)
        get_client_mock.return_value = cmeter_mock
        mock_obj = fake_alarm_object(fake_id=333, alarm_id=u'222')
        data = get_alarm_data(alarm_object=mock_obj)
        am = ceilometer_alarms.CeilometerAlarm(**data)
        am.delete()
        cmeter_mock.alarms.delete.assert_called_once_with(alarm_id=u'222')

    def test_alarm_update(self, get_client_mock):
        cmeter_mock = mock.MagicMock(set_specs=ceilometerclient.client.Client)
        get_client_mock.return_value = cmeter_mock
        data = get_alarm_data(alarm_id='ceilometer-id')
        
        mock_obj = fake_alarm_object(fake_id='track_id', **data)
        am = ceilometer_alarms.CeilometerAlarm(ctx=None, alarm_object=mock_obj)

        am.update()
        expected = {'period': data['period'], 
                    'name': mock_obj.id,
                    'repeat_actions': data.get('repeateable', False),
                    'meter_name': data['meter'], 'threshold': data['threshold'],
                    'comparison_operator': data['operator'],
                    'type': 'threshold'}
        
        cmeter_mock.alarms.update.assert_called_once_with(alarm_id=u'ceilometer-id', **expected)

    
    def test_alarm_create_hooks_and_options(self, get_client_mock):
        cmeter_mock = mock.MagicMock(set_specs=ceilometerclient.client.Client)
        get_client_mock.return_value = cmeter_mock
        cmeter_mock.alarms.create.return_value = get_fake_alarm_ceilometer(111)
        
        url = 'http://local-heal.com:12000'
        options = {'base_alarm_url': url,
                   'repeteable': True}

        data = get_alarm_data(evaluation_period=33, **options)
        data.update(options)
        am = ceilometer_alarms.CeilometerAlarm(**data)
        am.alarm_track = fake_alarm_object(**data)
        am.set_default_alarm_hook()
        am.set_default_ok_hook()
        am.set_default_insufficient_hook()
        self.assertEquals(url + '?status=alarm', am.hooks[alarm_base.ALARM_HOOK])
        self.assertEquals(url + '?status=ok', am.hooks[alarm_base.OK_HOOK])
        self.assertEquals(url + '?status=insufficient', am.hooks[alarm_base.INSUFFICIENT_HOOK])
        
        expected = {'period': data['period'], 
                    'name': am.alarm_track.id,
                    'repeat_actions': data.get('repeateable', False),
                    'meter_name': data['meter'], 'threshold': data['threshold'],
                    'comparison_operator': data['operator'],
                    'type': 'threshold', 'evaluation_period': str(data['evaluation_period'])}
        expected['alarm_actions'] = am.hooks[alarm_base.ALARM_HOOK]
        expected['ok_actions'] = am.hooks[alarm_base.OK_HOOK]
        expected['insufficient_data_actions'] = am.hooks[alarm_base.INSUFFICIENT_HOOK]
        am.create()
        cmeter_mock.alarms.create.assert_called_once_with(**expected)

        
