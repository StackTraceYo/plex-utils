import shutil
import time

from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer


# /home25/daymanbpi/downloads/1.SEED/3.Manual/2.Movie.SD   ---->   /home25/daymanbpi/downloads/2.PLEX/2.Movie.SD
# /home25/daymanbpi/downloads/1.SEED/3.Manual/3.Movie.HD   ---->   /home25/daymanbpi/downloads/2.PLEX/3.Movie.HD

class PlexWatcher(PatternMatchingEventHandler):
    patterns = ["*.avi", "*.mkv"]
    ignore_directories = ["1.TV.SD"]

    def __init__(self):
        super(PlexWatcher, self).__init__()
        self.dir_mapping = {
            "2.Movie.SD": "/2.PLEX/2.Movie.SD/",
            "3.Movie.HD": "/2.PLEX/3.Movie.HD/"
        }

    def process(self, event):
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
            shutil.copy2(full_path, new_path)
        else:
            print "No Path Mapping Found For: ", full_path.split("3.Manual/")[1].split("/")[0]

    def on_created(self, event):
        self.process(event)

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
