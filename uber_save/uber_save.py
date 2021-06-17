'''
Script Name: Uber Save
Script Version: 3.0
Flame Version: 2021
Written by: Michael Vaglienty - michael@slaytan.net
Creation Date: 07.28.19
Update Date: 06.08.21

Custom Action Type: Batch / Media Panel

Description:

    Save/Save Iterate batch group and batch setup file to custom path in one click

    Run script setup to set batch setup save path:

    Flame Main Menu -> Uber Save Setup

        Shot Name Type:

            Select: Shot Name when naming shots similar to this: PYT_0100, PYT_100, PYT100
            Select: Batch Group Name when shots are named in an episodic format such as: 100_100_100 or PYT_100_100_100

        Project Root Path:

            The script will always save batch setups into the default project batch folder that is set when creating a project.

            To use an alternate path, click Use Custom Path and select the new path. This path will be used for all projects and should be a root path
            that can then have subfolder defined in the Batch Path entry.

        Batch Path:

            Use this to define the folder structure that batch setups will be saved in. They will be sub folders of the path defined in the Project Root Path.
            This works in a way similar to defining where renders go with the write node.

            Tokens:

                <ProjectName> - Adds name of current Flame Project to path
                <DesktopName> - Adds name of current desktop to path
                <SeqName> - Will try to guess shot seqeunce name from the batch group name - for example: PYT_0100_comp will give a sequence name of PYT
                <SEQNAME> - Will do the same as above but give the sequence name in all caps
                <ShotName> - Will try to guess shot name from the batch group name - for example: PYT_0100_comp will give a shot name of PYT_0100
                <EpisodeNumber> - Will try to give an episode number from the batch group name - Shot Name Type should be set to Batch Group Name when using this
                                  Use with episodic shots named in the 100_100_100 or similar format.
                <JobFolder> - Will attempt to find job folder on server - not sure on the usefulness of this one

    To use:

    Right-click selected batchgroups in desktop -> Uber Save... -> Save Selected Batchgroups
    Right-click selected batchgroups in desktop -> Uber Save... -> Iterate and Save Selected Batchgroups

    Right-click on desktop in media panel -> Uber Save... -> Save All Batchgroups

    Right-click in batch -> Uber Save... -> Save Current Batchgroup
    Right-click in batch -> Uber Save... -> Iterate and Save Current Batchgroup

To install:

    Copy script into either /opt/Autodesk/shared/python/uber_save

Updates:

v3.0 06.08.21

    Updated to be compatible with Flame 2022/Python 3.7

    Improvements to shot name detection

    Speed improvements when saving

v2.0 10.08.20:

    Updated UI

    Improved iteration handling

    Added SEQNAME token to add sequence name in caps to path

v1.91 05.13.20:

    Fixed iterating: When previous iterations were not in batchgroup, new itereations would reset to 1.
    Iterations now continue from current iteration number.

v1.9 03.10.20:

    Fixed Setup UI for Linux

v1.7 12.29.19

    Menu now appears as Uber Save in right-click menu
'''

from __future__ import print_function
import os
import re
import ast
from PySide2 import QtWidgets, QtCore

VERSION = 'v3.0'

SCRIPT_PATH = '/opt/Autodesk/shared/python/uber_save'

#-------------------------------------#

class FlameLabel(QtWidgets.QLabel):
    """
    Custom Qt Flame Label Widget
    Options for normal, label with background color, and label with background color and outline
    """

    def __init__(self, label_name, parent, label_type='normal', *args, **kwargs):
        super(FlameLabel, self).__init__(*args, **kwargs)

        self.setText(label_name)
        self.setParent(parent)
        self.setMinimumSize(150, 28)
        self.setMaximumHeight(28)
        self.setFocusPolicy(QtCore.Qt.NoFocus)

        # Set label stylesheet based on label_type

        if label_type == 'normal':
            self.setStyleSheet('QLabel {color: #9a9a9a; border-bottom: 1px inset #282828; font: 14px "Discreet"}'
                               'QLabel:disabled {color: #6a6a6a}')
        elif label_type == 'background':
            self.setAlignment(QtCore.Qt.AlignCenter)
            self.setStyleSheet('color: #9a9a9a; background-color: #393939; font: 14px "Discreet"')
        elif label_type == 'outline':
            # self.setAlignment(QtCore.Qt.AlignLeft)
            self.setStyleSheet('color: #9a9a9a; background-color: #212121; border: 1px solid #404040; font: 14px "Discreet"')

class FlameButton(QtWidgets.QPushButton):
    """
    Custom Qt Flame Button Widget
    """

    def __init__(self, button_name, connect, parent, *args, **kwargs):
        super(FlameButton, self).__init__(*args, **kwargs)

        self.setText(button_name)
        self.setParent(parent)
        self.setMinimumSize(QtCore.QSize(150, 28))
        self.setMaximumSize(QtCore.QSize(150, 28))
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.clicked.connect(connect)
        self.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                           'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}'
                           'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

class FlameLineEdit(QtWidgets.QLineEdit):
    """
    Custom Qt Flame Line Edit Widget

    Main window should include this: window.setFocusPolicy(QtCore.Qt.StrongFocus)

    To use:

    line_edit = FlameLineEdit('Some text here', window)
    """

    def __init__(self, text, parent_window, *args, **kwargs):
        super(FlameLineEdit, self).__init__(*args, **kwargs)

        self.setText(text)
        self.setParent(parent_window)
        self.setMinimumHeight(28)
        self.setMinimumWidth(110)
        # self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setStyleSheet('QLineEdit {color: #9a9a9a; background-color: #373e47; selection-color: #262626; selection-background-color: #b8b1a7; font: 14px "Discreet"}'
                           'QLineEdit:focus {background-color: #474e58}'
                           'QLineEdit:disabled {color: #6a6a6a; background-color: #373737}')

class FlamePushButton(QtWidgets.QPushButton):
    """
    Custom Qt Flame Push Button Widget

    To use:

    pushbutton = FlamePushButton(' Button Name', bool, window)
    """

    def __init__(self, button_name, button_checked, parent_window, *args, **kwargs):
        super(FlamePushButton, self).__init__(*args, **kwargs)

        self.setText(button_name)
        self.setParent(parent_window)
        self.setCheckable(True)
        self.setChecked(button_checked)
        self.setMinimumSize(150, 28)
        self.setMaximumSize(150, 28)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setStyleSheet('QPushButton {color: #9a9a9a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .93 #424142, stop: .94 #2e3b48); text-align: left; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14px "Discreet"}'
                           'QPushButton:checked {color: #d9d9d9; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .93 #4f4f4f, stop: .94 #5a7fb4); font: italic; border: 1px inset black; border-bottom: 1px inset #404040; border-right: 1px inset #404040}'
                           'QPushButton:disabled {color: #6a6a6a; background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: .93 #383838, stop: .94 #353535); font: light; border-top: 1px solid #575757; border-bottom: 1px solid #242424; border-right: 1px solid #353535; border-left: 1px solid #353535}'
                           'QToolTip {color: black; background-color: #ffffde; border: black solid 1px}')

class FlamePushButtonMenu(QtWidgets.QPushButton):
    """
    Custom Qt Flame Menu Push Button Widget

    To use:

    push_button_menu_options = ['Item 1', 'Item 2', 'Item 3', 'Item 4']
    menu_push_button = FlamePushButtonMenu('push_button_name', push_button_menu_options, window)

    or

    push_button_menu_options = ['Item 1', 'Item 2', 'Item 3', 'Item 4']
    menu_push_button = FlamePushButtonMenu(push_button_menu_options[0], push_button_menu_options, window)
    """

    def __init__(self, button_name, menu_options, parent_window, *args, **kwargs):
        super(FlamePushButtonMenu, self).__init__(*args, **kwargs)
        from functools import partial

        self.setText(button_name)
        self.setParent(parent_window)
        self.setMinimumHeight(28)
        self.setMinimumWidth(110)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                           'QPushButton:disabled {color: #747474; background-color: #353535; border-top: 1px solid #444444; border-bottom: 1px solid #242424}')

        def create_menu(option):
            self.setText(option)

        pushbutton_menu = QtWidgets.QMenu(parent_window)
        pushbutton_menu.setFocusPolicy(QtCore.Qt.NoFocus)
        pushbutton_menu.setStyleSheet('QMenu {color: #9a9a9a; background-color:#24303d; font: 14px "Discreet"}'
                                      'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')
        for option in menu_options:
            pushbutton_menu.addAction(option, partial(create_menu, option))

        self.setMenu(pushbutton_menu)

class FlameTokenPushButton(QtWidgets.QPushButton):
    """
    Custom Qt Flame Token Push Button Widget

    To use:

    token_dict = {'Token 1': '<Token1>', 'Token2': '<Token2>'}
    token_push_button = FlameTokenPushButton('Add Token', token_dict, token_dest, window)

    token_dict: Key in dictionary is what will show in button menu.
                Value in dictionary is what will be applied to the button destination
    token_dest: Where the Value of the item selected will be applied such as a LineEdit
    """

    def __init__(self, button_name, token_dict, token_dest, parent, *args, **kwargs):
        super(FlameTokenPushButton, self).__init__(*args, **kwargs)

        self.setText(button_name)
        self.setParent(parent)
        self.setMinimumHeight(28)
        self.setMinimumWidth(110)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setStyleSheet('QPushButton {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                           'QPushButton:disabled {color: #6a6a6a}')

        def token_action_menu():
            from functools import partial

            def insert_token(token):
                for key, value in token_dict.items():
                    if key == token:
                        token_name = value
                        token_dest.insert(token_name)

            for key, value in token_dict.items():
                token_menu.addAction(key, partial(insert_token, key))

        token_menu = QtWidgets.QMenu(parent)
        token_menu.setFocusPolicy(QtCore.Qt.NoFocus)
        token_menu.setStyleSheet('QMenu {color: #9a9a9a; background-color: #24303d; font: 14px "Discreet"}'
                                 'QMenu::item:selected {color: #d9d9d9; background-color: #3a4551}')

        self.setMenu(token_menu)

        token_action_menu()

class FlameLineEditFileBrowse(QtWidgets.QLineEdit):
    """
    Custom Qt Flame Clickable Line Edit Widget with File Browser

    To use:

    lineedit = FlameLineEditFileBrowse('some_path', 'Python (*.py)', window)

    file_path: Path browser will open to. If set to root folder (/), browser will open to user home directory
    filter_type: Type of file browser will filter_type for. If set to 'dir', browser will select directory
    """

    clicked = QtCore.Signal()

    def __init__(self, file_path, filter_type, parent, *args, **kwargs):
        super(FlameLineEditFileBrowse, self).__init__(*args, **kwargs)

        self.filter_type = filter_type
        self.file_path = file_path

        self.setText(file_path)
        self.setParent(parent)
        self.setMinimumHeight(28)
        self.setReadOnly(True)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.clicked.connect(self.file_browse)
        self.setStyleSheet('QLineEdit {color: #898989; background-color: #373e47; font: 14px "Discreet"}'
                           'QLineEdit:disabled {color: #6a6a6a; background-color: #373737}')

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.setStyleSheet('QLineEdit {color: #bbbbbb; background-color: #474e58; font: 14px "Discreet"}'
                               'QLineEdit:disabled {color: #6a6a6a; background-color: #373737}')
            self.clicked.emit()
            self.setStyleSheet('QLineEdit {color: #898989; background-color: #373e47; font: 14px "Discreet"}'
                               'QLineEdit:disabled {color: #6a6a6a; background-color: #373737}')
        else:
            super().mousePressEvent(event)

    def file_browse(self):
        from PySide2 import QtWidgets

        file_browser = QtWidgets.QFileDialog()

        # If no path go to user home directory

        if self.file_path == '/':
            self.file_path = os.path.expanduser("~")
        if os.path.isfile(self.file_path):
            self.file_path = self.file_path.rsplit('/', 1)[0]

        file_browser.setDirectory(self.file_path)

        # If filter_type set to dir, open Directory Browser, if anything else, open File Browser

        if self.filter_type == 'dir':
            file_browser.setFileMode(QtWidgets.QFileDialog.Directory)
            if file_browser.exec_():
                self.setText(file_browser.selectedFiles()[0])
        else:
            file_browser.setFileMode(QtWidgets.QFileDialog.ExistingFile) # Change to ExistingFiles to capture many files
            file_browser.setNameFilter(self.filter_type)
            if file_browser.exec_():
                self.setText(file_browser.selectedFiles()[0])

#-------------------------------------#

class UberSave(object):

    def __init__(self, selection):
        import flame

        print ('\n', '>' * 20, ' uber save %s ' % VERSION, '<' * 20, '\n')

        self.selection = selection
        self.iterate = ''
        self.selected_batch = ''
        self.save_path = ''
        self.project_match = ''
        self.job_folder = ''
        self.batch_token_dict = ''

        self.flame_prj_name = flame.project.current_project.project_name
        print ('flame_prj_name:', self.flame_prj_name)

        self.current_project_path = self.get_current_project_path()
        print ('current_project_path:', self.current_project_path)

        # Get config file values
        # -----------------------------------------

        self.config_path = os.path.join(SCRIPT_PATH, 'config')
        self.config_file = os.path.join(self.config_path, 'config')

        self.config_file_check()

        get_config_values = open(self.config_file, 'r')
        values = get_config_values.read().splitlines()

        self.use_custom = ast.literal_eval(values[2])
        self.project_path = values[4]
        self.batch_path = values[6]
        self.shot_name_type = values[8]

        print ('save_custom:', self.use_custom)
        print ('project_path:', self.project_path)
        print ('batch_path:', self.batch_path)
        print ('shot_name_type:', self.shot_name_type, '\n')

        get_config_values.close()

        print ('>>> uber save config loaded <<<\n')

    def config_file_check(self):

        # Check for config file

        if not os.path.isdir(self.config_path):
            print ('config folder does not exist, creating folder and config file.')

            try:
                os.makedirs(self.config_path)
            except:
                message_box('Unable to create script config folder. Check folder permissions.')

        if not os.path.isfile(self.config_file):
            print ('config file does not exist, creating new config file.')

            config_text = []

            config_text.insert(0, 'Setup values for Uber Save script.')
            config_text.insert(1, 'Save Setups to Custom Project')
            config_text.insert(2, 'False')
            config_text.insert(3, 'Project Root Path:')
            config_text.insert(4, '/')
            config_text.insert(5, 'Batch Path:')
            config_text.insert(6, '<ShotName>')
            config_text.insert(7, 'Shot Name Type:')
            config_text.insert(8, 'Batch Group Name')

            out_file = open(self.config_file, 'w')
            for line in config_text:
                print(line, file=out_file)
            out_file.close()

    def get_project_name(self):

        # Get list of project folders from server

        project_folders = os.listdir(self.project_path)
        project_folders.sort()
        # print ('project_folders: ', project_folders)

        # Remove underscores from current project name

        current_project = self.flame_prj_name
        current_project = current_project.replace('_', ' ')
        #print 'current_project: ', current_project

        # Create list from words in current project name

        current_project_split_list = current_project.split()
        #print 'current_project_split_list: ', current_project_split_list

        # Remove underscores from job folder names

        new_project_folder_list = []

        for folder in project_folders:
            new_folder = folder.replace('_', ' ')
            new_project_folder_list.append(new_folder)

        # Find match if current project and folder name match

        if current_project in new_project_folder_list:
            #print 'CURRENT PROJECT MATCH: ', current_project
            self.project_match = current_project.replace(' ', '_')
            return self.project_match

        # If match not found compare project and folder names to find closest match

        match_list = []

        for word in current_project_split_list:
            for folder in new_project_folder_list:
                find_string = re.search(r'\b%s\b' % word, folder)
                if find_string != None:
                    match_list.append(folder)

        words_matched_list = []
        match_dict = {}

        for item in match_list:
            if item not in words_matched_list:
                match_count = match_list.count(item)
                words_matched_list.append(item)
                match_dict.update({item: match_count})

        # If match list is not empty, match to project

        if match_dict != {}:

            # Match to prject name that shows up the most in the list

            self.project_match = max(match_dict.items(), key=lambda k: k[1])
            self.project_match = self.project_match[0]
            self.project_match = self.project_match.replace(' ', '_')
            #print 'Project Match: ', self.project_match

            return self.project_match

    def get_current_project_path(self):

        # Get default save path from project.db file

        with open('/opt/Autodesk/project/project.db', 'r') as project_db:
            for line in project_db:
                if ':' + self.flame_prj_name + '=' in line:
                    current_project_path = re.search('SetupDir="(.*)",Partition', line)
                    current_project_path = current_project_path.group(1)

                    # If default project is on local drive add autodesk project folder to path

                    if not current_project_path.startswith('/'):
                        current_project_path = os.path.join('/opt/Autodesk/project', current_project_path)
                    return current_project_path

    def translate_path(self):
        import flame
        import re

        def get_job_folder():
            job_root_folder = self.save_path.rsplit('<JobFolder>', 1)[0]
            print ('job_root_folder:', job_root_folder)
            root_folder_list = os.listdir(job_root_folder)
            print ('root_folder_list:', root_folder_list)

            for n in root_folder_list:
                folder_match = re.search(seq_name, n, re.I)
                if folder_match:
                    self.job_folder = n
                    print ('job_folder:', self.job_folder)

        # If Use Custom button is selected use custom path provided
        # Otherwise use project default batch folder

        if self.use_custom:
            self.save_path = os.path.join(self.project_path, self.batch_path)
        else:
            batch_folder = os.path.join(self.current_project_path, 'batch/flame')
            if not os.path.isdir(batch_folder):
                os.makedirs(batch_folder)
            self.save_path = os.path.join(batch_folder, self.batch_path)
        print ('save_path:', self.save_path)

        #-------------------------------------#

        # Set path translate variables

        self.get_project_name()

        batch_name = str(self.selected_batch.name)[1:-1]
        print ('batch_name:', batch_name)

        try:
            if self.shot_name_type == 'Shot Name':
                shot_name_split = re.split(r'(\d+)', batch_name)
                shot_name_split = [s for s in shot_name_split if s != '']
                # print ('shot_name_split:', shot_name_split)

                if shot_name_split[1].isalnum():
                    shot_name = shot_name_split[0] + shot_name_split[1]
                else:
                    shot_name = shot_name_split[0] + shot_name_split[1] + shot_name_split[2]

                # Get sequence name from first split

                seq_name = shot_name_split[0]
                if seq_name.endswith('_'):
                    seq_name = seq_name[:-1]

            else:
                seq_name_split = re.split(r'(\d+)', shot_name)

                seq_name = seq_name_split[0]
                if seq_name.endswith('_'):
                    seq_name = seq_name[:-1]
        except:
            shot_name = batch_name
            seq_name = ''

        print ('shot_name:', shot_name)
        print ('seq_name:', seq_name)

        desktop_name = str(flame.projects.current_project.current_workspace.desktop.name)[1:-1]

        #-------------------------------------#

        print ('path_to_translate:', self.save_path)

        # Translate tokens in path

        if '<ProjectName>' in self.save_path:
            self.save_path = re.sub('<ProjectName>', self.project_match, self.save_path)

        if '<SeqName>' in self.save_path:
            self.save_path = re.sub('<SeqName>', seq_name, self.save_path)

        if '<SEQNAME>' in self.save_path:
            self.save_path = re.sub('<SEQNAME>', seq_name.upper(), self.save_path)

        if '<ShotName>' in self.save_path:
            self.save_path = re.sub('<ShotName>', shot_name, self.save_path)

        if '<EpisodeNum>' in self.save_path:
            episode_num_split = re.split(r'(\d+)', shot_name)
            # episode_num_split = filter(None, re.split(r'(\d+)', shot_name))
            episode_num = episode_num_split[1]
            self.save_path = re.sub('<EpisodeNum>', episode_num, self.save_path)

        if '<JobFolder>' in self.save_path:
            get_job_folder()
            self.save_path = re.sub('<JobFolder>', self.job_folder, self.save_path)

        if '<DesktopName>' in self.save_path:
            self.save_path = re.sub('<DesktopName>', desktop_name, self.save_path)

        print ('translated save_path:', self.save_path, '\n')

    def save(self):
        import flame
        import re

        def edit_batch():
            import flame

            batch_file = os.path.join(self.save_path, current_iteration_no_spaces) + '.batch'
            print ('batch_file:', batch_file)

            batch_name = str(self.selected_batch.name)[1:-1]
            print ('batch_name:', batch_name)

            line_insert = '<BatchName>' + batch_name + '</BatchName>'

            with open(batch_file, 'r') as batch:
                for line in batch:
                    if '<BatchName>' in line:
                        line_split01 = line.split('<BatchName>', 1)[0]
                        line_split02 = line.split('</BatchName>', 1)[1]

            new_line = line_split01 + line_insert + line_split02

            replace_line = open(batch_file, 'w')

            replace_line.write(new_line)
            replace_line.close()

        selected_batch_name = str(self.selected_batch.name)[1:-1]
        print ('selected_batch_name:', selected_batch_name)

        # Open batch if closed

        self.selected_batch.open()

        # Get current iteration
        iteration_split = (re.split(r'(\d+)', str(self.selected_batch.current_iteration.name)[1:-1]))[1:-1]
        # iteration_split = iteration_split[1:-1]
        # iteration_split = filter(None, re.split(r'(\d+)', str(self.selected_batch.current_iteration.name)[1:-1]))
        current_iteration = int(iteration_split[-1])
        print ('current_iteration:', current_iteration)

        # Get latest iteration if iterations are saved
        print ('selected_batch.batch_iterations:', self.selected_batch.batch_iterations)

        if not self.selected_batch.batch_iterations == []:
            print (str([i.name for i in self.selected_batch.batch_iterations][-1])[1:-1])
            # print (filter(None, re.split(r'(\d+)', str([i.name for i in self.selected_batch.batch_iterations][-1])[1:-1])))
            latest_iteration = int(((re.split(r'(\d+)', str([i.name for i in self.selected_batch.batch_iterations][-1])[1:-1]))[1:-1])[-1])

            # latest_iteration = int(filter(None, re.split(r'(\d+)', str([i.name for i in self.selected_batch.batch_iterations][-1])[1:-1]))[-1])
        else:
            latest_iteration = current_iteration
        print ('latest_iteration:', latest_iteration)

        # If first save of batch group, create first iteration

        if self.selected_batch.batch_iterations == [] and current_iteration == 1:
            self.iterate = True

        # Iterate up if iterate up menu selected

        print ('iterate:', self.iterate)

        if self.iterate:
            if current_iteration == 1:
                self.selected_batch.iterate()
            elif current_iteration < latest_iteration:
                self.selected_batch.iterate(index = (latest_iteration + 1))
            else:
                self.selected_batch.iterate(index = (current_iteration + 1))
            print ('\n>>> iterating up <<<\n')
        else:
            self.selected_batch.iterate(index=current_iteration)
            print ('\n>>> overwriting existing iteration <<<\n')

        # Get current iteration

        current_iteration = str(self.selected_batch.current_iteration.name)[1:-1]
        current_iteration_no_spaces = current_iteration.replace(' ', '_')
        print ('new current_iteration:', current_iteration)

        # Set batch save path

        shot_save_path = os.path.join(self.save_path, current_iteration)
        print ('shot_save_path:', shot_save_path)

        try:
            # Create shot save folder

            if not os.path.isdir(self.save_path):
                os.makedirs(self.save_path)

            # Hard save current batch iteration

            self.selected_batch.save_setup(shot_save_path)

            # edit_batch()

            print ('\n', '>>> %s uber saved <<<' % selected_batch_name, '\n')

        except:
            message_box('Batch not saved. Check path in setup')

    #-------------------------------------#

    def batchgroup_save_all(self):
        import flame

        self.iterate = False
        batch_groups = flame.project.current_project.current_workspace.desktop.batch_groups

        for self.selected_batch in batch_groups:
            self.translate_path()
            self.save()

        print ('done.\n')

    def batchgroup_save_selected(self):
        import flame

        self.iterate = False

        for self.selected_batch in self.selection:
            self.translate_path()
            self.save()

        print ('done.\n')

    def batchgroup_save_selected_iterate(self):
        import flame

        self.iterate = True

        for self.selected_batch in self.selection:
            self.translate_path()
            self.save()

        print ('done.\n')

    def batchgroup_save(self):
        import flame

        self.iterate = False
        self.selected_batch = flame.batch
        self.translate_path()
        self.save()

        print ('done.\n')

    def batchgroup_save_iterate(self):
        import flame

        self.iterate = True
        self.selected_batch = flame.batch
        self.translate_path()
        self.save()

        print ('done.\n')

    #-------------------------------------#

    def setup(self):

        self.setup_window = QtWidgets.QWidget()
        self.setup_window.setMinimumSize(QtCore.QSize(950, 230))
        self.setup_window.setMaximumSize(QtCore.QSize(950, 230))
        self.setup_window.setWindowTitle('Uber Save Setup %s' % VERSION)
        self.setup_window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setup_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setup_window.setStyleSheet('background-color: #272727')

        # Center window in linux

        resolution = QtWidgets.QDesktopWidget().screenGeometry()
        self.setup_window.move((resolution.width() / 2) - (self.setup_window.frameSize().width() / 2),
                               (resolution.height() / 2) - (self.setup_window.frameSize().height() / 2))

        # Labels

        self.shot_name_label = FlameLabel('Shot Name Type', self.setup_window, label_type='normal')
        self.project_path_label = FlameLabel('Project Root Path', self.setup_window, label_type='normal')
        self.batch_path_label = FlameLabel('Batch Path', self.setup_window, label_type='normal')

        # LineEdits

        self.project_path_lineedit = FlameLineEditFileBrowse(self.project_path, 'dir', self.setup_window)
        self.batch_path_lineedit = FlameLineEdit(self.batch_path, self.setup_window)

        # Shot Name Type Pushbutton Menu

        shot_name_options = ['Shot Name', 'Batch Group Name']
        self.shot_name_type_push_btn = FlamePushButtonMenu(self.shot_name_type, shot_name_options, self.setup_window)

        # Batch Path Token Pushbutton Menu

        self.batch_token_dict = {'Project Name': '<ProjectName>', 'Desktop Name': '<DesktopName>', 'Sequence Name': '<SeqName>', 'SEQUENCE NAME': '<SEQNAME>',
                                 'Shot Name': '<ShotName>', 'Episode Number': '<EpisodeNum>', 'Job Folder': '<JobFolder>'}
        self.batch_token_push_btn = FlameTokenPushButton('Add Token', self.batch_token_dict, self.batch_path_lineedit, self.setup_window)

        # Push Button

        def use_custom_path():
            if self.use_custom_push_btn.isChecked() == True:
                self.project_path_lineedit.setEnabled(True)
            else:
                self.project_path_lineedit.setEnabled(False)
                self.project_path_lineedit.setText(os.path.join(self.current_project_path, 'batch/flame'))

        self.use_custom_push_btn = FlamePushButton(' Use Custom Path', self.use_custom, self.setup_window)
        self.use_custom_push_btn.clicked.connect(use_custom_path)
        use_custom_path()

        #  Buttons

        self.save_btn = FlameButton('Save', self.setup_save, self.setup_window)
        self.cancel_btn = FlameButton('Cancel', self.setup_window.close, self.setup_window)

        # Setup window layout

        gridbox = QtWidgets.QGridLayout()
        gridbox.setMargin(20)

        gridbox.addWidget(self.shot_name_label, 0, 0)
        gridbox.addWidget(self.shot_name_type_push_btn, 0 ,1)

        gridbox.addWidget(self.project_path_label, 1 ,0)
        gridbox.addWidget(self.project_path_lineedit, 1 ,1, 1, 3)
        gridbox.addWidget(self.use_custom_push_btn, 1, 5)

        gridbox.addWidget(self.batch_path_label, 2 ,0)
        gridbox.addWidget(self.batch_path_lineedit, 2 ,1, 1, 3)
        gridbox.addWidget(self.batch_token_push_btn, 2, 5)

        gridbox.setRowStretch(3, 10)

        gridbox.addWidget(self.save_btn, 4, 5)
        gridbox.addWidget(self.cancel_btn, 5, 5)

        self.setup_window.setLayout(gridbox)

        self.setup_window.show()

        return self.setup_window

    def setup_save(self):

            def save_config_file():

                config_text = []

                config_text.insert(0, 'This text files saves setup values for pyFlame Uber Save script.')
                config_text.insert(1, 'Save Setups to Custom Project')
                config_text.insert(2, self.use_custom_push_btn.isChecked())
                config_text.insert(3, 'Project Root Path:')
                config_text.insert(4, self.project_path_lineedit.text())
                config_text.insert(5, 'Batch Path:')
                config_text.insert(6, self.batch_path_lineedit.text())
                config_text.insert(7, 'Shot Name Type:')
                config_text.insert(8, self.shot_name_type_push_btn.text())

                out_file = open(self.config_file, 'w')
                for line in config_text:
                    print(line, file=out_file)
                out_file.close()

                self.setup_window.close()

                print ('\n>>> uber save settings saved <<<\n')

            if self.project_path_lineedit.text() == '':
                message_box('Enter Project Root Path')
            elif self.batch_path_lineedit.text() == '':
                message_box('Enter Batch Path')
            else:
                save_config_file()

            print ('done.\n')

#-------------------------------------#

def message_box(message):

    msg_box = QtWidgets.QMessageBox()
    msg_box.setMinimumSize(400, 100)
    msg_box.setText(message)
    msg_box_button = msg_box.addButton(QtWidgets.QMessageBox.Ok)
    msg_box_button.setFocusPolicy(QtCore.Qt.NoFocus)
    msg_box_button.setMinimumSize(QtCore.QSize(80, 28))
    msg_box.setStyleSheet('QMessageBox {background-color: #313131; font: 14pt "Discreet"}'
                          'QLabel {color: #9a9a9a; font: 14pt "Discreet"}'
                          'QPushButton {color: #9a9a9a; background-color: #424142; border-top: 1px inset #555555; border-bottom: 1px inset black; font: 14pt "Discreet"}'
                          'QPushButton:pressed {color: #d9d9d9; background-color: #4f4f4f; border-top: 1px inset #666666; font: italic}')
    msg_box.exec_()

    code_list = ['<br>', '<dd>']

    for code in code_list:
        message = message.replace(code, '\n')

    print ('\n>>> %s <<<\n' % message)

def uber_save_setup(selection):

    # Opens Uber Save Setup window

    uber_save = UberSave(selection)
    return uber_save.setup()

def uber_batchgroup_save(selection):

    # Saves current batch from batch

    uber_save = UberSave(selection)
    uber_save.batchgroup_save()

def uber_batchgroup_iterate_save(selection):

    # Iterates and saves current batch from batch

    uber_save = UberSave(selection)
    uber_save.batchgroup_save_iterate()

def uber_batchgroup_save_all(selection):

    # Saves all batchgroups in desktop

    uber_save = UberSave(selection)
    uber_save.batchgroup_save_all()

def uber_batchgroup_save_selected(selection):

    # Saves selected batchgroups in desktop

    uber_save = UberSave(selection)
    uber_save.batchgroup_save_selected()

def uber_batchgroup_iterate_save_selected(selection):

    # Saves selected batchgroups in desktop

    uber_save = UberSave(selection)
    uber_save.batchgroup_save_selected_iterate()

# Scopes
#-------------------------------------#

def scope_batch(selection):
    import flame

    for item in selection:
        if isinstance(item, flame.PyBatch):
            return True
    return False

def scope_desktop(selection):
    import flame

    for item in selection:
        if isinstance(item, flame.PyDesktop):
            return True
    return False

# Menus
#-------------------------------------#

def get_media_panel_custom_ui_actions():

    return [
        {
            'name': 'Uber Save',
            'actions': [
                {
                    'name': 'Save All Batchgroups',
                    'isVisible': scope_desktop,
                    'execute': uber_batchgroup_save_all,
                    'minimumVersion': '2021'
                },
                {
                    'name': 'Save Selected Batchgroups',
                    'isVisible': scope_batch,
                    'execute': uber_batchgroup_save_selected,
                    'minimumVersion': '2021'
                },
                {
                    'name': 'Iterate and Save Selected Batchgroups',
                    'isVisible': scope_batch,
                    'execute': uber_batchgroup_iterate_save_selected,
                    'minimumVersion': '2021'
                }
            ]
        }
    ]

def get_batch_custom_ui_actions():

    return [
        {
            'name': 'Uber Save',
            'actions': [
                {
                    'name': 'Save Current Batchgroup',
                    'execute': uber_batchgroup_save,
                    'minimumVersion': '2021'
                },
                {
                    'name': 'Iterate and Save Current Batchgroup',
                    'execute': uber_batchgroup_iterate_save,
                    'minimumVersion': '2021'
                }
            ]
        }
    ]

def get_main_menu_custom_ui_actions():

    return [
        {
            'name': 'pyFlame',
            'actions': [
                {
                    'name': 'Uber Save Setup',
                    'execute': uber_save_setup,
                    'minimumVersion': '2021'
                }
            ]
        }
    ]
