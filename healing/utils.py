from keystoneclient import client as keystone_client
from novaclient.v1_1 import client as nova_client
from ceilometerclient import client as ceilometer_client

from healing import config
from healing import context
from healing import exceptions as exc
from healing.openstack.common import log as logging


LOG = logging.getLogger(__name__)

#with build_context()?


def build_context(username=None, password=None,
                  headers=None, admin=True):
    """
    This is if we really want to get token first,
    but having user/pass can be used on clients
    directly.
    """
    if headers:
        return context_from_headers(headers)
    # empty user password, only token here. check if we want this..
    # this is used by the plugins and fake context request if auth disabled
    if not username and not password and admin:
        username = config.CONF.keystone.admin_user
        password=config.CONF.keystone.admin_password

    ctx = context.Context(user=username, password=password)
    get_auth_token(ctx, admin)

    return ctx

def context_from_headers(headers):
    return context.Context(
             user_id=headers.get('X-User-Id'),
             project=headers.get('X-Project-Name'),
             token=headers.get('X-Auth-Token'),
             service_catalog=headers.get('X-Service-Catalog'),
             user=headers.get('X-User-Name'),
             roles=headers.get('X-Roles', "").split(",")
    )


def get_context_req(request, admin=True):
    """ Get context from request, should be setup
        by DelayedAuthHook on authorized urls.
    """
    #IF AUTHO NOT ENABLED< RETURN A FIXED CONTEXT,
    #with user password from config? only for debug

    if admin:
        return request.admin_ctx
    return request.user_ctx

def get_auth_token(ctx, admin=True, refresh_token=False):
    if ctx.token and not refresh_token:
        return

    ctx.token = None
    #todo: user token o impersonate
    # REPLCE USERNAME with The user RETURNED By KEYSTONE

    if admin:
        client = admin_keystone_client('admin')
    try:
        client.authenticate()
        #se puede pasar un proxy_tenant y proxy_token  los clientes
        #para impersonar
        ctx.token = client.auth_token
        ctx.user_id = client.user_id
        ctx.service_catalog = client.service_catalog.get_endpoints()
    except Exception as e:
        LOG.exception(e)
        raise exc.AuthorizationException()

def get_endpoint_url(ctx, service='identity', endpoint_type='publicURL',
                     version="v2", region=None):
    """ TODO: Check how it works when X-Service-Catalog is in HEADERs on auth 
        enabled. Probably this will fail.
        ADd version check
    """
    if not ctx.service_catalog:
        return None
    
    for x in ctx.service_catalog.get(service):
        if region and not x.get(region) == region:
            continue
        return x.get(endpoint_type)
        
    return None

def get_keystone_client(auth_url, username=None, password=None, project_name=None, 
                        auth_token=None):
    client = keystone_client.Client(username=username, password=password,
                                   project_name=project_name, auth_token=auth_token,
                                   auth_url=auth_url)

    return client

def admin_keystone_client(project_name):
    auth_url = config.CONF.keystone.auth_uri
    
    client = get_keystone_client(
                        username=config.CONF.keystone.admin_user,
                        password=config.CONF.keystone.admin_password,
                        project_name=project_name,
                        auth_url=auth_url)

    client.management_url = auth_url
    return client


def get_nova_client(ctx):
    client = nova_client.Client(ctx.user, ctx.user_id, ctx.project,
                                auth_token=ctx.token,
                                auth_url=config.CONF.keystone.auth_uri)
    client.management_url = config.CONF.keystone.auth_uri
    return client


def get_ceilometer_client(ctx):
    ep = get_endpoint_url(ctx, service='metering')
    client = ceilometer_client.get_client("2", ceilometer_url=ep, 
                                              os_auth_token = ctx.token)
    return client
