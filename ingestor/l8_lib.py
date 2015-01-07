
def parse_scene(scene_root):
    """returns (sensor, path, row)"""

    # Root looks like 'LC80010082013237LGN00'

    assert scene_root[0] == 'L'
    assert len(scene_root) == 21

    return (scene_root[0:3], scene_root[3:6], scene_root[6:9])
