'''
Script Name: Find A Point
Script Version: 1.0
Flame Version: 2021.1
Written by: Michael Vaglienty - michael@slaytan.net
Creation Date: 06.17.21
Update Date: 06.17.21

Custom Action Type: Action

Description:

    Creates nodes to Find A Point in 3d space of a 3d tracked scene as presented by
    Kirk Balden on Logik Live.

    Right-click in Action -> Create... -> Find A Point

    A copy of the Action result camera locked to the current frame will be created.
    Linked to it will be an axis node called x_y_axis. Manually position this axis in
    x and y to the desired location. Move to another frame then using the z_axis node,
    position the axis to the same location in z space.

    This new axis should now track with the object through 3d space.

To install:

    Copy script into /opt/Autodesk/shared/python/find_a_point
'''

from __future__ import print_function
import os

VERSION = 'v1.0'

SCRIPT_PATH = '/opt/Autodesk/shared/python/find_a_point'

class FindAPoint(object):

    def __init__(self, selection):

        print ('\n', '>' * 20, 'find a point %s' % VERSION, '<' * 20, '\n')

        # Set paths

        self.temp_path = os.path.join(SCRIPT_PATH, 'temp')

        if not os.path.isdir(self.temp_path):
            os.makedirs(self.temp_path)

        # Init variables

        self.action_node_name = ''
        self.action_node = ''
        self.action_filename = ''
        self.save_action_path = ''
        self.camera_parent_name = ''

        self.create_find_a_point()

    def find_line(self, item):

        with open(self.action_filename, 'r') as action_file:
            for num, line in enumerate(action_file, 1):
                if item in line:
                    item_line = num
                    return item_line

    def get_line_value(self, line_number):

        with open(self.action_filename, 'r') as action_file:
            for num, line in enumerate(action_file, 1):
                if num == line_number:
                    item_value = line.rsplit(' ', 1)[1]
                    return item_value

    #--------------------------------------------#

    def get_result_camera(self):
        import flame

        def find_parent(child_num):

            action_file = open(self.action_filename)
            lines = action_file.readlines()
            name_line = lines[child_num]
            action_file.close()

            if 'Name' in name_line:
                camera_parent_name = name_line.rsplit(' ', 1)[1][:-1]
                if camera_parent_name == 'scene':
                    camera_parent_name = None
                return camera_parent_name
            child_num = child_num - 1
            return find_parent(child_num)

        # Find result camera line

        item_line = self.find_line('ResultCamChannel')

        result_cam_line = item_line + 3
        # print ('result_cam_line:', result_cam_line)

        # Get result camera value

        item_value = self.get_line_value(result_cam_line)

        result_camera_num = int(item_value) + 1

        # Get list of all camera names in action node

        action_camera_list = ['null camera'] + [node for node in self.action_node.nodes if 'Camera' in node.type]
        # print ('action_camera_list:', action_camera_list)

        if len(action_camera_list) == 2:
            result_camera_num = 1

        # Get action result camera

        result_cam = action_camera_list[result_camera_num]
        result_cam_name = str(result_cam.name)[1:-1]

        if result_cam_name != 'DefaultCam':
            result_camera_num = result_camera_num# + 1

            result_cam = action_camera_list[result_camera_num]
            result_cam_name = str(result_cam.name)[1:-1]

        # Get result camera node number for action file to search for node camera is parented to

        item_line = self.find_line(result_cam_name)
        result_cam_number_line = item_line + 1
        # print ('result_cam_number_line:', result_cam_number_line)

        # Get name of node camera is parented to if it has a parent

        result_cam_number = self.get_line_value(result_cam_number_line)
        # print ('result_cam_number:', result_cam_number)

        result_cam_child_num = 'Child ' + result_cam_number
        # print ('result_cam_child_num:', result_cam_child_num)

        child_num = self.find_line(result_cam_child_num)
        # print ('child_num:', child_num)

        if child_num == None:
            self.camera_parent_name = None
        else:
            # Get name of node parented to camera node

            self.camera_parent_name = find_parent(child_num)

    def create_cur_frame_camera(self):
        import flame

        # Get name for new camera

        self.new_camera_name = self.name_node('camera_fr')

        # Create new camera at current frame

        flame.execute_shortcut('Result View')
        flame.execute_shortcut('Action Create Camera at Camera Position')
        flame.execute_shortcut('Toggle Node Schematic View')

        # Get list of all 3d camera names in action node

        action_node_values = flame.batch.current_node.get_value()
        action_camera_list = ['null camera'] + [node for node in action_node_values.nodes if 'Camera' in node.type]

        # New camera is last camera in list. Get new camera and new camera index number

        self.new_camera = action_camera_list[-1]
        self.new_camera.name = self.new_camera_name
        self.new_camera_index = len(action_camera_list) - 1

        print ('\n>>> current frame camera created <<<\n')

    def get_action_node(self):
        import flame

        node_type = str(flame.batch.current_node.get_value().type)[1:-1]

        if node_type == 'Action Media':
            node_value = flame.batch.current_node.get_value()
            node_sockets = node_value.sockets
            output_dict = node_sockets.get('output')
            self.action_node_name = output_dict.get('Result')[0]
            self.action_node = flame.batch.get_node(self.action_node_name)
        else:
            self.action_node_name = str(flame.batch.current_node.get_value().name)[1:-1]
            self.action_node = flame.batch.get_node(self.action_node_name)

    def save_action_node(self):
        import flame

        # Set save path for action node

        self.save_action_path = os.path.join(self.temp_path, self.action_node_name)
        # print ('save_action_path:', self.save_action_path)

        # Save action node

        self.action_node.save_node_setup(self.save_action_path)

        # Set Action path and filename variable

        self.action_filename = self.save_action_path + '.action'

    def name_node(self, node_type, node_num=0):
        import flame

        # action_node, action_node_name = get_action_node()

        # Get current frame number

        current_frame = flame.batch.current_frame

        # Get list of existing nodes

        existing_nodes = [str(node.name)[1:-1] for node in flame.batch.current_node.get_value().nodes]

        # Name new node

        node_name = node_type + str(current_frame) + '_' + str(node_num)
        # print ('node_name:', node_name)

        if node_name.endswith('_0'):
            node_name = node_name[:-2]

        # If node name is not in list of existing nodes return node name
        # Otherwise add 1 to node name and try again

        if node_name not in existing_nodes:
            new_node_name = node_name
            # print ('new_node_name:', new_node_name)
            return new_node_name

        node_num = node_num + 1
        return self.name_node(node_type, node_num)

    #--------------------------------------------#

    def create_find_a_point(self):
        import shutil
        import flame

        # Get action node

        self.get_action_node()

        # Save action node

        self.save_action_node()

        # Get result camera

        self.get_result_camera()

        # Create camera at current frame

        self.create_cur_frame_camera()

        # If result camera has parent, connect new camera to parent

        if self.camera_parent_name != None:
            parent_node = self.action_node.get_node(self.camera_parent_name)
            child_node = self.action_node.get_node(self.new_camera_name)
            self.action_node.connect_nodes(parent_node, child_node, link_type='Default')

        # Create x_y axis node

        x_y_axis_node = self.action_node.create_node('Axis')
        x_y_axis_node.name = self.name_node('x_y_axis')
        # print ('x_y_axis_node_name:', x_y_axis_node.name)

        z_axis_node = self.action_node.create_node('Axis')
        z_axis_node.name = self.name_node('z_axis')
        # print ('z_axis_node_name:', z_axis_node.name)

        print ('>>> axis nodes created <<<')

        # Connect nodes

        self.action_node.connect_nodes(x_y_axis_node, self.new_camera, link_type = 'look at')
        self.action_node.connect_nodes(x_y_axis_node, z_axis_node)

        # Get cursor Position

        self.cursor_position = self.action_node.cursor_position

        # Position nodes

        self.new_camera.pos_x = self.cursor_position[0]
        self.new_camera.pos_y = self.cursor_position[1]

        x_y_axis_node.pos_x = self.cursor_position[0]
        x_y_axis_node.pos_y = self.cursor_position[1] - 150

        z_axis_node.pos_x = self.cursor_position[0]
        z_axis_node.pos_y = self.cursor_position[1] - 300

        # Remove temp action save folder

        shutil.rmtree(self.temp_path)

        print ('\n>>> created nodes to find a point <<<\n')

def get_action_custom_ui_actions():

    return [
        {
            'name': 'Create...',
            'actions': [
                {
                    'name': 'Find A Point',
                    'execute': FindAPoint,
                    'minimumVersion': '2021.1'
                }
            ]
        }
    ]
