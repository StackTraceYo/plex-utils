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
        return ((timestamp - self.timestamp).total_seconds()) < diff


class PlexWatcher(PatternMatchingEventHandler):
    patterns = ["*.avi", "*.mkv"]
    ignore_directories = ["1.TV.SD"]

    def __init__(self):
        super(PlexWatcher, self).__init__()
        self.dir_mapping = {
            "2.Movie.SD": "/2.PLEX/2.Movie.SD/",
            "3.Movie.HD": "/2.PLEX/3.Movie.HD/"
        }
        self.pending = {}
        self.scheduler = BackgroundScheduler()
        self.check_pending_job = self.scheduler.add_job(self.check_pending, 'interval', minutes=2, name='check-pending')
        self.scheduler.start()

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
        full_path = event.src_path
        new_path = self.gen_new_path(full_path)
        if new_path != None:
            print "New Path: ", new_path
            fc = FileToCopy(full_path, new_path, datetime.now())
            self.pending[full_path] = fc
        else:
            print "No Path Mapping Found For: ", full_path.split("3.Manual/")[1].split("/")[0]

    def update(self, event):
        """
        event.event_type
            'modified' | 'created' | 'moved' | 'deleted'
        event.is_directory
            True | False
        event.src_path
            path/to/observed/file
        """
        print event.event_type
        full_path = event.src_path
        if full_path in self.pending:
            fc = self.pending[full_path]
            fc.update(datetime.now())
            print "Updating Timestamp for: ", full_path

    def check_pending(self):
        print "Checking Pending Files To Copy"
        for name, fc in self.pending.items():
            if fc.not_modified_since(datetime.now(), 60):
                # file has not been touched for a minute
                shutil.copy2(fc.from_path, fc.to_path)
                del self.pending[name]
            else:
                print name + " was modified within 60 seconds"

    def on_created(self, event):
        self.queue_file_copy(event)

    def on_modified(self, event):
        self.update(event)

    def gen_new_path(self, full_path):
        sub_dir = full_path.split("3.Manual/")[1].split("/")[0]
        fn = full_path.split("3.Manual/")[1].split("/")[1]
        if sub_dir in self.dir_mapping:
            return full_path.split("/1.SEED/")[0] + self.dir_mapping[sub_dir] + fn
        else:
            return None


if __name__ == '__main__':
    observer = Observer()
    directory_to_watch = "/home25/daymanbpi/downloads/1.SEED/3.Manual"
    observer.schedule(PlexWatcher(), path=directory_to_watch, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
