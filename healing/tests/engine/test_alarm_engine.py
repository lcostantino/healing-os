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

def get_alarm_data(ctx=None, meter=u'meter', period=10,
                   threshold='22', query=None, alarm_id=None,
                   contract_id=1, options=None, alarm_object=None,
                   operator=u'eq', evaluation_period=1, 
                   statistic=None, **kwargs):
    return {'meter': meter, 'period': period,
            'threshold': threshold, 'query': query,
            'contract_id': contract_id,
            'remote_alarm_id': alarm_id,
            'evaluation_period': evaluation_period,
            'alarm_id': alarm_id,  #just for object
            'alarm_object': alarm_object,
            'statistic': statistic,
            'action': 'none',
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
                    'evaluation_period': data['evaluation_period'],
                    'type': 'threshold'}
        
        cmeter_mock.alarms.update.assert_called_once_with(alarm_id=u'ceilometer-id', **expected)

    
    def test_alarm_create_hooks_and_options(self, get_client_mock):
        # TODO: add resource_id and project in tests
        cmeter_mock = mock.MagicMock(set_specs=ceilometerclient.client.Client)
        get_client_mock.return_value = cmeter_mock
        cmeter_mock.alarms.create.return_value = get_fake_alarm_ceilometer(111)
        
        url = 'http://local-heal.com:12000/'
        options = {'base_alarm_url': url,
                   'repeteable': True}

        data = get_alarm_data(evaluation_period=33, **options)
        data.update(options)
        am = ceilometer_alarms.CeilometerAlarm(**data)
        am.alarm_track = fake_alarm_object(**data)
        am.set_default_alarm_hook()
        am.set_default_ok_hook()
        am.set_default_insufficient_hook()
        self.assertEquals(url + '?status=alarm&source=ceilometer', am.hooks[alarm_base.ALARM_HOOK])
        self.assertEquals(url + '?status=ok&source=ceilometer', am.hooks[alarm_base.OK_HOOK])
        self.assertEquals(url + '?status=insufficient&source=ceilometer', am.hooks[alarm_base.INSUFFICIENT_HOOK])
        
        expected = {'period': data['period'], 
                    'name': am.alarm_track.id,
                    'repeat_actions': data.get('repeateable', False),
                    'meter_name': data['meter'], 'threshold': data['threshold'],
                    'comparison_operator': data['operator'],
                    'type': 'threshold', 'evaluation_period': data['evaluation_period']}
        expected['alarm_actions'] = am.hooks[alarm_base.ALARM_HOOK]
        expected['ok_actions'] = am.hooks[alarm_base.OK_HOOK]
        expected['insufficient_data_actions'] = am.hooks[alarm_base.INSUFFICIENT_HOOK]
        am.create()
        cmeter_mock.alarms.create.assert_called_once_with(**expected)

        

@mock.patch('healing.db.api')
class TestHostDownAlarm(base.TestCase):
    
    def setUp(self):
        super(TestHostDownAlarm, self).setUp()
        
    
    @mock.patch('healing.engine.alarms.ceilometer_alarms.CeilometerAlarm.create')
    def test_first_alarm_create_external(self, parent_create_mock, db_api_mock):
        db_api_mock.alarm_track_create = mock.Mock()
        data = get_alarm_data()
        am = ceilometer_alarms.HostDownUniqueAlarm(**data)
        with mock.patch.object(am, 'get_unique_alarm') as mk:
            mk.return_value = None
            am.alarm_track = fake_alarm_object(**data)
            am.create()
        self.assertTrue(parent_create_mock.called)
        
    
    @mock.patch('healing.engine.alarms.ceilometer_alarms.CeilometerAlarm.create')
    @mock.patch('healing.objects.alarm_track.AlarmTrack.get_by_type')
    def test_second_alarm_dont_create_external(self, alarm_get_mock,
                                               parent_create_mock, db_api_mock):
        db_api_mock.alarm_track_create = mock.Mock()
        data = get_alarm_data()
        am = ceilometer_alarms.HostDownUniqueAlarm(**data)
        alarm_get_mock.return_value =  fake_alarm_object(**data)
        new_alarm_data = dict(data)
        new_alarm_data['id'] = 0
        new_alarm_data['alarm_id'] = None
        am.alarm_track = fake_alarm_object(**data)
        am.create()
        self.assertFalse(parent_create_mock.called)
        self.assertTrue(am.alarm_track.create.called)
        self.assertEqual(am.alarm_id, alarm_get_mock.return_value.alarm_id)
        
    
    @mock.patch('healing.engine.alarms.ceilometer_alarms.CeilometerAlarm.delete')
    @mock.patch('healing.objects.alarm_track.AlarmTrack.get_by_type')
    def test_delete_alarm_dont_delete_external_if_have_records(self, alarm_get_mock,
                                               parent_delete_mock, db_api_mock):
        db_api_mock.alarm_track_create = mock.Mock()
        data = get_alarm_data()
        # in real code we use alarm utils get by type() from alarm object
        # for testing purposes is the same.
        am = ceilometer_alarms.HostDownUniqueAlarm(**data)
        alarm_get_mock.return_value = fake_alarm_object(**data)
        new_alarm_data = dict(data)
        new_alarm_data['id'] = 0
        new_alarm_data['alarm_id'] = None
        am.alarm_track = fake_alarm_object(**data)
        am.delete()
        self.assertFalse(parent_delete_mock.called)
        self.assertTrue(am.alarm_track.delete.called)
       
    
    @mock.patch('healing.engine.alarms.ceilometer_alarms.CeilometerAlarm.delete')
    @mock.patch('healing.objects.alarm_track.AlarmTrack.get_by_type')
    def test_delete_alarm_if_last_record(self, alarm_get_mock,
                                               parent_delete_mock, db_api_mock):
        db_api_mock.alarm_track_create = mock.Mock()
        data = get_alarm_data()
        # in real code we use alarm utils get by type() from alarm object
        # for testing purposes is the same.
        am = ceilometer_alarms.HostDownUniqueAlarm(**data)
        alarm_get_mock.return_value = None
        new_alarm_data = dict(data)
        new_alarm_data['id'] = 0
        new_alarm_data['alarm_id'] = None
        am.alarm_track = fake_alarm_object(**data)
        am.delete()
        self.assertTrue(parent_delete_mock.called)
        self.assertTrue(am.alarm_track.delete.called)
       

    @mock.patch('healing.engine.alarms.ceilometer_alarms.CeilometerAlarm.update')
    @mock.patch('healing.objects.alarm_track.AlarmTrack.get_by_type')
    def test_update_once_on_multiple_records(self, alarm_get_mock,
                                             parent_update_mock, db_api_mock):
        db_api_mock.alarm_track_create = mock.Mock()
        
        
        first_record_obj = fake_alarm_object(**get_alarm_data(contract_id=22, treshold=33, period=22))
        second_record_obj = fake_alarm_object(**get_alarm_data(contract_id=33, treshold=33, period=22))
        unique_db_alarm = get_alarm_data(contract_id=22, threhold=22, period=10)
    
        first_record_obj.type = ceilometer_alarms.HostDownUniqueAlarm.ALARM_TYPE
        second_record_obj.type = ceilometer_alarms.HostDownUniqueAlarm.ALARM_TYPE
        # we should not need to test this here, but instead mock if_something_changed.
        first_alarm = ceilometer_alarms.HostDownUniqueAlarm(ctx=None, alarm_object=first_record_obj)
        
        alarm_get_mock.return_value = fake_alarm_object(**unique_db_alarm)
        first_alarm.update()
        self.assertTrue(parent_update_mock.called)
        self.assertTrue(first_record_obj.save.called)
        
        # now, the unique_db_alarm should be equal to first_record_obj in db
        parent_update_mock.reset_mock()
        alarm_get_mock.return_value = first_record_obj
        second_alarm =  ceilometer_alarms.HostDownUniqueAlarm(ctx=None, alarm_object=second_record_obj)
        second_alarm.update()
        self.assertFalse(parent_update_mock.called)
        self.assertTrue(second_record_obj.save.called)
       


@mock.patch('healing.db.api')
class TestResourceAlarm(base.TestCase):
    
    def setUp(self):
        super(TestResourceAlarm, self).setUp()
        
    
    @mock.patch('healing.engine.alarms.ceilometer_alarms.CeilometerAlarm.create')
    def test_alarm_create_external(self, parent_create_mock, db_api_mock):
        db_api_mock.alarm_track_create = mock.Mock()
        data = get_alarm_data()
        data['resource_id'] = 'myvm'
        data['project_id'] = 'sss'
        am = ceilometer_alarms.ResourceAlarm(**data)
        am.alarm_track = fake_alarm_object(**data)
        am.create()
        self.assertEquals('resource_id', am.query[0]['field'])
        self.assertEquals('project_id', am.query[1]['field'])
        self.assertTrue(parent_create_mock.called)
        
    """    
    @mock.patch('healing.engine.alarms.ceilometer_alarms.CeilometerAlarm.delete')
    @mock.patch('healing.objects.alarm_track.AlarmTrack.get_by_type')
    def test_delete_alarm_if_last_record(self, alarm_get_mock,
                                               parent_delete_mock, db_api_mock):
        db_api_mock.alarm_track_create = mock.Mock()
        data = get_alarm_data()
        # in real code we use alarm utils get by type() from alarm object
        # for testing purposes is the same.
        am = ceilometer_alarms.HostDownUniqueAlarm(**data)
        alarm_get_mock.return_value = None
        new_alarm_data = dict(data)
        new_alarm_data['id'] = 0
        new_alarm_data['alarm_id'] = None
        am.alarm_track = fake_alarm_object(**data)
        am.delete()
        self.assertTrue(parent_delete_mock.called)
        self.assertTrue(am.alarm_track.delete.called)
       
        
    @mock.patch('healing.engine.alarms.ceilometer_alarms.CeilometerAlarm.update')
    @mock.patch('healing.objects.alarm_track.AlarmTrack.get_by_type')
    def test_update_once_on_multiple_records(self, alarm_get_mock,
                                             parent_update_mock, db_api_mock):
        db_api_mock.alarm_track_create = mock.Mock()
        
        
        first_record_obj = fake_alarm_object(**get_alarm_data(contract_id=22, treshold=33, period=22))
        second_record_obj = fake_alarm_object(**get_alarm_data(contract_id=33, treshold=33, period=22))
        unique_db_alarm = get_alarm_data(contract_id=22, threhold=22, period=10)
    
        first_record_obj.type = ceilometer_alarms.HostDownUniqueAlarm.ALARM_TYPE
        second_record_obj.type = ceilometer_alarms.HostDownUniqueAlarm.ALARM_TYPE
        # we should not need to test this here, but instead mock if_something_changed.
        first_alarm = ceilometer_alarms.HostDownUniqueAlarm(ctx=None, alarm_object=first_record_obj)
        
        alarm_get_mock.return_value = fake_alarm_object(**unique_db_alarm)
        first_alarm.update()
        self.assertTrue(parent_update_mock.called)
        self.assertTrue(first_record_obj.save.called)
        
        # now, the unique_db_alarm should be equal to first_record_obj in db
        parent_update_mock.reset_mock()
        alarm_get_mock.return_value = first_record_obj
        second_alarm =  ceilometer_alarms.HostDownUniqueAlarm(ctx=None, alarm_object=second_record_obj)
        second_alarm.update()
        self.assertFalse(parent_update_mock.called)
        self.assertTrue(second_record_obj.save.called)
       
    """