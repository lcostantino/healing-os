import six

from keystoneclient import client as keystone_client
from novaclient.v1_1 import client as nova_client
from ceilometerclient import client as ceilometer_client

from healing import config
from healing import context
from healing import exceptions as exc
from healing.openstack.common import jsonutils
from healing.openstack.common import log as logging
from healing.openstack.common import timeutils


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
        password = config.CONF.keystone.admin_password

    ctx = context.Context(user=username, password=password)
    get_auth_token(ctx, admin)

    return ctx


def context_from_headers(headers):
    token = headers.get('X-Auth-Token')
    catalog = jsonutils.loads(headers.get('X-Service-Catalog', {}))
    ctx = context.Context(user_id=headers.get('X-User-Id'),
                           project=headers.get('X-Project-Name'),
                           token=token,
                           service_catalog=catalog,
                           user=headers.get('X-User-Name'),
                           roles=headers.get('X-Roles', "").split(","))
    return ctx


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


def get_endpoint_url(ctx, service='identity', endpoint_type='public',
                     version="v3", region=None):
    """ TODO: Check how it works when X-Service-Catalog is in HEADERs on auth
        enabled. Probably this will fail.
        ADd version check
    """
    if not ctx.service_catalog:
        return None
    if type(ctx.service_catalog) == list:
        for ep in ctx.service_catalog:
            if ep.get('type') != service:
                continue
            for available in ep.get('endpoints'):
                if region and available.get('region') != region:
                    continue
                if available.get('interface') != endpoint_type:
                    continue
                return available.get('url')

    else:
        for x in ctx.service_catalog.get(service, {}):
            if region and not x.get('region') == region:
                continue
            if x.get('interface') != endpoint_type:
                continue
            return x.get('url')
    return None


def get_keystone_client(auth_url, username=None, password=None,
                        project_name=None, auth_token=None, **kwargs):
    client = keystone_client.Client(username=username, password=password,
                                    project_name=project_name,
                                    token=auth_token, auth_url=auth_url,
                                    **kwargs)

    return client


def admin_keystone_client(project_name, **kwargs):
    auth_url = config.CONF.keystone.auth_uri
    client = get_keystone_client(username=config.CONF.keystone.admin_user,
                                 password=config.CONF.keystone.admin_password,
                                 project_name=project_name,
                                 auth_url=auth_url, **kwargs)
    client.management_url = auth_url
    return client


def get_nova_client(ctx):
    url = config.CONF.keystone.auth_uri
    client = nova_client.Client(ctx.user, ctx.user_id, ctx.project,
                                auth_token=ctx.token,
                                auth_url=url,
                                bypass_url=get_endpoint_url(ctx,
                                                            service='compute'))
    return client


def get_ceilometer_client(ctx):
    ep = get_endpoint_url(ctx, service='metering')
    client = ceilometer_client.get_client("2", ceilometer_url=ep,
                                          os_auth_token=ctx.token)
    return client


def get_ceilometer_statistics(client, group_by='resource_id',
                              period=0, query=None,
                              start_date=None, end_date=None,
                              aggregates=None, delta_seconds=None,
                              meter=None):
    try:
        period = period or 0
        query = query or []
        meter = meter
        if not end_date:
            end_date = timeutils.utcnow()
        if not start_date:
            delta_seconds = timeutils.datetime.timedelta(seconds=delta_seconds)
            start_date = end_date - delta_seconds
        #lt,le,gt,ge not supported for start and end, but this should work
        query.append(build_ceilometer_query(field='end', operator='eq',
                                            value=timeutils.strtime(end_date)))
        query.append(build_ceilometer_query(
                                    value=timeutils.strtime(start_date),
                                    operator='eq', field='start'))
        return client.statistics.list(meter_name=meter, period=period, q=query,
                                      groupby=group_by,
                                      aggregates=aggregates or [])
    except Exception as e:
        LOG.exception(e)
        return None


def build_ceilometer_query(field, operator, value, field_type=''):
    return {'field': field, 'op': operator, 'value': value,
            'type': field_type}


def get_nova_vms(client, tenant_id=None, host=None):
    res_by_tenant_id = {}
    search_opts = {}
    if not tenant_id:
        search_opts['all_tenants'] = 1
    else:
        search_opts['tenant_id'] = tenant_id

    if host:
        search_opts['host'] = host
    res = client.servers.list(search_opts=search_opts)
    if res:
        for x in res:
            if not res_by_tenant_id.get(x.tenant_id):
                res_by_tenant_id[x.tenant_id] = []
            res_by_tenant_id[x.tenant_id].append({'id': x.id,
                                'vm_state': getattr(x, 'OS-EXT-STS:vm_state'),
                                'power_state': getattr(x, 'OS-EXT-STS:power_state'),
                                'name': x.name})
    return res_by_tenant_id

    pass
