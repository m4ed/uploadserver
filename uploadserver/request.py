from pyramid.decorator import reify
from pyramid.request import Request

from gridfs import GridFS


class CustomRequestFactory(Request):
    """ Add db, fs and user variables to every request.
    """

    @reify
    def db(self):
        settings = self.registry.settings
        db_name = settings['db.mongo.collection_name']
        db_conn = settings['db.mongo.conn']
        return db_conn[db_name]

    @reify
    def fs(self):
        return GridFS(self.db)

    @reify
    def cloud(self):
        return self.registry.settings['cloud']

    @reify
    def upload_queue(self):
        return self.registry.settings['zmq.upload_queue']

    @reify
    def imager(self):
        return self.registry.settings['imager']
