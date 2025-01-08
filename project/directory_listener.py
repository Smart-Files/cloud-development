import asyncio
from watchdog.events import FileSystemEventHandler
from project.firestore import db
import os
from watchdog.observers import Observer
class DirectoryEventHandler(FileSystemEventHandler):
    def __init__(self, uuid):
        self.uuid = uuid

    def on_modified(self, event):
        if not event.is_directory:
            self.update_firestore(event.src_path)

    def update_firestore(self, file_path):
        output_files = get_directory_contents(self.uuid)
        asyncio.run(db.collection("process").document(self.uuid).update({"output_files": output_files}))

def get_directory_contents(uuid: str):
    return os.listdir(f"/working_dir/{uuid}")

async def directory_listener(uuid: str):
    event_handler = DirectoryEventHandler(uuid)
    observer = Observer()
    path = f"/working_dir/{uuid}"
    observer.schedule(event_handler, path, recursive=False)
    observer.start()

    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        observer.stop()
    observer.join()
