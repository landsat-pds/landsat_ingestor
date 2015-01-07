import hashlib
import md5

def parse_scene(scene_root):
    """returns (sensor, path, row)"""

    # Root looks like 'LC80010082013237LGN00'

    assert scene_root[0] == 'L'
    assert len(scene_root) == 21

    return (scene_root[0:3], scene_root[3:6], scene_root[6:9])

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

