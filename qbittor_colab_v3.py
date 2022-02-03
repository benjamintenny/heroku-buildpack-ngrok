import os
from sys import exit as sys_exit
from time import sleep, time, strftime
from json import loads, dump
from qbittorrent_local import Client
from setup_qbittor import SetupQbittor
#import libtorrent
import my_variables

platform = my_variables.platform

class Main():
    def __init__(self):
        self.path = my_variables.work_directory
        self.drive_path = my_variables.drive_path
        self.download_path = my_variables.download_path
        self.max_size = 20*1024*1024*1024
        # SETUP FIRST THINGS
        setup = SetupQbittor()
        setup.start()
        self.qb = setup.qb
        self.torrents_dict = setup.torrents_dict
        print(self.torrents_dict)
        self.downed_txt = setup.downed_txt
        #self.start()

    def start(self):
        self.add_torrents()
        self.wait_downloads()

    def add_torrents(self):
        self.added_files = []
        space_in_use = self.space_in_use()
        is_full = False
        files_to_download = {}
        #{'b46f86df69e6f3a69de70949f6409a08c7c2988b': {'torrent_name': 'Canvas 2 Ni Ji Iro no Sketch Creditless OP ED DVD.torrent', 'files': [{'file_name': 'canvas2op.zip', 'file_size': 38971202, 'index': 0}]}, 'after_downloaded_run': None}
        for hash_string in self.torrents_dict:
            #print(self.torrents_dict)
            files = self.torrents_dict[hash_string]["files"]
            #print("FILES:", files)
            for file_dict in files:
                file_name = file_dict["file_name"]
                line = hash_string + "_-_" + file_name
                if line not in self.downed_txt and line not in self.added_files:
                    file_size = int(file_dict["file_size"])
                    # CHECK IF WE ADD THIS WILL IT PASS THE MAX SIZE
                    if space_in_use + file_size <= self.max_size:
                        if hash_string not in files_to_download:
                            files_to_download[hash_string] = []

                        files_to_download[hash_string].append(file_dict)
                        space_in_use = space_in_use + file_size
                    else:
                        is_full = True
                        break
            if is_full:
                break

        self.download_torrent(files_to_download)

    def space_in_use(self):
        torrents = self.qb.torrents()
        hash_list = []
        for torrent in torrents:
            hash_string = str(torrent["hash"])
            hash_list.append(hash_string)

        total = 0
        for hash_string in hash_list:
            files_info = self.qb.get_torrent_files(hash_string)
            for file_info in files_info:
                file_priority = str(file_info["priority"])
                if file_priority == "1":
                    file_name = str(file_info["name"]).strip()
                    file_size = int(file_info["size"])
                    total = total + file_size
                    ### IF TORRENT ADDED BEFORE AND FILE NOT IN 'self.added_files' ###
                    line = hash_string + "_-_" + file_name
                    if line not in self.added_files:
                        self.added_files.append(line)
                    ####################################################################

        return total

    def download_torrent(self, files_to_download):
        torrents = self.qb.torrents()
        hash_list = []
        for torrent in torrents:
            hash_string = str(torrent["hash"])
            hash_list.append(hash_string)

        for hash_string in files_to_download:
            # IF THIS TORRENT NOT IN 'qb.torrents()',
            if hash_string not in hash_list:
                # WE HAVE TO ADD TORRENT
                torrent_file = self.drive_path + self.torrents_dict[hash_string]["torrent_name"]
                torrent_file = open(torrent_file, "rb")
                self.qb.download_from_file(torrent_file)
                sleep(4)
                # AND SET ALL ITS FILES PRIORITY TO 0
                self.priority_to_zero(hash_string)

            # ALL PRIORITY IS 0 AND RESUMING WON'T BE BAD
            print("Resuming:", hash_string)
            self.qb.resume(hash_string)

            # SET PRIORITY OF FILES WE WANT TO 1
            for file_dict in files_to_download[hash_string]:
                index = file_dict["index"]
                file_name = file_dict["file_name"]
                self.qb.set_file_priority(hash_string, index, 1)
                print(file_name, "has", index, "index priority set to 1")
                sleep(1)
                self.added_files.append(hash_string + "_-_" + file_name)

    # SET A TORRENTS ALL FILES PRIORITY TO ZERO
    def priority_to_zero(self, hash_string):
        file_count = len(self.qb.get_torrent_files(hash_string))
        file_id_list = [i for i in range(file_count)]
        #print(file_id_list)
        self.qb.set_multi_file_priority(hash_string, file_id_list, 0)
        sleep(5)
        # CHECK IF ALL FILES PRIORITY SUCCESSFULLY SET TO 0(zero)
        for file_info in self.qb.get_torrent_files(hash_string):
            priority = str(file_info["priority"])
            if priority == "0":
                pass
            else:
                file_name = str(file_info["name"])
                print(file_name, "PRIORITY NOT 0", file_info)
                sys.exit()

        print("All priorities set to zero for: ", self.torrents_dict[hash_string]["torrent_name"])

    def wait_downloads(self):
        while len(self.qb.torrents()) > 0:
            print("Sleeping...")
            sleep(20)
            self.check_download()

    def check_download(self):
        self.check_overly()

    def check_overly(self):
        for torrent in self.qb.torrents():
            progress = torrent["progress"]
            if progress == 1:
                hash_string = torrent["hash"]
                if hash_string in self.torrents_dict:
                    response = self.check_by_files(hash_string)
                    if response:
                        self.complete(hash_string)
                    else:
                        pass #??

    def check_by_files(self, hash_string):
        progress_1_files = {}
        for file in self.qb.get_torrent_files(hash_string):
            print("FILE:", file)
            progress = file["progress"]
            if progress == 1:
                name = file["name"]
                print(name, "progress 1")
                progress_1_files[name] = file

        selected_files = self.torrents_dict[hash_string]["files"]
        for file_dict in selected_files:
            file_name = file_dict["file_name"]
            if file_name not in progress_1_files:
                print("Check by file failed for: ", progress_1_files[file_name])
                return False

        return True

    def complete(self, hash_string):
        on_complete = self.torrents_dict["on_complete"]
        if on_complete:
            pass
        else:
            files = self.qb.get_torrent_files(hash_string)
            for file in files:
                name = file["name"]
                progress = file["progress"]
                if progress == 1 and name in self.added_files:
                    file_name = name.split("/")[-1]
                    file_path_and_name = save_path + name
                    upt_upload(file_name, file_path_and_name)
                    line = hash_string + "_-_" + file_name
                    mongo_qbittor.insert_new_downed_video(line)
                    self.downed_txt = self.downed_txt + "\n" + line

m = Main()
m.start()
