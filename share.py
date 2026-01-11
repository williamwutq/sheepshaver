#!/usr/bin/env python3
"""
Share utility - Sync files between local filesystem and a shared directory.

You can customize the local root (SHARE_PATH) and shared root (SHARED_ROOT)
by creating ~/.sharepath and ~/.shareroot files containing the absolute paths.
Only files under SHARE_PATH are managed; they are mapped to SHARED_ROOT
preserving their relative path under SHARE_PATH.

Copyright (C) 2026 William Wu

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation; either version 2 of the License, or (at your
option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software Foundation,
Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
"""


import sys
import os
from pathlib import Path
import shutil
from datetime import datetime
import argparse
import fnmatch

# Load SHARE_PATH from ~/.sharepath if exists, else None
def load_path_config(config_file, default=None):
    try:
        path = Path.home() / config_file
        if path.exists():
            with open(path, 'r') as f:
                value = f.read().strip()
                if value:
                    return Path(value).expanduser().resolve()
    except Exception:
        pass
    return default

SHARE_PATH = load_path_config('.sharepath')
SHARED_ROOT = load_path_config('.shareroot', Path.home() / "Shared" / "dump")


def get_shared_path(local_path):
    """Convert local path to shared path, preserving relative path under SHARE_PATH"""
    if not local_path:
        return None
    abs_path = Path(local_path).resolve()
    if SHARE_PATH:
        try:
            rel = abs_path.relative_to(SHARE_PATH)
        except ValueError:
            print(f"Error: {local_path} is not under SHARE_PATH ({SHARE_PATH})")
            return None
    else:
        rel = abs_path.name  # fallback: just filename
    return SHARED_ROOT / rel


def format_time(timestamp):
    """Format timestamp for human-readable display"""
    delta = datetime.now().timestamp() - timestamp
    if delta < 60:
        return f"{int(delta)}s ago"
    elif delta < 3600:
        return f"{int(delta/60)}m ago"
    elif delta < 86400:
        return f"{int(delta/3600)}h ago"
    else:
        return f"{int(delta/86400)}d ago"


def file_exists_and_valid(path):
    """Check if file exists and is a regular file"""
    p = Path(path)
    return p.exists() and p.is_file()


def file_is_newer(time1, time2):
    """Check if time1 is newer than time2 with 1 second tolerance"""
    return (time1 - time2) > 1  # 1 second tolerance


def looks_like_private(name):
    """Check if filename looks like a private file"""
    private_prefix = ['_', '~', '.', '#']
    return any(name.startswith(prefix) for prefix in private_prefix)


def recursive_apply_skips(func, path, **kwargs):
    """Recursively apply func to all files under path"""
    ignore_patterns = kwargs.get('ignore_patterns', [])
    p = Path(path)
    res = 0
    if p.is_dir():
        # Read .shareignore if exists
        if (p / '.shareignore').exists():
            with open(p / '.shareignore', 'r') as f:
                new_patterns = []
                for line in f:
                    pattern = line.split('#', 1)[0].strip()
                    if pattern:
                        if pattern.startswith('/'):
                            pattern = pattern[1:]
                        new_patterns.append(pattern)
            ignore_patterns = ignore_patterns + new_patterns
            kwargs['ignore_patterns'] = ignore_patterns
        for sub_path in p.iterdir():
            # Check against ignore patterns using fnmatch
            if any(fnmatch.fnmatch(sub_path.name, pattern) or fnmatch.fnmatch(sub_path, pattern) for pattern in ignore_patterns):
                continue
            # Skip private-looking files
            if looks_like_private(sub_path.name):
                if not kwargs.get('suppress_extra', False):
                    print(f"⚠ {sub_path} looks like private; skipping.")
                continue
            if sub_path.is_file() or sub_path.is_dir():
                res += func(sub_path, **kwargs)
        if res != 0:
            return res
        return 0
    else:
        return func(p, **kwargs)


def recursive_apply_noskip(func, path, **kwargs):
    """Recursively apply func to all files under path without skipping"""
    ignore_patterns = kwargs.get('ignore_patterns', [])
    kwargs['suppress_error'] = True  # Suppress errors for missing files
    p = Path(path)
    res = 0
    if p.is_dir():
        # Read .shareignore if exists
        if (p / '.shareignore').exists():
            with open(p / '.shareignore', 'r') as f:
                new_patterns = []
                for line in f:
                    pattern = line.split('#', 1)[0].strip()
                    if pattern:
                        if pattern.startswith('/'):
                            pattern = pattern[1:]
                        new_patterns.append(pattern)
            ignore_patterns = ignore_patterns + new_patterns
            kwargs['ignore_patterns'] = ignore_patterns
        for sub_path in p.iterdir():
            # Check against ignore patterns using fnmatch
            if any(fnmatch.fnmatch(sub_path.name, pattern) or fnmatch.fnmatch(sub_path, pattern) for pattern in ignore_patterns):
                continue
            if sub_path.is_file() or sub_path.is_dir():
                res += func(sub_path, **kwargs)
        if res != 0:
            return res
        return 0
    else:
        return func(p, **kwargs)


def cmd_put(local_file, **kwargs):
    """Copy local file to shared (always overwrite)"""
    local_path = Path(local_file)
    if local_path.is_dir():
        recursive_apply_skips(cmd_put, local_path, **kwargs)
        return 0

    if not file_exists_and_valid(local_path):
        if not kwargs.get('suppress_error', False):
            print(f"Error: Local file does not exist: {local_file}")
        return 1

    shared_path = get_shared_path(local_file)
    if shared_path is None:
        return 1
    shared_path.parent.mkdir(parents=True, exist_ok=True)

    shutil.copy2(local_path, shared_path)
    print(f"✓ Put: {local_file} → {shared_path}")
    return 0


def cmd_push(local_file, **kwargs):
    """Copy local file to shared only if local is newer"""
    local_path = Path(local_file)
    if local_path.is_dir():
        return recursive_apply_skips(cmd_push, local_path, **kwargs)

    if not file_exists_and_valid(local_path):
        if not kwargs.get('suppress_error', False):
            print(f"Error: Local file does not exist: {local_file}")
        return 1

    shared_path = get_shared_path(local_file)
    if shared_path is None:
        return 1

    # If shared doesn't exist, always push
    if not shared_path.exists():
        shared_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(local_path, shared_path)
        print(f"✓ Pushed: {local_file} → {shared_path} (new)")
        return 0

    # Compare modification times
    local_mtime = local_path.stat().st_mtime
    shared_mtime = shared_path.stat().st_mtime

    if file_is_newer(local_mtime, shared_mtime):
        shutil.copy2(local_path, shared_path)
        print(f"✓ Pushed: {local_file} (local newer)")
        return 0
    else:
        print(f"⊘ Not pushed: {local_file} (shared is newer or same)")
        return 0
    

def cmd_push_all(**kwargs):
    """Push all local files under SHARE_PATH to SHARED_ROOT if local is newer"""
    if SHARE_PATH is None:
        if not kwargs.get('suppress_critical', False):
            print("Error: SHARE_PATH is not set. Cannot push all.")
        return 1
    
    count = 0

    for remote_file in SHARED_ROOT.rglob('*'):
        if not remote_file.is_file():
            continue
        local_path = Path(remote_file)
        # Reconstruct local path
        relative = local_path.relative_to(SHARED_ROOT)
        local_file = SHARE_PATH / relative
        local_path = Path(local_file)

        if not file_exists_and_valid(local_path):
            continue

        # If shared doesn't exist, always push
        if not remote_file.exists():
            remote_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(local_path, remote_file)
            print(f"✓ Pushed: {local_file} → {remote_file} (new)")
            count += 1
            continue

        # Compare modification times
        local_mtime = local_path.stat().st_mtime
        shared_mtime = remote_file.stat().st_mtime
        if file_is_newer(local_mtime, shared_mtime):
            shutil.copy2(local_path, remote_file)
            print(f"✓ Pushed: {local_file} (local newer)")
            count += 1
        
    if count == 0:
        print("✓ Already up to date")
    else:
        print(f"✓ Pushed {count} files")
    return 0


def cmd_get(local_file, **kwargs):
    """Copy shared file to local (always overwrite)"""
    local_path = Path(local_file)
    if local_path.is_dir():
        return recursive_apply_noskip(cmd_get, local_path, **kwargs)

    shared_path = get_shared_path(local_file)
    if shared_path is None:
        return 1

    if not shared_path.exists():
        if not kwargs.get('suppress_error', False):
            print(f"Error: File not shared: {local_file}")
        return 1

    local_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(shared_path, local_path)
    print(f"✓ Got: {shared_path} → {local_file}")
    return 0


def cmd_pull(local_file, **kwargs):
    """Copy shared file to local only if shared is newer"""
    local_path = Path(local_file)
    if local_path.is_dir():
        return recursive_apply_noskip(cmd_pull, local_path, **kwargs)

    shared_path = get_shared_path(local_file)
    if shared_path is None:
        return 1

    if not shared_path.exists():
        if not kwargs.get('suppress_error', False):
            print(f"Error: File not shared: {local_file}")
        return 1

    # If local doesn't exist, always pull
    if not local_path.exists():
        local_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(shared_path, local_path)
        print(f"✓ Pulled: {local_file} (new locally)")
        return 0

    # Compare modification times
    local_mtime = local_path.stat().st_mtime
    shared_mtime = shared_path.stat().st_mtime

    if file_is_newer(shared_mtime, local_mtime):
        shutil.copy2(shared_path, local_path)
        print(f"✓ Pulled: {local_file} (shared newer)")
        return 0
    else:
        if not kwargs.get('suppress_extra', False):
            print(f"⊘ Not pulled: {local_file} (local is newer or same)")
        return 0
    

def cmd_pull_all(**kwargs):
    """Pull all shared files under SHARED_ROOT to SHARE_PATH if shared is newer"""
    if SHARE_PATH is None:
        if not kwargs.get('suppress_critical', False):
            print("Error: SHARE_PATH is not set. Cannot pull all.")
        return 1
    
    count = 0

    for shared_file in SHARED_ROOT.rglob('*'):
        if not shared_file.is_file():
            continue
        shared_path = Path(shared_file)
        # Reconstruct local path
        relative = shared_path.relative_to(SHARED_ROOT)
        if SHARE_PATH:
            local_file = SHARE_PATH / relative
        else:
            local_file = Path(relative)
        local_path = Path(local_file)

        # If local doesn't exist, always pull
        if not local_path.exists():
            local_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(shared_path, local_path)
            print(f"✓ Pulled: {local_file} (new locally)")
            count += 1
            continue

        # Compare modification times
        local_mtime = local_path.stat().st_mtime
        shared_mtime = shared_path.stat().st_mtime
        if file_is_newer(shared_mtime, local_mtime):
            shutil.copy2(shared_path, local_path)
            print(f"✓ Pulled: {local_file} (shared newer)")
            count += 1

    if count == 0:
        if not kwargs.get('suppress_extra', False):
            print("✓ Already up to date")
    else:
        print(f"✓ Pulled {count} files")

    return 0


def cmd_sync(local_file, **kwargs):
    """Sync by copying whichever version is newer"""
    local_path = Path(local_file)
    shared_path = get_shared_path(local_file)
    if shared_path is None:
        return 1

    local_exists = file_exists_and_valid(local_path)
    shared_exists = shared_path.exists()

    # If is path, recurse
    if local_path.is_dir():
        return recursive_apply_skips(cmd_sync, local_path, **kwargs)

    # If neither exists, error
    if not local_exists and not shared_exists:
        if not kwargs.get('suppress_error', False):
            print(f"Error: File exists in neither location: {local_file}")
        return 1

    # If only one exists, copy to the other
    if not shared_exists:
        shared_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(local_path, shared_path)
        print(f"✓ Synced: {local_file} → shared (new)")
        return 0

    if not local_exists:
        local_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(shared_path, local_path)
        print(f"✓ Synced: shared → {local_file} (new)")
        return 0

    # Both exist, compare times
    local_mtime = local_path.stat().st_mtime
    shared_mtime = shared_path.stat().st_mtime

    if file_is_newer(local_mtime, shared_mtime):
        shutil.copy2(local_path, shared_path)
        print(f"✓ Synced: {local_file} → shared (local newer)")
        return 0
    elif file_is_newer(shared_mtime, local_mtime):
        shutil.copy2(shared_path, local_path)
        print(f"✓ Synced: shared → {local_file} (shared newer)")
        return 0
    else:
        if not kwargs.get('suppress_extra', False):
            print(f"✓ Already synced: {local_file}")
        return 0


def cmd_sync_all(**kwargs):
    """Sync all files under SHARE_PATH and SHARED_ROOT by copying whichever is newer"""
    if SHARE_PATH is None:
        if not kwargs.get('suppress_critical', False):
            print("Error: SHARE_PATH is not set. Cannot sync all.")
        return 1
    
    count = 0

    # Walk through shared directory
    for shared_file in SHARED_ROOT.rglob('*'):
        if not shared_file.is_file():
            continue

        # Reconstruct local path
        relative = shared_file.relative_to(SHARED_ROOT)
        if SHARE_PATH:
            local_file = SHARE_PATH / relative
        else:
            local_file = Path(relative)
        local_path = Path(local_file)
        shared_path = Path(shared_file)

        local_exists = file_exists_and_valid(local_path)
        shared_exists = shared_path.exists()

        # If only one exists, copy to the other
        if not local_exists:
            local_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(shared_path, local_path)
            print(f"✓ Synced: shared → {local_file} (new)")
            count += 1
            continue

        if not shared_exists:
            shared_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(local_path, shared_path)
            print(f"✓ Synced: {local_file} → shared (new)")
            count += 1
            continue

        # Both exist, compare times
        local_mtime = local_path.stat().st_mtime
        shared_mtime = shared_path.stat().st_mtime

        if file_is_newer(local_mtime, shared_mtime):
            shutil.copy2(local_path, shared_path)
            print(f"✓ Synced: {local_file} → shared (local newer)")
            count += 1
        elif file_is_newer(shared_mtime, local_mtime):
            shutil.copy2(shared_path, local_path)
            print(f"✓ Synced: shared → {local_file} (shared newer)")
            count += 1

    if count == 0:
        if not kwargs.get('suppress_extra', False):
            print("✓ Already up to date")
    else:
        print(f"✓ Synced {count} files")

    return 0

def cmd_check(local_file, **kwargs):
    """Check the status of a file"""
    local_path = Path(local_file)
    if local_path.is_dir():
        return recursive_apply_skips(cmd_check, local_path, **kwargs)

    shared_path = get_shared_path(local_file)
    if shared_path is None:
        return 1

    local_exists = file_exists_and_valid(local_path)
    shared_exists = shared_path.exists()

    print(f"File: {local_file}")
    print(f"Shared path: {shared_path}")
    print()

    if not local_exists and not shared_exists:
        print("Status: ✗ Does not exist in either location")
        return 0

    if not shared_exists:
        print("Status: ⊘ Not shared (only exists locally)")
        if not kwargs.get('suppress_extra', False):
            if local_exists:
                local_time = format_time(local_path.stat().st_mtime)
                print(f"Local: Modified {local_time}")
            print("→ Use 'share put' or 'share push' to share")
        return 0

    if not local_exists:
        print("Status: ⊘ Only in shared (not in local)")
        shared_time = format_time(shared_path.stat().st_mtime)
        if not kwargs.get('suppress_extra', False):
            print(f"Shared: Modified {shared_time}")
            print("→ Use 'share get' or 'share pull' to retrieve")
        return 0

    # Both exist, compare
    local_mtime = local_path.stat().st_mtime
    shared_mtime = shared_path.stat().st_mtime

    local_time_str = format_time(local_mtime)
    shared_time_str = format_time(shared_mtime)

    if not kwargs.get('suppress_extra', False):
        print(f"Local:  Modified {local_time_str}")
        print(f"Shared: Modified {shared_time_str}")
        print()

    if file_is_newer(local_mtime, shared_mtime):
        print("Status: ⚠ Local is newer")
        print("→ Use 'share push' to update shared")
    elif file_is_newer(shared_mtime, local_mtime):
        print("Status: ⚠ Shared is newer")
        print("→ Use 'share pull' to update local")
    else:
        print("Status: ✓ Synced")

    return 0


def cmd_remove(local_file, **kwargs):
    """Remove file from shared location"""
    local_path = Path(local_file)
    if local_path.is_dir():
        return recursive_apply_noskip(cmd_remove, local_path, **kwargs)

    shared_path = get_shared_path(local_file)
    if shared_path is None:
        return 1

    if not shared_path.exists():
        if not kwargs.get('suppress_error', False):
            print(f"File not in shared: {local_file}")
        return 0

    shared_path.unlink()
    print(f"✓ Removed from shared: {shared_path}")

    # Clean up empty parent directories
    try:
        parent = shared_path.parent
        while parent != SHARED_ROOT and not any(parent.iterdir()):
            parent.rmdir()
            parent = parent.parent
    except:
        pass

    return 0


def cmd_status(**kwargs):
    """Show status of entire shared directory"""
    if not SHARED_ROOT.exists():
        if not kwargs.get('suppress_critical', False):
            print(f"Error: Shared directory does not exist\nCreating {SHARED_ROOT}...")
            SHARED_ROOT.mkdir(parents=True, exist_ok=True)
            print(f"Created shared directory: {SHARED_ROOT}")
        else:
            SHARED_ROOT.mkdir(parents=True, exist_ok=True)
        print("No files tracked")
        return 0

    synced = []
    need_push = []
    need_pull = []
    only_shared = []

    # Walk through shared directory
    for shared_file in SHARED_ROOT.rglob('*'):
        if not shared_file.is_file():
            continue

        # Reconstruct local path
        relative = shared_file.relative_to(SHARED_ROOT)
        if SHARE_PATH:
            local_file = SHARE_PATH / relative
        else:
            local_file = Path(relative)

        if not local_file.exists():
            only_shared.append((local_file, shared_file))
            continue

        local_mtime = local_file.stat().st_mtime
        shared_mtime = shared_file.stat().st_mtime

        if file_is_newer(local_mtime, shared_mtime):
            need_push.append(local_file)
        elif file_is_newer(shared_mtime, local_mtime):
            need_pull.append(local_file)
        else:
            synced.append(local_file)

    total = len(synced) + len(need_push) + len(need_pull) + len(only_shared)

    print(f"Shared directory: {SHARED_ROOT}")
    print(f"Local root: {SHARE_PATH if SHARE_PATH else 'Not set'}")
    print(f"Total files tracked: {total}")
    print()

    if kwargs.get('suppress_extra', False):
        return 0

    if synced:
        print(f"✓ Synced: {len(synced)} files")
        for f in synced[:5]:
            print(f"  {f}")
        if len(synced) > 5:
            print(f"  ... and {len(synced) - 5} more")
        print()

    if need_push:
        print(f"⚠ Need push (local newer): {len(need_push)} files")
        for f in need_push:
            print(f"  {f}")
        print()

    if need_pull:
        print(f"⚠ Need pull (shared newer): {len(need_pull)} files")
        for f in need_pull:
            print(f"  {f}")
        print()

    if only_shared:
        print(f"⊘ Only in shared: {len(only_shared)} files")
        for local_f, shared_f in only_shared[:5]:
            print(f"  {local_f}")
        if len(only_shared) > 5:
            print(f"  ... and {len(only_shared) - 5} more")
        print()

    if not (synced or need_push or need_pull or only_shared):
        print("No files tracked")

    return 0


def cmd_list():
    """List all files in shared directory"""
    if not SHARED_ROOT.exists():
        return 1

    for shared_file in SHARED_ROOT.rglob('*'):
        if shared_file.is_file():
            # Show the path relative to SHARED_ROOT, and if SHARE_PATH is set, show as under SHARE_PATH
            relative = shared_file.relative_to(SHARED_ROOT)
            if SHARE_PATH:
                print(SHARE_PATH / relative)
            else:
                print(relative)

    return 0


def main():
    parser = argparse.ArgumentParser(
                description='Share utility - Sync files between local and shared directory (supports multiple files)',
                formatter_class=argparse.RawDescriptionHelpFormatter,
                epilog="""
Customization:
    - To set your local root, create ~/.sharepath containing the absolute path.
    - To set your shared root, create ~/.shareroot containing the absolute path.
    - Only files under SHARE_PATH are managed; they are mapped to SHARED_ROOT
        preserving their relative path under SHARE_PATH.

Commands:
  list                 List all files in shared directory
  put <file> [...]     Copy file(s) to shared (always overwrite)
  push <file> [...]    Copy to shared only if local is newer
  pushall              Push all local files to shared if local is newer
  get <file> [...]     Copy from shared to local (always overwrite)
  pull <file> [...]    Copy from shared only if shared is newer
  pullall              Pull all shared files to local if shared is newer
  sync <file> [...]    Sync by copying whichever is newer
  syncall              Sync all files by copying whichever is newer
  check <file> [...]   Check sync status of file(s)
  rm <file> [...]      Remove file(s) from shared location
  status               Show status of entire shared directory

Examples:
  share put rust/cargo.toml
  share push rust/cargo.toml src/main.rs
  share check rust/cargo.toml src/main.rs
  share list
  share status
        """
    )

    parser.add_argument('command', help='Command to execute')
    parser.add_argument('file', nargs='*', help='File path(s) (required for most commands)')

    if len(sys.argv) == 1:
        parser.print_usage()
        return 0

    args = parser.parse_args()

    command = args.command.lower()
    file_paths = args.file

    # Commands that don't require a file argument
    if command == 'status':
        return cmd_status()
    elif command == 'pushall':
        return cmd_push_all()
    elif command == 'pullall':
        return cmd_pull_all()
    elif command == 'syncall':
        return cmd_sync_all()
    elif command == 'list':
        return cmd_list()

    # Dispatch to appropriate command
    commands = {
        'put': cmd_put,
        'push': cmd_push,
        'get': cmd_get,
        'pull': cmd_pull,
        'sync': cmd_sync,
        'check': cmd_check,
        'rm': cmd_remove,
        'remove': cmd_remove,
    }

    if command not in commands:
        print(f"Error: Unknown command '{command}'")
        print("Use 'share --help' for usage information")
        return 1
    
    if not file_paths:
        print(f"Error: '{command}' require at least one file path argument")
        return 1

    if len(file_paths) > 1:
        # Multiple files
        res = 0
        for f in file_paths:
            res += commands[command](f)
        if res != 0:
            print(f"⚠ '{command}' completed with {res} errors")
            return 1
        return 0
    else:
        # Single file
        return commands[command](file_paths[0])


if __name__ == "__main__":
    sys.exit(main())
