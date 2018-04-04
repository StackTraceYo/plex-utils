import os
import shutil
import time
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer


# /home25/daymanbpi/downloads/1.SEED/3.Manual/2.Movie.SD   ---->   /home25/daymanbpi/downloads/2.PLEX/2.Movie.SD
# /home25/daymanbpi/downloads/1.SEED/3.Manual/3.Movie.HD   ---->   /home25/daymanbpi/downloads/2.PLEX/3.Movie.HD

class FileToCopy:
    def __init__(self, from_path, to_path, timestamp):
        self.from_path = from_path
        self.new_path = to_path
        self.timestamp = timestamp

    def update(self, timestamp):
        self.timestamp = timestamp

    def not_modified_since(self, timestamp, diff):
        return ((timestamp - self.timestamp).total_seconds()) > diff


# stupid class that buffers my print statements
class PrintBuffer:
    def __init__(self, buffer_count=30):
        self.buffer_count = buffer_count
        self.buffer = []

    def write(self, output):
        if len(self.buffer) > 0:
            front = self.buffer[0]
            if front == output:
                self.buffer.append(output)
                if self.buffer_count > len(self.buffer):
                    self.buffer_write(output)
            else:
                self.buffer_write(output)
        else:
            self.buffer.append(output)

    def buffer_write(self, output):
        print self.buffer[0]
        print output
        if len(self.buffer) > 1:
            self.buffer = []
        else:
            self.buffer.pop()


class PlexWatcher(PatternMatchingEventHandler):
    patterns = ["*.avi", "*.mkv"]
    ignore_directories = True
    ignore_patterns = ["*.sample*", "*.Sample*"]

    def __init__(self):
        super(PlexWatcher, self).__init__()
        self.dir_mapping = {
            "2.Movie.SD": "/2.PLEX/2.Movie.SD/",
            "3.Movie.HD": "/2.PLEX/3.Movie.HD/"
        }
        self.pending = {}
        self.scheduler = BackgroundScheduler()
        self.check_pending_job = self.scheduler.add_job(self.check_pending, 'interval', minutes=1, name='check-pending')
        self.scheduler.start()
        self.sub_directories_to_ignore = {"Sample", "1.TV.SD"}
        self.writer = PrintBuffer()

    def should_ignore(self, path):
        # create a set from the path and intersect it with the sub_directories to ignore
        # if the length of the intersection is >0 then we should ignore
        return len(set(path.split("/")).intersection(self.sub_directories_to_ignore)) > 0

    def queue_file_copy(self, event):
        """
        event.event_type
            'modified' | 'created' | 'moved' | 'deleted'
        event.is_directory
            True | False
        event.src_path
            path/to/observed/file
        """
        print event.src_path, event.event_type
        if self.should_ignore(event.src_path):
            self.writer.write("Ignoring File In Blacklisted Directory")
            return
        full_path = event.src_path
        new_path = self.gen_new_path(full_path)
        if new_path != None:
            self.writer.write("New Path: " + new_path)
            fc = FileToCopy(full_path, new_path, datetime.now())
            self.pending[full_path] = fc
        else:
            self.writer.write("Error Generating new path for " + full_path)

    def update(self, event):
        """
        event.event_type
            'modified' | 'created' | 'moved' | 'deleted'
        event.is_directory
            True | False
        event.src_path
            path/to/observed/file
        """
        full_path = event.src_path
        # if its in the pending files
        if full_path in self.pending:
            # get the filetocopy and update the timestamp
            fc = self.pending[full_path]
            fc.update(datetime.now())
            self.writer.write("Updating Timestamp for: " + full_path)

    def check_pending(self):
        self.writer.write("Checking Pending Files To Copy")
        if len(self.pending.keys()) == 0:
            self.writer.write("No Files To Copy")
        for name, fc in self.pending.items():
            self.writer.write("Checking: " + name)
            if fc.not_modified_since(datetime.now(), 30):  # file has not been touched for a 30 seconds
                self.writer.write("Starting Copy...")
                shutil.copy2(fc.from_path, fc.new_path)
                self.writer.write("Copied: " + fc.from_path + " - To - " + fc.new_path)
                del self.pending[name]
            else:
                self.writer.write(name + " was modified within 30 seconds skipping")

    def on_created(self, event):
        # on file create queue the file for processing
        self.queue_file_copy(event)

    def on_modified(self, event):
        # on file modify, update the files timestamp
        self.update(event)

    def gen_new_path(self, full_path):
        self.writer.write("Generating New Path For : " + full_path)
        try:
            path_split = full_path.split("3.Manual/")[1].split("/")
            sub_dir = path_split[0]  # directory to map
            i = len(path_split) - 1  # get index of filename
            fn = path_split[i]  # filename
            pd = path_split[i - 1]  # parent directory
            if sub_dir in self.dir_mapping:  # if the mapping exists
                sub_split = full_path.split("/1.SEED/")[0]
                if pd in self.dir_mapping:  # if the mapped folder is the parent
                    # just return path of the file
                    return sub_split + self.dir_mapping[sub_dir] + fn
                else:
                    # parent folder exists lets make a copy of it in the destination
                    # make folder path
                    dir_path = sub_split + self.dir_mapping[sub_dir] + pd
                    try:
                        os.makedirs(dir_path)
                        return dir_path + "/" + fn
                    except OSError as exc:
                        return sub_split + self.dir_mapping[sub_dir] + fn
        except Exception as e:
            self.writer.write(e)


if __name__ == '__main__':
    observer = Observer()
    # testing directory_to_watch = "/home/ahmad/test/daymanbpi/downloads/1.SEED/3.Manual"
    directory_to_watch = "/home25/daymanbpi/downloads/1.SEED/3.Manual"
    observer.schedule(PlexWatcher(), path=directory_to_watch, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
