#Keys:
VERTICES_KEY = 'verts'
FACES_KEY = 'faces'
NORMALS_KEY = 'normals'
TRI_ID_KEY = 'tri_ids'
NAME_KEY = 'name'
RAW_NAME_KEY = 'raw_name'
TRANSFORM_KEY = 'transform'
TRANSLATION_KEY = 'translation'
LOCATION_KEY = 'location'
ROTATION_KEY = 'rotation'
SCALE_KEY = 'scale'
PIVOT_KEY = 'pivot'
SIZE_KEY = 'size'
POINTS_KEY = 'points'
PIVOT_OFFSET_KEY = 'pivot_offset'
ASSET_PATH_KEY = 'asset_path'
GROUP_KEY = 'group'
PARENT_NAME_KEY = 'parent_name'
IS_GROUP_KEY = 'is_group'
ART_ASSET_PATH_KEY = 'art_asset_path'

VACATE_MESSAGE = 'promethean_vacate_socket'

NO_PARENT = 'no_parent'

#Blender Constants:
RBD_PASSIVE = 'PASSIVE'
RBD_ACTIVE = 'ACTIVE'
FINISHED = 'FINISHED'
PASS_THROUGH = 'PASS_THROUGH'
RUNNING_MODAL = 'RUNNING_MODAL'
EVENT_TIMER = 'TIMER'
PLAIN_AXES = 'PLAIN_AXES'
OBJ_TYPE_EMPTY = 'EMPTY'

#IDs:       note: Changing these IDs will require changes in other parts of the code where the id is called
DRAG_DROP_MODAL_ID = "wm.promethean_dragdrop_modal"
SERVER_MESSAGE_MODAL_ID = "wm.promethean_check_for_messages"
BEGIN_SERVER_OPERATOR_ID = "promethean.begin_server"
KILL_SERVER_OPERATOR_ID = "promethean.kill_server"
#Names:
RBD_GROUP_NAME = "Promethean Rigid Bodies"
DRAG_DROP_MODAL_NAME = "Promethean Drag Drop Modal"
SERVER_MESSAGE_MODAL_NAME = "Promethean Check For Messages"
BEGIN_SERVER_NAME = "Connect"
KILL_SERVER_NAME = "Disconnect"

DEFAULT_STATIC_NODE_NAMES = ['floor', 'terrain']

KILL_STR = '__kill__'

#UI Messages
PROMETHEAN_SERVER_NOT_RUNNING = "Promethean Server not Running..."
PROMETHEAN_SERVER_RUNNING = "Promethean Server Running!"
PROMETHEAN_SERVER_STATUS_DISCONNECTED = "Disconnected"
PROMETHEAN_SERVER_STATUS_CONNECTED = "Connected"

#Prefix and Suffix for finding responses in console responses
PROMETHEAN_MESSAGE_PREFIX = "<BEGIN_PROMETHEAN_RESPONSE>"
PROMETHEAN_MESSAGE_SUFFIX = "<END_PROMETHEAN_RESPONSE>"