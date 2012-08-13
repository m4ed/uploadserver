import cloudfiles

import os


class Cloud(object):

    def __init__(self, **settings):
        #print settings
        #raise SystemExit
        self.service = '_' + settings.pop('service')
        self.username = settings.pop('username')
        self.api_key = settings.pop('api_key')
        self.container_name = settings.pop('container_name')
        self.connpool = None

        self._cloudfiles(self.username, self.api_key)

        if self.connpool:
            print 'Connection to cloud initialized'
            print

    def _cloudfiles(self, username, api_key, servicenet=False):
        self.connpool = cloudfiles.ConnectionPool(
            username, api_key, servicenet=servicenet)
        self.container = self._get_container(self.container_name)
        # Around 50 years
        #self.container.make_public(ttl=60 * 60 * 24 * 365 * 50)

    def _get_connection(self):
        return self.connpool.get()

    def _release_connection(self, connobj):
        self.connpool.put(connobj)

    def _get_container(self, container_name):
        conn = self._get_connection()
        container = conn.get_container(container_name)
        if not container:
            container = conn.create_container(
                container_name, error_on_existing=False)
        self._release_connection(conn)
        return container

    def save(self, path, ssl=False):
        name = os.path.basename(path)
        o = self.container.create_object(name)
        file_extension = name.rsplit('.', 1)[-1]
        print 'Saving the image with file extension image/' + file_extension
        o.content_type = 'image/' + file_extension
        with open(path, 'rb') as f:
            o.write(f)
        if not ssl:
            return o.public_uri()
        else:
            return o.public_ssl_uri()

    def delete(self, *args, **kwargs):
        self.container.delete_object(*args, **kwargs)
