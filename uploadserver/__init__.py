from pyramid.config import Configurator
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy

from pyramid_beaker import session_factory_from_settings
import pymongo
import zmq

from .request import CustomRequestFactory
from .util.settings import parse_asset_settings
from .util.image import ImageProcessor


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """

    session_factory = session_factory_from_settings(settings)
    #UnencryptedCookieSessionFactoryConfig('itsaseekreet')

    #print session_factory

    authn_policy = AuthTktAuthenticationPolicy(
        'supersecretstring',
        callback=lambda x, y: ['g:superuser']  # TODO: Implement a group finder
    )

    authz_policy = ACLAuthorizationPolicy()

    config = Configurator(
        settings=settings,
        authentication_policy=authn_policy,
        authorization_policy=authz_policy,
        session_factory=session_factory,
        request_factory=CustomRequestFactory,
        root_factory='m4ed.factories:RootFactory'
    )

    config.registry.settings['assets'] = parse_asset_settings(settings)

    asset_settings = config.registry.settings['assets']

    # Set up the mongo connection
    mongo_host = config.registry.settings['db.mongo.host']
    mongo_port = int(config.registry.settings['db.mongo.port'])
    db_conn = pymongo.Connection(host=mongo_host, port=mongo_port)
    config.registry.settings['db.mongo.conn'] = db_conn

    upload_queue = zmq.Context().socket(zmq.PUSH)
    upload_queue.connect(settings['zmq.socket'])
    config.registry.settings['zmq.upload_queue'] = upload_queue

    db_name = config.registry.settings['db.mongo.collection_name']

    config.registry.settings['imager'] = ImageProcessor(
        db=db_conn[db_name], image_save_path=asset_settings['save_path'])

    config.add_static_view('static', 'static', cache_max_age=3600)
    config.include(api, route_prefix='/api')
    config.scan()
    return config.make_wsgi_app()


def api(config):
    config.include(asset_api, route_prefix='/assets')


def asset_api(config):
    config.add_route('rest_assets', '/', factory='m4ed.factories:AssetFactory')
    config.add_route('rest_asset', '/{id}', factory='m4ed.factories:AssetFactory', traverse='/{id}')
