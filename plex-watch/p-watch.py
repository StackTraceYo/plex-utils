import sys
import time

from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer


class PlexWatcher(PatternMatchingEventHandler):
    patterns = ["*.avi", "*.mkv"]

    def process(self, event):
        """
        event.event_type
            'modified' | 'created' | 'moved' | 'deleted'
        event.is_directory
            True | False
        event.src_path
            path/to/observed/file
        """
        # the file will be processed there
        print event.src_path, event.event_type  # print now only for debug


    def on_created(self, event):
        self.process(event)


if __name__ == '__main__':
    args = sys.argv[1:]
    observer = Observer()
    directory_to_watch = "/home/ahmad/test/daymanbpi/downloads/1.SEED/3.Manual"
    observer.schedule(PlexWatcher(), path=directory_to_watch, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
