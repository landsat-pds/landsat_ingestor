
import hashlib
import md5


def parse_scene(scene_root):
    """
    Returns (sensor, path, row) based on either an entity id (e.g. LC80410342017032LGN01)
    or a product id (e.g. LC08_L1TP_041034_20170201_20170218_01_T1).
    """

    assert scene_root[0] == 'L'

    if (len(scene_root) == 21):
        sensor = scene_root[0:3]
        path = scene_root[3:6]
        row = scene_root[6:9]
    elif (len(scene_root) == 40):
        sensor = scene_root[0:4]
        path = scene_root[10:13]
        row = scene_root[13:16]
    else:
        raise Exception("This does not appear to be a Landsat 8 identifier.")

    return (sensor, path, row)


def is_entity_id(scene_root):
    return True if len(scene_root) == 21 else False


def get_file_md5sum(filename):
    """Compute MD5Sum of a file.

    :param fileid: Either a filename or a File object.

    :returns: md5sum in 32 character hexdigest format.
    """

    fd = open(filename)
    md5 = hashlib.md5()
    for chunk in iter(lambda: fd.read(8192), b''):
        md5.update(chunk)
    return md5.hexdigest()