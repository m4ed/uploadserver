import sys
import zmq
import pymongo

import os

from bson.objectid import ObjectId

from util.cloud import Cloud
from util.settings import parse_asset_settings

try:
    import configparser
except ImportError:
    import ConfigParser as configparser


def main():
    settings = configparser.SafeConfigParser()
    with open(sys.argv[1]) as fp:
        settings.readfp(fp)
    settings = dict(settings.items('app:main'))
    settings.update(parse_asset_settings(settings))
    worker = UploadWorker(**settings)
    worker.run()


class UploadWorker(object):
    def __init__(self, **settings):

        print settings

        conn = pymongo.Connection(
            host=settings['db.mongo.host'],
            port=int(settings['db.mongo.port'])
        )
        self.db = conn[settings['db.mongo.collection_name']]

        context = zmq.Context()

        self.receiver = context.socket(zmq.PULL)
        self.receiver.connect(settings['zmq.socket'])

        self.save_path = settings['save_path']

        self.cloud = Cloud(**settings)

    def run(self):
        while True:
            try:
                s = self.receiver.recv()
            except KeyboardInterrupt:
                raise SystemExit
            print s
            args = s.split(':')
            getattr(self, args[0])(args[1])

    def save(self, _id):
        asset = self.db.assets.find_one({'_id': ObjectId(_id)})
        print asset
        name = asset.get('name')
        directory = asset.get('id')
        thumb_name = '_s.'.join(name.rsplit('.', 1))
        full_save_path = os.path.join(
            self.save_path, directory, name
        )
        thumb_save_path = os.path.join(
            self.save_path, directory, thumb_name
        )

        url = self.cloud.save(full_save_path)
        os.unlink(full_save_path)
        thumb_url = self.cloud.save(thumb_save_path)
        os.unlink(thumb_save_path)

        if asset.get('type') == 'anim':
            for x in range(1, asset.get('frames')):
                p = os.path.join(
                    self.save_path, directory, '{}_{}'.format(x, name)
                )
                self.cloud.save(p)
                os.unlink(p)

        os.rmdir(directory)

        self.db.assets.update(
            {'_id': ObjectId(_id)},
            {'$set': {'url': url, 'thumbnail_url': thumb_url}}
        )

    def delete(self, _id):
        raise NotImplementedError


if __name__ == '__main__':
    main()
