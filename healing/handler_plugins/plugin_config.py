"""
Read plugin config for provided check actions.
"""
import os
import yaml

from healing import config as cfg
from healing.openstack.common import log as logging

LOG = logging.getLogger(__name__)

#PLUGIN_CONFIG = None

class PluginConfig(object):
   """
   Actually, this checks could be plugins also that register
   they own configs / params
   If this get better, switch..
   """
   def __init__(self, cfg=None, restriction_data=None, plugin_names=None):
       """
       Restriction data is name + config params for each one.
       """
       self.plugin_config = cfg
       self.valid_restrictions = {}
       # TODO: load in memory this instances only? test with greenthredads
       # also will depend if they are going to have attributes...
       self.used_restrictions = set()
       if restriction_data and cfg:
           self.check_config(restriction_data, plugin_names)
       
   def _check_restriction(self, restriction, restriction_data):
       if restriction_data is None:
           LOG.warning('Unknown restriction name in config %s', restriction.get('name'))
           return False
       self.used_restrictions.add(restriction.get('name'))
       if not restriction.get('config'):
           restriction['config'] = {}
       for config in restriction.get('config', {}).keys():
           if config not in restriction_data.keys():
               LOG.warning('Unknown config %s for %s', config, restriction.get('name'))
       return True
   
   def check_config(self, restriction_data, plugin_names):
       """
       This will check the plugin names and restrictions, and output
       warning message in case of errors.
       """
       for x in self.plugin_config.get("plugins", {}):
           name = x.get('name')
           if name and name != '*' and name not in plugin_names:
               LOG.warning('Unknown plugin name in config %s', name)
               continue
           self.valid_restrictions[name] = []
           for restrict in x.get('restrictions', {}):
               if self._check_restriction(restrict, restriction_data.get(restrict.get('name'))):
                   self.valid_restrictions[name].append(restrict) 
                
   def get_restriction_config_for(self, plugin_name):
       restrictions = self.valid_restrictions.get(plugin_name)
       if not restrictions:
           restrictions = self.valid_restrictions.get('*', None)
        
       return restrictions
          

def setup_config(available_restrictions, plugin_names):
    """ Same as ceilometer."""
    cfg_file = cfg.CONF.plugins.plugins_config_file
    if not os.path.exists(cfg_file):
        cfg_file = cfg.CONF.find_file(cfg_file)
    
    LOG.debug("Plugins config file: %s", cfg_file)
    plugins_cfg = None
    try:                     
        with open(cfg_file) as fap:
            data = fap.read()
        plugins_cfg = yaml.safe_load(data)
    except Exception as e:
        LOG.exception(e)
        raise
    return PluginConfig(plugins_cfg, available_restrictions, plugin_names)


