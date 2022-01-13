import sys
import os
import subprocess
from PyQt5 import QtWidgets, QtGui, QtCore
import re
import threading

class OpenVpnUi(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.main_layout = QtWidgets.QVBoxLayout()
        self.browse_config_layout = QtWidgets.QHBoxLayout()
        self.login_password_layout = QtWidgets.QHBoxLayout()
        self.path_to_config_le = QtWidgets.QLineEdit("Path to vpn configs", returnPressed=self.list_config_files)
        self.browse_button = QtWidgets.QPushButton("Browse", clicked=self.get_select_path)
        self.config_files_list_widget = QtWidgets.QListWidget(itemClicked=self.get_ping_on_location_threaded)
        self.login_id_le = QtWidgets.QLineEdit("Login")
        self.password_le = QtWidgets.QLineEdit("Password")
        self.ping_button = QtWidgets.QPushButton("Ping all locations", clicked=self.ping_all_locations)
        self.sort_asc_cb = QtWidgets.QCheckBox("Sort Ascending", checked=True, stateChanged=lambda x:self.config_files_list_widget.sortItems(not x))
        self.connect_button = QtWidgets.QPushButton("Connect", clicked=self.validate_and_connect)

        # self.sort_asc_cb.

        self.browse_config_layout.addWidget(self.path_to_config_le)
        self.browse_config_layout.addWidget(self.browse_button)
        self.main_layout.addLayout(self.browse_config_layout)
        self.main_layout.addWidget(self.config_files_list_widget)
        self.login_password_layout.addWidget(self.login_id_le)
        self.login_password_layout.addWidget(self.password_le)
        self.main_layout.addLayout(self.login_password_layout)
        self.main_layout.addWidget(self.ping_button)
        self.main_layout.addWidget(self.sort_asc_cb)
        self.main_layout.addWidget(self.connect_button)

        self.setLayout(self.main_layout)


    def get_select_path(self, silent=False):
        if not silent:
            directory = QtWidgets.QFileDialog(self).getExistingDirectory()
        else:
            directory = self.path_to_config_le.text()

        if directory and os.path.exists(directory):
            self.path_to_config_le.setText(directory)
            self.list_config_files()


    def list_config_files(self):
        directory = self.path_to_config_le.text()
        if directory and os.path.exists(directory):
            self.config_files_list_widget.clear()
            all_config_files = [os.path.join(directory, i) for i in os.listdir(directory) if os.path.splitext(i)[-1] == ".ovpn"]
            for config_file in all_config_files:
                item = QtWidgets.QListWidgetItem()
                item.full_path = config_file
                item.name = os.path.basename(config_file)
                item.protocol = 'udp' if 'udp' in item.name else "tcp"
                item.ping = 0
                item.setText(f"{item.ping} - {item.name.split('.prod')[0]}")
                QtWidgets.QApplication.processEvents()
                self.config_files_list_widget.addItem(item)
                QtWidgets.QApplication.processEvents()
        
    def get_ping_of_location(self, current_selection=None):
        if not current_selection:
            current_selection = self.config_files_list_widget.currentItem()
        if current_selection:
            remote = current_selection.name.split(f'_{current_selection.protocol}')[0]
            try:
                process = subprocess.Popen(["ping", "-c", "1", remote], stdout=subprocess.PIPE)
                output = str(process.communicate()[0])
                val = re.search("time=[\d]+", output)
                if val:
                    ping = int(val.group().split("=")[-1])
                    current_selection.ping = ping
                    current_selection.setText(f"{ping} - {current_selection.name.split('.prod')[0]}")
            except Exception as e:
                print (e)
            
    def get_ping_on_location_threaded(self):
        t = threading.Thread(target=self.get_ping_of_location, args=())
        t.start()

    def ping_all_locations(self):
        for i in range(self.config_files_list_widget.count()):
            lwi = self.config_files_list_widget.item(i)
            t = threading.Thread(target=self.get_ping_of_location, args=(lwi,))
            t.start()

    def validate_and_connect(self):
        current_selection = self.config_files_list_widget.currentItem()
        login = self.login_id_le.text()
        password = self.password_le.text()
        if current_selection and login and password:
            temp_file = os.path.join(os.path.expanduser("~"), "sys_var_conf_cache_meta")
            with open(temp_file, "w") as writer:
                writer.write(login+"\n")
                writer.write(password)
            try:
                subprocess.call(["sudo", "openvpn", "--config", current_selection.full_path, "--auth-user-pass", temp_file])
            except Exception as e:
                print (e)


def main():
    app = QtWidgets.QApplication(sys.argv)
    Ui = OpenVpnUi()
    Ui.show()
    app.exec_()

main()