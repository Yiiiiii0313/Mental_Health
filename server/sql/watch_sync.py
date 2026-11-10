"""
开发时文件监听：保存 init.sql 或数据库相关 Python 后，自动迁移并同步 init.sql。

用法（在 server 目录，与 app.py 并行开一个终端）:
    python sql/watch_sync.py

监听范围:
    - sql/init.sql
    - routes/*.py
    - utils/media_list.py
"""
from __future__ import annotations

import subprocess
import sys
import threading
import time
import os
from pathlib import Path

SERVER_DIR = Path(__file__).resolve().parent.parent
INIT_SQL = SERVER_DIR / 'sql' / 'init.sql'
ROUTES_DIR = SERVER_DIR / 'routes'
MEDIA_LIST = SERVER_DIR / 'utils' / 'media_list.py'

DEBOUNCE_SEC = 1.5
IGNORE_INIT_SEC = 4.0

IGNORED_NAMES = {
    'watch_sync.py',
    'sync_init.py',
    'apply_migrations.py',
    '__init__.py',
}


def _configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            try:
                stream.reconfigure(encoding='utf-8', errors='replace')
            except Exception:
                pass


def _subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    return env


def _emit(text: str, stream=sys.stdout) -> None:
    if not text:
        return
    try:
        print(text, file=stream, flush=True)
    except UnicodeEncodeError:
        encoding = getattr(stream, 'encoding', None) or 'utf-8'
        print(text.encode(encoding, errors='replace').decode(encoding), file=stream, flush=True)


def _ensure_watchdog():
    try:
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer
        return FileSystemEventHandler, Observer
    except ImportError:
        print('缺少依赖 watchdog，请先执行: pip install watchdog', file=sys.stderr)
        raise SystemExit(1)


def _is_watched(path: Path) -> bool:
    path = path.resolve()
    if path.name in IGNORED_NAMES:
        return False
    if '__pycache__' in path.parts:
        return False
    if path == INIT_SQL.resolve():
        return True
    if path == MEDIA_LIST.resolve():
        return True
    if path.parent.resolve() == ROUTES_DIR.resolve() and path.suffix == '.py':
        return True
    return False


def _run_pipeline(apply_migrations: bool) -> None:
    stamp = time.strftime('%H:%M:%S')
    if apply_migrations:
        _emit(f'[{stamp}] 检测到 Python 变更，先应用迁移…')
        result = subprocess.run(
            [sys.executable, 'sql/apply_migrations.py'],
            cwd=SERVER_DIR,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            env=_subprocess_env(),
        )
        if result.stdout:
            _emit(result.stdout.rstrip())
        if result.returncode != 0 and result.stderr:
            _emit(result.stderr.rstrip(), sys.stderr)
    else:
        _emit(f'[{stamp}] 检测到 init.sql 变更，同步表结构…')

    result = subprocess.run(
        [sys.executable, 'sql/sync_init.py'],
        cwd=SERVER_DIR,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        env=_subprocess_env(),
    )
    if result.stdout:
        _emit(result.stdout.rstrip())
    if result.stderr:
        _emit(result.stderr.rstrip(), sys.stderr)


def main() -> int:
    _configure_stdio()
    FileSystemEventHandler, Observer = _ensure_watchdog()

    class Handler(FileSystemEventHandler):
        def __init__(self):
            super().__init__()
            self._lock = threading.Lock()
            self._timer: threading.Timer | None = None
            self._apply_migrations = False
            self._ignore_init_until = 0.0

        def _schedule(self, path: Path) -> None:
            if not _is_watched(path):
                return
            if path.resolve() == INIT_SQL.resolve():
                if time.monotonic() < self._ignore_init_until:
                    return
                with self._lock:
                    self._apply_migrations = self._apply_migrations or False
            else:
                with self._lock:
                    self._apply_migrations = True

            with self._lock:
                if self._timer:
                    self._timer.cancel()
                self._timer = threading.Timer(DEBOUNCE_SEC, self._trigger)
                self._timer.start()

        def on_modified(self, event):
            if event.is_directory:
                return
            self._schedule(Path(event.src_path))

        def on_created(self, event):
            if event.is_directory:
                return
            self._schedule(Path(event.src_path))

        def _trigger(self) -> None:
            with self._lock:
                apply_migrations = self._apply_migrations
                self._apply_migrations = False
                self._ignore_init_until = time.monotonic() + IGNORE_INIT_SEC

            try:
                _run_pipeline(apply_migrations)
            except Exception as exc:
                print(f'[{time.strftime("%H:%M:%S")}] 自动同步失败: {exc}', file=sys.stderr)

    handler = Handler()
    observer = Observer()
    observer.schedule(handler, str(SERVER_DIR / 'sql'), recursive=False)
    observer.schedule(handler, str(ROUTES_DIR), recursive=False)
    observer.schedule(handler, str(SERVER_DIR / 'utils'), recursive=False)
    observer.start()

    print('数据库同步监听已启动。', flush=True)
    print(f'  监听: {INIT_SQL.name}, routes/*.py, utils/media_list.py', flush=True)
    print('  保存上述文件后将自动迁移并同步 init.sql（Ctrl+C 退出）\n', flush=True)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
