import time
import os
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from scanner import scan_files
try:
    from log_manager import log_scan, delete_log
    print("Successfully imported log_manager functions.")
except ImportError:
    print("Error: Could not import from log_manager.py.")
    log_scan = None
    delete_log = None
    

logging.basicConfig(
    filename="safewatch.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def categorize(file_path):
    ext = os.path.splitext(file_path)[1].lower()  # get extension
    categories = {
        "Documents": [".pdf", ".docx", ".txt"],
        "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp"],
        "Videos": [".mp4", ".avi", ".mov", ".mkv"]
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
        try:
            scan_result = scan_files(event.src_path)
            recently_created[event.src_path]= time.time()
            print(f"Scan result: {scan_result}")

            if scan_result.get("status") == "Danger":
                violations_list = scan_result.get("violations")
                print(f"DANGER DETECTED: {violations_list}")
                logging.warning(f"DANGER DETECTED: {event.src_path}, Violations: {violations_list}")
                log_scan(event.src_path, category, scan_result)
        except Exception as e:
            print(f"Error calling scan_files for {event.src_path}: {e}")
        

        
    def on_deleted(self, event):
        if event.is_directory:
            return
        print(f"🗑️ File deleted: {event.src_path}")
        logging.info(f"Deleted file: {event.src_path}")
        delete_log(event.src_path)
        if event.src_path in recently_created:
            del recently_created[event.src_path]

    def on_modified(self, event):
        if event.is_directory:
            return
        now = time.time()
        if event.src_path in recently_created:
            if now - recently_created[event.src_path] < 2:
                return
            else:
                del recently_created[event.src_path]

        try:
            if os.path.exists(event.src_path) and os.path.isfile(event.src_path):
                scan_result = scan_files(event.src_path)
                print(f"Scan result: {scan_result}")

                if scan_result.get("status") == "Danger":
                    violations_list = scan_result.get("violations",[])
                    print(f"DANGER DETECTED: {violations_list}")
                    logging.warning(f"DANGER DETECTED: {event.src_path}, Violations: {violations_list}")
                    log_scan(event.src_path, categorize(event.src_path), scan_result)
        except Exception as e:
            print(f"Error calling scan_files for {event.src_path}: {e}")
    
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
    folder = r"//path to folder to moniter"
    start_watch(folder)