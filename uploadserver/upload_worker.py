import sys
import zmq
import pymongo
import os
import threading

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

    url_worker = 'inproc://workers'
    url_client = settings['zmq.socket']

    context = zmq.Context(1)

    # The 'frontend' facing the clients where new jobs are being sent
    clients = context.socket(zmq.PULL)
    clients.bind(url_client)

    # The 'backend' facing the workers where received jobs are being pushed
    workers = context.socket(zmq.PUSH)
    workers.bind(url_worker)

    conn = pymongo.Connection(
        host=settings['db.mongo.host'],
        port=int(settings['db.mongo.port'])
    )

    db = conn[settings['db.mongo.collection_name']]

    print '\n\nInitializing cloud connection...'
    cloud = Cloud(**settings)

    save_path = settings['save_path']

    for i in range(int(settings['zmq.workers'])):
        worker = UploadWorker(
            name='[worker-thread-{}]'.format(i),
            context=context,
            worker_url=url_worker,
            db=db,
            cloud=cloud,
            save_path=save_path
        )
        worker.start()

    try:
        print 'Starting zmq streamer'
        print 'Now waiting for jobs...'
        zmq.device(zmq.STREAMER, clients, workers)
    except KeyboardInterrupt:
        pass

    # We never get here... but if we do, shut down!
    print '\n\nShutting down...\n'

    clients.close()
    workers.close()
    context.term()


class UploadWorker(threading.Thread):
    def __init__(self, name, context, worker_url, db, cloud, save_path):
        super(UploadWorker, self).__init__()
        self.name = name
        self.db = db
        self.cloud = cloud

        self.socket = context.socket(zmq.PULL)
        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.connect(worker_url)

        self.save_path = save_path

        self._print('Spawned!')

    def _print(self, msg):
        print '{} - {}'.format(self.name, msg)

    def run(self):
        while True:
            try:
                s = self.socket.recv()
            except zmq.ZMQError:
                self.socket.close()
                break

            self._print('Handling the job...')
            self._print(s)

            args = s.split(':')
            getattr(self, args[0])(args[1])

    def save(self, _id):
        asset = self.db.assets.find_one({'_id': ObjectId(_id)})
        self._print(asset)
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

        os.rmdir(os.path.join(self.save_path, directory))

        self.db.assets.update(
            {'_id': ObjectId(_id)},
            {'$set': {'url': url, 'thumbnail_url': thumb_url}}
        )

    def delete(self, _id):
        raise NotImplementedError


if __name__ == '__main__':
    main()
