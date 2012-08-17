from pyramid.view import (
    view_config,
    view_defaults,
    notfound_view_config
    )
from pyramid.security import authenticated_userid
from pyramid.httpexceptions import HTTPNotAcceptable

from bson import ObjectId

import os


@view_defaults(route_name='rest_asset', renderer='json')
class RESTAssetView(object):
    def __init__(self, request):
        self.request = request

    @view_config(request_method='DELETE')
    def delete(self):
        _id = self.request.context.get('_id')
        self.request.upload_queue.send('delete:' + str(_id))
        return {'result': 'done'}

    @view_config(request_method='PUT')
    def put(self):
        if not self.request.context:
            self.request.status = '404'
            return {}
        try:
            kwargs = self.request.json_body
        except ValueError:
            # If we get a value error, the request didn't have a json body
            # Ignore the request
            return HTTPNotAcceptable()
        update = {}

        if not kwargs.pop('_id', None):
            # Internal Server Error
            self.request.status = '500'
            return {}
        update['title'] = kwargs.pop('title')
        update['tags'] = kwargs.pop('tags')

        asset = self.request.context
        asset.update(update)
        _id = asset.get('_id')
        # We can't update the mongo ObjectId so pop it
        asset.pop('_id')
        asset.pop('id')

        self.request.context = self.request.db.assets.find_and_modify(
            query={'_id': ObjectId(_id)},
            update={'$set': asset},
            upsert=True,
            safe=True
        )

        self.request.response.status = '200'
        return {}


@view_defaults(route_name='rest_assets', renderer='json')
class RESTAssetsView(object):
    def __init__(self, request):
        self.request = request

    @view_config(request_method='POST')
    def post(self):
        request = self.request
        print request.session
        if not authenticated_userid(request):
            return {'result': 'error', 'why': 'diaf'}

        post_param = dict(request.POST)
        print post_param

        file_path = post_param.get('path')
        settings = request.registry.settings['assets']

        if file_path and file_path.startswith(settings['tmp_path']):
            try:
                save_results = request.imager.process(file_path)
            except [IOError, TypeError]:
                # When the image format isn't supported by pil an IOError is raised
                # TypeError is raised when the image doesn't match our whitelist
                return {'result': 'error', 'why': 'image format not supported'}
            finally:
                os.unlink(file_path)

            # TODO: Might be unnecessary?
            if len(save_results) == 0:
                return {'result': 'error', 'why': 'filetype not allowed'}

            r = save_results

            data = dict(
                size=r.get('size'),
                name=r.get('name'),
                delete_url='/api/assets/{}'.format(r.get('id')),
                delete_type='DELETE',
                type=r.get('type'),
                format=r.get('format'),
                desc='This is an image',
                id=r.get('id'),
                status='local'
            )

            frames = r.get('frames')
            if frames:
                data['frames'] = frames

            #if settings['store_locally']:
            resource_uri = settings['resource_uri']
            dir_name = r.get('name').rsplit('.', 1)[0]
            #api_url = '/api/assets/{}'.format(r.get('id'))
            data['url'] = (resource_uri +
                '/{directory}/{full}').format(
                directory=dir_name,
                full=r.get('full')
                )

            data['thumbnail_url'] = (resource_uri +
                '/{directory}/{thumb}').format(
                directory=dir_name,
                thumb=r.get('thumb')
                )

            _id = request.db.assets.insert(data, safe=True)

            # The _id gets added into the response dictionary when mongo inserts
            # the res into the collection. Remove them since we don't want them
            # in our response but send them to upload_queue to be processed
            if not settings['store_locally']:
                request.upload_queue.send('save:' + str(_id))

        del data['_id']
        return [data]


@notfound_view_config(append_slash=True, renderer='404.mako')
def notfound(request):
    request.response.status = '404'
    return {}
