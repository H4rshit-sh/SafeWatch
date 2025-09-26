import time
import os
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logging.basicConfig(
    filename="safewatch.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def categorize(file_path):
    ext = os.path.splitext(file_path)[1].lower()  # get extension
    categories = {
        "Documents": [".pdf", ".docx", ".txt", ".pptx", ".xlsx"],
        "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp"],
        "Videos": [".mp4", ".avi", ".mov", ".mkv"],
        "Audio": [".mp3", ".wav", ".aac"],
        "Executables": [".exe", ".bat", ".msi"],
        "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"]
    }
    for category, exts in categories.items():
        if ext in exts:
            return category
    return "SUS"


recently_created = {}
class SafeWatchHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        category = categorize(event.src_path)
        print(f"📂 New file detected: {event.src_path}",[category])
        logging.info(f"New file: {event.src_path}, [category]")
        recently_created[event.src_path]= time.time()

        
    def on_deleted(self, event):
        if event.is_directory:
            return
        print(f"🗑️ File deleted: {event.src_path}")
        logging.info(f"Deleted file: {event.src_path}")

    def on_modified(self, event):
        if event.is_directory:
            return
        now = time.time()
        if event.src_path in recently_created:
            if now - recently_created[event.src_path] < 2:
                return
            else:
                del recently_created[event.src_path]

        print(f"📝 File modified: {event.src_path}")
        logging.info(f"Modified file: {event.src_path}")
    
def start_watch(path_to_watch):
    observer = Observer()
    observer.schedule(SafeWatchHandler(), path=path_to_watch, recursive=True)
    observer.start()
    print(f"Watching {path_to_watch} for changes...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    folder = r"D:\Proj\SafeWatch\SafeFolder"
    start_watch(folder)