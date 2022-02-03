import os
import libtorrent
import my_variables

class SelectFiles():
    def __init__(self, torrent_file, spec_file=None):
        self.path = my_variables.work_directory
        self.drive_path = my_variables.drive_path
        self.max_file_size = 12*1024*1024*1024
        self.min_file_size = 1*1024*1024
        self.torrent_file = torrent_file
        self.spec_file = spec_file
        self.selected_files = None
        self.after_downloaded_run = None

    def start(self):
        self.downloaded_files()
        if self.spec_file:
            self.spec_dict = self.load_specs()
            self.torrents_dict = self.select_files_to_download()
        else:
            self.torrents_dict = self.all_files_to_download()
        return self.torrents_dict

    def downloaded_files(self):
        downed_txt = self.path + "downed.txt"
        if os.path.exists(downed_txt):
            self.downed_txt = open(downed_txt, "r", encoding="utf-8").read()
        else:
            self.downed_txt = ""

    def all_files_to_download(self):
        info = libtorrent.torrent_info(self.drive_path + self.torrent_file)
        hash_string = str(info.info_hash())
        files = info.files()
        temp_file_dict = {}
        counter = -1
        for file in files:
            counter = counter + 1
            file_name = str(file.path)
            downed_line = hash_string + "_-_" + file_name
            # IF FILE NOT DOWNLOADED
            if downed_line not in self.downed_txt:
                # IF FILESIZE BETWEEN REQUESTED SIZES
                file_size = file.size
                if file_size >= self.min_file_size and file_size <= self.max_file_size:
                    temp_file_dict[downed_line] = {"file_name": file_name, "file_size": file_size, "index": counter}

        # SORT FILES
        temp_list = [key for key in temp_file_dict]
        temp_list.sort()
        torrents_dict = {}
        torrents_dict[hash_string] = {"torrent_name": self.torrent_file, "files": []}
        for key in temp_list:
            torrents_dict[hash_string]["files"].append(temp_file_dict[key])
        torrents_dict[hash_string]["after_downloaded_run"] = self.after_downloaded_run
        return torrents_dict

    def load_specs(self):
        spec_dict = {}
        spec_file = open(self.spec_file, "r", encoding="utf-8").read()
        entries = spec_file.split("*="*5)
        for entry in entries:
            if entry.strip() != "":
                key, value = entry.split("-."*5)
                spec_dict[key.strip()] = value.strip()
        return spec_dict

    def set_spec_keys(self):
        for key, value in self.spec_dict.items():
            if key == "MAX-FILE-SIZE":
                self.max_file_size = self.kb_mb_gb_to_byte(value)
            elif key == "MIN-FILE-SIZE":
                self.min_file_size = self.kb_mb_gb_to_byte(value)
            elif key == "SELECTED-FILES":
                self.selected_files = value.split("\n")
                self.selected_files = [file.strip() for file in self.selected_files]
                print(77, "SELECTED-FILES:", self.selected_files)
            elif key == "AFTER-DOWNLOADED-RUN":
                self.after_downloaded_run = value.strip()
            else:
                pass

    def kb_mb_gb_to_byte(self, text):
        number, unit = text.split(" ")
        if "KB" in unit:
            number = int(number)*1024
        elif "MB" in unit:
            number = int(number)*1024*1024
        elif "GB" in unit:
            number = int(number)*1024*1024*1024
        else:
            pass #??
        return number

    def select_files_to_download(self):
        info = libtorrent.torrent_info(self.drive_path + self.torrent_file)
        hash_string = str(info.info_hash())
        self.set_spec_keys()
        files = info.files()
        temp_file_dict = {}
        counter = -1
        for file in files:
            counter = counter + 1
            file_name = str(file.path)
            downed_line = hash_string + "_-_" + file_name
            # IF FILE NOT DOWNLOADED
            if downed_line not in self.downed_txt:
                # IF FILESIZE BETWEEN REQUESTED SIZES
                file_size = file.size
                if file_size >= self.min_file_size and file_size <= self.max_file_size:
                    # IF WE HAVE 'self.selected_files' AND 'file_name' IN IT
                    if self.selected_files:
                        if file_name in self.selected_files:
                            temp_file_dict[downed_line] = {"file_name": file_name, "file_size": file_size, "index": counter}
                        else:
                            print([file_name], "not in selected_files")
                    else:
                        temp_file_dict[downed_line] = {"file_name": file_name, "file_size": file_size, "index": counter}

        torrents_dict = {}
        if len(temp_file_dict) > 0:
            # SORT FILES
            temp_list = [key for key in temp_file_dict]
            temp_list.sort()
            torrents_dict[hash_string] = {"torrent_name": self.torrent_file, "files": []}
            for key in temp_list:
                torrents_dict[hash_string]["files"].append(temp_file_dict[key])
            torrents_dict[hash_string]["after_downloaded_run"] = self.after_downloaded_run
        else:
            print("'temp_file_dict' is empty for:", self.torrent_file)
        return torrents_dict
