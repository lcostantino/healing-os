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
from healing import handler_manager
from healing.handler_plugins import plugin_config
from healing.handler_plugins import base as base_plugin
from healing.handler_plugins import action_data
from healing.handler_plugins.restrictions import base as restr_base
from healing.tests import base
import yaml


class FakeRestriction(restr_base.RestrictionBase):
    CFG_PARAMS = {}
    NAME = 'fakerestriction'

    def can_execute(self, config, last_action=None, ctx=None, data=None,
                    **kwargs):
        return True


class FakeRestriction2(restr_base.RestrictionBase):
    CFG_PARAMS = {}
    NAME = 'fakerestriction2'

    def can_execute(self, config, last_action=None, ctx=None, data=None,
                    **kwargs):
        return False


class FakePlugin(base_plugin.HandlerPluginBase):
    NAME = 'fake'

    def start(self, ctx, data):
        pass

    def stop(self, ctx, error=False):
        pass


class FakePlugin2(base_plugin.HandlerPluginBase):
    NAME = 'fake2'

    def start(self, ctx, data):
        pass

    def stop(self, ctx, error=False):
        pass

# TODO: do it dynamic with new method
PLUGIN_NAMES = [FakePlugin.NAME, FakePlugin2.NAME]
RESTRICTION_DATA = {'fakerestriction': FakeRestriction.CFG_PARAMS,
                    'fakerestriction2': FakeRestriction2.CFG_PARAMS}


class FakeObj(object):
    def __init__(self, name, plg):
        self.name = name
        self.plugin = plg

PLUGIN_MGR = {FakePlugin.NAME: FakeObj(FakePlugin.NAME, FakePlugin),
              FakePlugin2.NAME: FakeObj(FakePlugin2.NAME, FakePlugin2)}

RESTRICTIONS_MGR = {FakeRestriction.NAME: FakeObj(FakeRestriction.NAME,
                                                  FakeRestriction),
                    FakeRestriction2.NAME: FakeObj(FakeRestriction2.NAME,
                                                   FakeRestriction2)}


def get_action_data(name='fake', target_resource='fake', source='custom',
                    data=None, headers=None, internal_data=None):
    return action_data.ActionData(name, target_resource, source, data, headers,
                                  internal_data)


def get_sample_config():
    CONFIG = """
plugins:
  - name: "unknown"
    restrictions:
      - name: "actionstatus"
      - name: "timeinterval"
        config:
          interval: "1"
  - name: "fake"
    restrictions:
      - name: "fakerestriction"
      - name: "fakerestriction2"
        config:
          interval: "1"
  - name: "*"
    restrictions:
      - name: "fakerestriction"
      - name: "fakerestriction2"
        config:
          interval: "1000"
"""
    return yaml.safe_load(CONFIG)


class TestPluginConfig(base.TestCase):

    def setUp(self):
        super(TestPluginConfig, self).setUp()
        self.config = get_sample_config()

    def test_read_config_restrictions(self):
        pcfg = plugin_config.PluginConfig(self.config, RESTRICTION_DATA,
                                          PLUGIN_NAMES)
        self.assertEqual(2, len(pcfg.valid_restrictions))
        self.assertIn('fake', pcfg.valid_restrictions)
        self.assertIn('*', pcfg.valid_restrictions)
        self.assertEqual(2, len(pcfg.valid_restrictions['fake']))
        self.assertEqual(2, len(pcfg.valid_restrictions['*']))

    def test_get_restrictions_for_plugin(self):
        pcfg = plugin_config.PluginConfig(self.config, RESTRICTION_DATA,
                                          PLUGIN_NAMES)
        for_fake = pcfg.get_restriction_config_for(PLUGIN_NAMES[0])
        self.assertEqual('1', for_fake[1]['config']['interval'])
        self.assertEqual(2, len(for_fake))

    def test_get_restrictions_for_plugin_default_values(self):
        pcfg = plugin_config.PluginConfig(self.config, RESTRICTION_DATA,
                                          PLUGIN_NAMES)
        for_fake = pcfg.get_restriction_config_for(PLUGIN_NAMES[1])
        self.assertEqual('1000', for_fake[1]['config']['interval'])
        self.assertEqual(2, len(for_fake))


class MockHandlerManager(handler_manager.HandlerManager):
    """ to avoid mocking stevedore, init, etc.."""
    def __init__(self):
        self.config_manager = plugin_config.PluginConfig(get_sample_config(),
                                        RESTRICTION_DATA, PLUGIN_NAMES)
        self.mgr = PLUGIN_MGR
        self.restrictions = RESTRICTIONS_MGR


class TestHandlerManager(base.TestCase):

    def setUp(self):
        super(TestHandlerManager, self).setUp()
        #add to teardown?
        self.handler_manager = MockHandlerManager()

    def test_get_plugin(self):
        for name, data in PLUGIN_MGR.iteritems():
            pl = self.handler_manager.get_plugin(name)
            self.assertIsNotNone(pl)
            self.assertEquals(type(pl), type(data.plugin))

    def test_invalid_plugin(self):
        # todo: should raise notfoundexception
        self.assertRaises(Exception, self.handler_manager.get_plugin,
                          'fake22222')

    @mock.patch('healing.handler_plugins.base.HandlerPluginBase'
                '.prepare_for_checks')
    def test_restrictions_run(self, prepare_mock):
        """ The first restriction return true, so second should not be called
            as today code.
        """
        target = 'fake-host'

        def fake_prepare(*args, **kwargs):
            self.last_action = None
        prepare_mock.side_effect = fake_prepare
        data = get_action_data(PLUGIN_NAMES[0], target)
        FakeRestriction.can_execute = mock.Mock(return_value=True)
        FakeRestriction2.can_execute = mock.Mock(return_value=True)

        self.handler_manager.start_plugin(PLUGIN_NAMES[0], ctx=None, data=data)
        self.assertTrue(prepare_mock.called)
        self.assertTrue(FakeRestriction.can_execute.called)
        self.assertFalse(FakeRestriction2.can_execute.called)

    @mock.patch('healing.handler_plugins.base.HandlerPluginBase'
                '.prepare_for_checks')
    def test_restrictions_run_first_false(self, prepare_mock):
        """ The first restriction return false, so second should be called."""
        target = 'fake-host'

        def fake_prepare(*args, **kwargs):
            self.last_action = None
        prepare_mock.side_effect = fake_prepare
        data = get_action_data(PLUGIN_NAMES[0], target)
        FakeRestriction.can_execute = mock.Mock(return_value=False)
        FakeRestriction2.can_execute = mock.Mock(return_value=True)

        self.handler_manager.start_plugin(PLUGIN_NAMES[0], ctx=None, data=data)
        self.assertTrue(prepare_mock.called)
        self.assertTrue(FakeRestriction.can_execute.called)
        self.assertTrue(FakeRestriction2.can_execute.called)

    @mock.patch('healing.handler_plugins.base.HandlerPluginBase'
                '.prepare_for_checks')
    def test_restrictions_fails(self, prepare_mock):
        target = 'fake-host'

        def fake_prepare(*args, **kwargs):
            self.last_action = None
        prepare_mock.side_effect = fake_prepare
        data = get_action_data(PLUGIN_NAMES[0], target)
        # check this is nt being override on each test
        FakeRestriction.can_execute = mock.Mock(return_value=False)
        FakeRestriction2.can_execute = mock.Mock(return_value=False)
        FakePlugin.start = mock.Mock()
        self.handler_manager.start_plugin(PLUGIN_NAMES[0], ctx=None, data=data)
        self.assertTrue(prepare_mock.called)
        self.assertTrue(FakeRestriction.can_execute.called)
        self.assertTrue(FakeRestriction2.can_execute.called)

        self.assertFalse(FakePlugin.start.called)

#TODO: verify restrictions CFG are set.
