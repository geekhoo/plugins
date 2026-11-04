"""Record each change to a contestant's kanban board, from the host, without touching the contestant.

Runs outside the sandbox and only reads. It needs no harness or model support, so it sees lane moves however
they were written.

Windows fails a rename over a file while anyone holds a handle on it, even with full sharing. So changes are found
by enumerating the directory, which opens no handle on the board. A read opens the file and takes a full oplock as
one atomic step: a contestant's conflicting write or rename then waits the read out rather than failing. Anyone
else having the file open refuses the oplock, and the board is read on a later tick, so a torn board is never
recorded.

    python board-watcher.py --workspace <folder> --out <run>/board-snapshots.jsonl --stop-file <path> --parent-pid <pid>

The output is NDJSON: a `start` record, one `snapshot` per observed board state, and a `stop` record. A record
without a `stop` means the watcher died, and the adapters then treat its coverage as unproven.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time

SCHEMA = 'geeky-eval.board-snapshots/1'
MAX_BYTES = 1024 * 1024


def now():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'


if os.name == 'nt':
    import ctypes
    from ctypes import wintypes

    class _Overlapped(ctypes.Structure):
        _fields_ = [('Internal', ctypes.c_size_t), ('InternalHigh', ctypes.c_size_t), ('Offset', wintypes.DWORD), ('OffsetHigh', wintypes.DWORD), ('hEvent', wintypes.HANDLE)]

    class _OplockInput(ctypes.Structure):
        _fields_ = [('Version', wintypes.WORD), ('Length', wintypes.WORD), ('Level', wintypes.DWORD), ('Flags', wintypes.DWORD)]

    class _OplockOutput(ctypes.Structure):
        _fields_ = [('Version', wintypes.WORD), ('Length', wintypes.WORD), ('Original', wintypes.DWORD), ('New', wintypes.DWORD), ('Flags', wintypes.DWORD), ('Access', wintypes.DWORD), ('Share', wintypes.WORD)]

    class _UnicodeString(ctypes.Structure):
        _fields_ = [('Length', wintypes.USHORT), ('MaximumLength', wintypes.USHORT), ('Buffer', wintypes.LPCWSTR)]

    class _ObjectAttributes(ctypes.Structure):
        _fields_ = [('Length', wintypes.ULONG), ('RootDirectory', wintypes.HANDLE), ('ObjectName', ctypes.POINTER(_UnicodeString)), ('Attributes', wintypes.ULONG),
                    ('SecurityDescriptor', wintypes.LPVOID), ('SecurityQualityOfService', wintypes.LPVOID)]

    class _IoStatus(ctypes.Structure):
        _fields_ = [('Status', ctypes.c_size_t), ('Information', ctypes.c_size_t)]

    _ntdll = ctypes.WinDLL('ntdll')
    _ntdll.NtCreateFile.restype = wintypes.LONG
    _ntdll.NtCreateFile.argtypes = (ctypes.POINTER(wintypes.HANDLE), wintypes.DWORD, ctypes.POINTER(_ObjectAttributes), ctypes.POINTER(_IoStatus), wintypes.LPVOID,
                                    wintypes.ULONG, wintypes.ULONG, wintypes.ULONG, wintypes.ULONG, wintypes.LPVOID, wintypes.ULONG)
    _kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    _kernel32.CreateEventW.restype = wintypes.HANDLE
    _kernel32.CreateEventW.argtypes = (wintypes.LPVOID, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR)
    _kernel32.DeviceIoControl.argtypes = (wintypes.HANDLE, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD, wintypes.LPVOID, wintypes.LPVOID)
    _kernel32.ReadFile.argtypes = (wintypes.HANDLE, wintypes.LPVOID, wintypes.DWORD, wintypes.LPVOID, wintypes.LPVOID)
    _kernel32.GetOverlappedResult.argtypes = (wintypes.HANDLE, wintypes.LPVOID, wintypes.LPVOID, wintypes.BOOL)
    _kernel32.WaitForSingleObject.argtypes = (wintypes.HANDLE, wintypes.DWORD)
    _kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    _GENERIC_READ, _SHARE_ALL, _FILE_ATTRIBUTE_NORMAL, _FILE_OPEN, _CASE_INSENSITIVE = 0x80000000, 0x7, 0x80, 1, 0x40
    _NON_DIRECTORY, _OPEN_REQUIRING_OPLOCK = 0x40, 0x10000
    _FSCTL_REQUEST_OPLOCK, _OPLOCK_FULL, _OPLOCK_REQUEST = 0x00090240, 0x7, 0x1
    _IO_PENDING, _HANDLE_EOF = 997, 38

    def _open_for_oplock(path):
        """Open with FILE_OPEN_REQUIRING_OPLOCK, which leaves no gap between the open and the oplock for a rename to hit."""
        text = '\\??\\' + os.path.abspath(path)
        name = _UnicodeString(len(text) * 2, len(text) * 2, text)
        attributes = _ObjectAttributes(ctypes.sizeof(_ObjectAttributes), None, ctypes.pointer(name), _CASE_INSENSITIVE, None, None)
        handle, status = wintypes.HANDLE(), _IoStatus()
        result = _ntdll.NtCreateFile(ctypes.byref(handle), _GENERIC_READ, ctypes.byref(attributes), ctypes.byref(status), None, _FILE_ATTRIBUTE_NORMAL, _SHARE_ALL, _FILE_OPEN,
                                     _NON_DIRECTORY | _OPEN_REQUIRING_OPLOCK, None, 0)
        return handle.value if result >= 0 else None

    def read_board(path):
        """The file's bytes, or None when it cannot be read without risk to a writer right now."""
        handle = _open_for_oplock(path)
        if handle is None:
            return None
        held = _kernel32.CreateEventW(None, True, False, None)
        finished = _kernel32.CreateEventW(None, True, False, None)
        request = _OplockInput(1, ctypes.sizeof(_OplockInput), _OPLOCK_FULL, _OPLOCK_REQUEST)
        answer = _OplockOutput()
        oplock, reading = _Overlapped(hEvent=held), _Overlapped(hEvent=finished)
        try:
            # A pending call means the oplock is held. It stays pending until a break or this handle's close.
            if _kernel32.DeviceIoControl(handle, _FSCTL_REQUEST_OPLOCK, ctypes.byref(request), ctypes.sizeof(request), ctypes.byref(answer), ctypes.sizeof(answer), None, ctypes.byref(oplock)) or ctypes.get_last_error() != _IO_PENDING:
                return None
            buffer = ctypes.create_string_buffer(MAX_BYTES + 1)
            count = wintypes.DWORD()
            if not _kernel32.ReadFile(handle, buffer, MAX_BYTES + 1, None, ctypes.byref(reading)) and ctypes.get_last_error() != _IO_PENDING:
                return b'' if ctypes.get_last_error() == _HANDLE_EOF else None
            if not _kernel32.GetOverlappedResult(handle, ctypes.byref(reading), ctypes.byref(count), True):
                return b'' if ctypes.get_last_error() == _HANDLE_EOF else None
            return buffer.raw[:count.value]
        finally:
            _kernel32.CloseHandle(handle)
            # Closing completes the oplock call. `oplock` and `answer` must outlive it.
            _kernel32.WaitForSingleObject(held, 5000)
            _kernel32.CloseHandle(held)
            _kernel32.CloseHandle(finished)
else:
    def read_board(path):
        """The file's bytes, or None when it changed during the read."""
        try:
            with open(path, 'rb') as stream:
                before = os.fstat(stream.fileno())
                data = stream.read(MAX_BYTES + 1)
                after = os.fstat(stream.fileno())
        except OSError:
            return None
        return data if (before.st_mtime_ns, before.st_size) == (after.st_mtime_ns, after.st_size) == (after.st_mtime_ns, len(data)) else None


def boards(workspace):
    """(path, signature, size) of each board, from directory entries alone, so no handle is opened on a board."""
    found = []
    try:
        with os.scandir(Path(workspace) / 'docs') as folders:
            for folder in folders:
                if not folder.is_dir():
                    continue
                with os.scandir(folder.path) as entries:
                    for entry in entries:
                        if entry.name.lower() == 'kanban.md':
                            info = entry.stat()
                            found.append((Path(entry.path), (info.st_mtime_ns, info.st_size), info.st_size))
    except OSError:
        pass
    return found


def alive(pid):
    if not pid:
        return True
    if os.name == 'nt':
        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
        if not handle:
            return False
        code = wintypes.DWORD()
        ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
        ctypes.windll.kernel32.CloseHandle(handle)
        return code.value == 259
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


class Watcher:
    def __init__(self, workspace, out):
        self.workspace, self.out = Path(workspace), out
        self.signature, self.digest = {}, {}
        self.snapshots = self.retries = 0

    def write(self, record):
        self.out.write(json.dumps(record, ensure_ascii=False) + '\n')
        self.out.flush()

    def poll(self, force=False):
        for path, signature, size in boards(self.workspace):
            unchanged = self.signature.get(path) == signature
            if unchanged and not force:
                continue
            if size > MAX_BYTES:
                if not unchanged:
                    self.signature[path] = signature
                    self.write({'record': 'skipped', 'at': now(), 'path': path.relative_to(self.workspace).as_posix(), 'bytes': size})
                continue
            data = read_board(path)
            if data is None:
                self.retries += 1
                continue
            self.signature[path] = signature
            digest = hashlib.sha256(data).hexdigest()
            if self.digest.get(path) == digest:
                continue
            self.digest[path] = digest
            self.snapshots += 1
            self.write({'record': 'snapshot', 'at': now(), 'path': path.relative_to(self.workspace).as_posix(), 'sha256': digest, 'text': data.decode('utf-8', 'replace')})


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--stop-file', type=Path, required=True)
    parser.add_argument('--parent-pid', type=int)
    parser.add_argument('--interval', type=float, default=0.25)
    parser.add_argument('--max-seconds', type=float, default=6 * 3600)
    args = parser.parse_args()
    deadline = time.monotonic() + args.max_seconds
    with open(args.out, 'a', encoding='utf-8', newline='\n') as out:
        watcher = Watcher(args.workspace, out)
        watcher.write({'record': 'start', 'schema': SCHEMA, 'at': now(), 'interval_s': args.interval})
        reason = 'deadline'
        while time.monotonic() < deadline:
            watcher.poll()
            if args.stop_file.exists():
                reason = 'stop-file'
                break
            if not alive(args.parent_pid):
                reason = 'parent-exited'
                break
            time.sleep(args.interval)
        watcher.poll(force=True)
        watcher.write({'record': 'stop', 'at': now(), 'reason': reason, 'snapshots': watcher.snapshots, 'retries': watcher.retries})
    return 0


if __name__ == '__main__':
    sys.exit(main())
