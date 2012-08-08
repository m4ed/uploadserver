from pyramid.config import Configurator

import pymongo

from .request import CustomRequestFactory


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(
        settings=settings,
        request_factory=CustomRequestFactory
        )

    # Set up the mongo connection
    mongo_host = config.registry.settings['db.mongo.host']
    mongo_port = int(config.registry.settings['db.mongo.port'])
    config.registry.settings['db.mongo.conn'] = pymongo.Connection(host=mongo_host, port=mongo_port)

    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('upload', '/upload')
    config.scan()
    return config.make_wsgi_app()
