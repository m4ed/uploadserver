from pyramid.view import view_config

import os


@view_config(route_name='home', renderer='index.mako')
def my_view(request):
    return {'project': 'uploadserver'}


@view_config(route_name='upload', renderer='json', request_method='POST')
def upload(request):
    #success = False
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

        if len(save_results) == 0:
            return {'result': 'error', 'why': 'filetype not allowed'}

        r = save_results

        data = dict(
            size=r.get('size'),
            name=r.get('name'),
            delete_url='/api/assets/{}'.format('id'),
            delete_type='DELETE',
            type=r.get('type'),
            format=r.get('format'),
            desc='This is an image',
            id=r.get('id')
        )

        frames = r.get('frames')
        if frames:
            data['frames'] = frames

        #if settings['store_locally']:
        resource_uri = settings['resource_uri']
        dir_name = r.get('name').rsplit('.', 1)[0]
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
        #del r['_id']  # = str(r['_id'])

    return r
