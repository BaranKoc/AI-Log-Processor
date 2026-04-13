# Phase 3: File Watcher
# TODO: Implement LogFileHandler(FileSystemEventHandler) — handles on_created for new .json files
# TODO: Implement start_watcher(watch_dir, db_path, loop) — starts watchdog observer, bridges to async shipper
# TODO: Implement process_log_file(file_path, db_path, loop) — reads JSON, validates with Pydantic, ships via asyncio
