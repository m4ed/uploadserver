from pyramid.config import Configurator

import pymongo
import zmq

from .request import CustomRequestFactory
from .util.settings import parse_asset_settings
from .util.image import ImageProcessor


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """

    config = Configurator(
        settings=settings,
        request_factory=CustomRequestFactory
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
    config.add_route('home', '/')
    config.add_route('upload', '/upload')
    config.scan()
    return config.make_wsgi_app()
