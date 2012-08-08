from pyramid.view import view_config
from .util import process_image, Base62

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
    tmp_path = request.registry.settings['asset_tmp_path']
    print file_path
    print tmp_path
    if file_path and file_path.startswith(tmp_path):
        save_results = process_image(file_path)
        print save_results
        os.unlink(file_path)

        res = []
        for r in save_results:
            o = request.db.counters.find_and_modify(
                query={'_id': 'imgId'},
                update={'$inc': {'c': 1}}
            )
            c = int(o.get('c'))
            _id = str(Base62(c))
            # {"src": "http://placehold.it/150x100",
            # "title": "Placeholder image 1",
            # "_id": "5018cfe938d57a56b900000b",
            # "type": "image",
            # "id": "1",
            # "desc": "Description of asset 1"}
            res.append(dict(
                size=r.get('size'),
                name=r.get('image_name'),
                url=('http://127.0.0.1:8080'
                '/static/tmp/{directory}/{full}').format(
                    directory=r.get('directory_name'),
                    full=r.get('full_img')
                ),
                thumbnail_url=('http://127.0.0.1:8080'
                '/static/tmp/{directory}/{thumb}').format(
                    directory=r.get('directory_name'),
                    thumb=r.get('thumb_small')
                ),
                delete_url='',
                delete_type='',
                type='image',
                desc='This is an image',
                id=_id
            ))

        request.db.assets.insert(res)
        #success = True
    # "name":"picture1.jpg",
    # "size":902604,
    # "url":"\/\/example.org\/files\/picture1.jpg",
    # "thumbnail_url":"\/\/example.org\/thumbnails\/picture1.jpg",
    # "delete_url":"\/\/example.org\/upload-handler?file=picture1.jpg",
    # "delete_type":"DELETE"
    for r in res:
        r['_id'] = str(r['_id'])

    return res
