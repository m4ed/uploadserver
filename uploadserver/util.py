from PIL import Image
import os
import string

BASE_LIST = string.digits + string.letters
BASE_DICT = dict((c, i) for i, c in enumerate(BASE_LIST))


class Base62(object):
    """ A simple base 62 encode/decoder

        Used to generate IDs in base 62 for shorter api urls """

    def __init__(self, val=None):
        if not val:
            self.base10_val = 0
            self.val = "0"
        elif (isinstance(val, int)):
            self.base10_val = val
            self.val = self._encode(val)
        elif (isinstance(val, str)):
            self.base10_val = self._decode(val)
            self.val = val
        else:
            raise TypeError('Valid input types are string or int')

    def _decode(self, strng, reverse_base=BASE_DICT):
        length = len(reverse_base)
        res = 0
        for i, c in enumerate(strng[::-1]):
            res += (length ** i) * reverse_base[c]

        return res

    def _encode(self, integer, base=BASE_LIST):
        length = len(base)
        res = ''
        while integer != 0:
            res = base[integer % length] + res
            integer /= length
        return res

    def increment(self):
        return self._add(1)

    def _add(self, val):
        if isinstance(val, str):
            val = self._decode(val)
        self.base10_val += val
        self.val = self._encode(self.base10_val)
        return self.val

    def __add__(self, val):
        self._add(val)
        return self

    def __iadd__(self, val):
        self._add(val)
        return self

    def __int__(self):
        return self.base10_val

    def __str__(self):
        return self.val

    def __unicode__(self):
        return self.val


def _iter_frames(im):
    transparent_bg = False

    # Save the palette from first frame for future use
    palette = im.getpalette()
    # Skip the first frame
    current_frame = im.convert('RGBA')
    # Fill the previous buffer in advance for the first loop
    buf = current_frame.load()
    for x in range(current_frame.size[0]):
        for y in range(current_frame.size[1]):
            # Check if the pixel is transparent
            # TODO: Make sure that 0 actually means transparency in all images
            if buf[x, y][3] == 0:
                # If we find a single pixel with transparent alpha channel
                # assume the img has a transparent background
                transparent_bg = True
                break

    # If it looks like there's a static background in the first image,
    # try to preserve it
    if not transparent_bg:
        print 'Treating the gif as having a static background!'
        prev_frame = current_frame
    else:
        print 'Treating the gif as having a transparent background!'

    yield current_frame

    try:
        i = 1
        im.seek(i)

        while True:
            # Fix palette for the current image frame
            im.putpalette(palette)
            current_frame = im.convert('RGBA')
            if not transparent_bg:
                # Image1, Image2, mask => Image
                current_frame = Image.composite(
                    current_frame, prev_frame, mask=current_frame
                    )
                prev_frame = current_frame

            yield current_frame
            i += 1
            im.seek(i)

    except EOFError:
        pass


def _convert_gif(im, output_filename, output_filepath,
        size_s=(128, 128), size_m=(256, 256)):
    #print "WORKING DIR IS ", working_dir
    #infile_path = os.path.join(working_dir, infile)
    #infile_path = infile
    result = []
    for i, frame in enumerate(_iter_frames(im)):
        full_output_path = os.path.join(
            output_filepath, '{index}_{filename}'.format(
                filename=output_filename, index=i))

        result.append(_handle_image(frame, output_filepath, full_output_path, size_s, size_m))

    return result


def _convert_png_jpg(im, output_filename, output_filepath,
        size_s=(128, 128), size_m=(256, 256)):
    full_output_path = os.path.join(
        output_filepath, output_filename)
    return [_handle_image(im, output_filepath, full_output_path, size_s, size_m)]


def _handle_image(im, output_directory, full_output_path, size_s, size_m):
    img_s = im.copy()
    img_m = im.copy()
    img_s.thumbnail(size_s, Image.ANTIALIAS)
    img_m.thumbnail(size_m, Image.ANTIALIAS)

    full_img = full_output_path + '_full.png'
    thumb_small = full_output_path + '_thumb_s.png'
    thumb_medium = full_output_path + '_thumb_m.png'

    img_s.save(thumb_small, format='PNG')
    img_m.save(thumb_medium, format='PNG')
    im.save(full_img, format='PNG')

    return {
        'directory_name': os.path.basename(output_directory),
        'image_name': os.path.basename(full_img),
        'size': os.path.getsize(full_img),
        'full_img': os.path.basename(full_img),
        'thumb_small': os.path.basename(thumb_small),
        'thumb_medium': os.path.basename(thumb_medium)
    }


def process_image(infile):
    working_dir = os.path.dirname(os.path.abspath(__file__))
    output_filename = os.path.basename(infile)
    output_filepath = os.path.join(working_dir, 'static', 'tmp', output_filename)
    if not os.path.exists(output_filepath):
        os.makedirs(output_filepath)
    try:
        im = Image.open(infile)
        print im.format
        if im.format == 'GIF':
            return _convert_gif(im, output_filename, output_filepath)
        elif im.format in ['PNG', 'JPEG']:
            return _convert_png_jpg(im, output_filename, output_filepath)
    # FOR TESTING ONLY! REPLACE WITH SOMETHING INTELLIGENT FOR PRODUCTION
    except:
        import traceback
        traceback.print_exc()
        return []

if __name__ == '__main__':
    import timeit
    t = timeit.Timer(
        "convert(infile=str(sys.argv[1]))",
        "from __main__ import convert_gif; import sys"
        )
    passes = 10
    print "{:.2} sec/pass".format(t.timeit(number=passes) / passes)
