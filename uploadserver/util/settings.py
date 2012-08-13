from pyramid.path import AssetResolver
# ConfigParser renamed to configparser in python 3.0
import os

try:
    import configparser
except ImportError:
    import ConfigParser as configparser


def no_option_catcher(original_function):
    def catcher(*args, **kwargs):
        try:
            return original_function(*args, **kwargs)
        except configparser.NoOptionError:
            print 'No such option! DO SOMETHING WILL YOU?!'
            return None
    return catcher


@no_option_catcher
def parse_asset_settings(settings):
    config = configparser.ConfigParser()
    r = AssetResolver()
    try:
        s = r.resolve(settings.get('assets.config')).abspath()
        config.read(s)
    except AttributeError:
        try:
            with open(settings) as fp:
                config.readfp(fp)
        except IOError:
            raise

    store_locally = config.getboolean('assets', 'store_locally')
    result = dict(
        store_locally=store_locally,
        tmp_path=r.resolve(config.get('assets', 'tmp_path')).abspath(),
        save_path=r.resolve(config.get('assets', 'save_path')).abspath()
    )
#if (store_locally):
    c = config.items('assets:local')

    for key, value in c:
        # Skip any urls since they don't need to be resolved
        # TODO: Might produce bugs if module name starts with `http`
        if value.startswith('http'):
            result[key] = value
            continue
        try:
            value = r.resolve(value).abspath()
        except ValueError:
            # This gets raised if the name isn't in dotted notation
            pass
        except ImportError:
            # This gets raised if there's ":" in the value but it's not a module
            pass
        finally:
            result[key] = value
    #else:
    c = config.items('assets:cloud')
    result.update(c)

    return result


# def parse_path(path):
#     prefix = 'uploadserver:'
#     if path.startswith(prefix):
#         # This assumes that util.py (this file) is
#         # located in uploadserver directory!
#         # TODO: Fix it
#         working_dir = os.path.dirname(os.path.abspath(__file__))
#         # Slice the prefix
#         p = path[len(prefix):]
#         p = os.path.join(working_dir, p)
#     else:
#         p = path

#     return p
