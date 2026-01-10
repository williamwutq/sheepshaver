#!/usr/bin/env python3
"""
Share utility - Sync files between local filesystem and ~/Shared/dump
"""

import sys
import os
from pathlib import Path
import shutil
from datetime import datetime
import argparse

SHARED_ROOT = Path.home() / "Shared" / "dump"


def get_shared_path(local_path):
    """Convert local path to shared path maintaining full directory structure"""
    if not local_path:
        return None
    abs_path = Path(local_path).resolve()
    # Remove leading / to make it relative for joining with SHARED_ROOT
    relative = str(abs_path).lstrip('/')
    return SHARED_ROOT / relative


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


def cmd_put(local_file):
    """Copy local file to shared (always overwrite)"""
    local_path = Path(local_file)

    if not file_exists_and_valid(local_path):
        print(f"Error: Local file does not exist: {local_file}")
        return 1

    shared_path = get_shared_path(local_file)
    shared_path.parent.mkdir(parents=True, exist_ok=True)

    shutil.copy2(local_path, shared_path)
    print(f"✓ Put: {local_file} → {shared_path}")
    return 0


def cmd_push(local_file):
    """Copy local file to shared only if local is newer"""
    local_path = Path(local_file)

    if not file_exists_and_valid(local_path):
        print(f"Error: Local file does not exist: {local_file}")
        return 1

    shared_path = get_shared_path(local_file)

    # If shared doesn't exist, always push
    if not shared_path.exists():
        shared_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(local_path, shared_path)
        print(f"✓ Pushed: {local_file} → {shared_path} (new)")
        return 0

    # Compare modification times
    local_mtime = local_path.stat().st_mtime
    shared_mtime = shared_path.stat().st_mtime

    if local_mtime > shared_mtime:
        shutil.copy2(local_path, shared_path)
        print(f"✓ Pushed: {local_file} (local newer)")
        return 0
    else:
        print(f"⊘ Not pushed: {local_file} (shared is newer or same)")
        return 0


def cmd_get(local_file):
    """Copy shared file to local (always overwrite)"""
    local_path = Path(local_file)
    shared_path = get_shared_path(local_file)

    if not shared_path.exists():
        print(f"Error: File not shared: {local_file}")
        return 1

    local_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(shared_path, local_path)
    print(f"✓ Got: {shared_path} → {local_file}")
    return 0


def cmd_pull(local_file):
    """Copy shared file to local only if shared is newer"""
    local_path = Path(local_file)
    shared_path = get_shared_path(local_file)

    if not shared_path.exists():
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

    if shared_mtime > local_mtime:
        shutil.copy2(shared_path, local_path)
        print(f"✓ Pulled: {local_file} (shared newer)")
        return 0
    else:
        print(f"⊘ Not pulled: {local_file} (local is newer or same)")
        return 0


def cmd_sync(local_file):
    """Sync by copying whichever version is newer"""
    local_path = Path(local_file)
    shared_path = get_shared_path(local_file)

    local_exists = file_exists_and_valid(local_path)
    shared_exists = shared_path.exists()

    # If neither exists, error
    if not local_exists and not shared_exists:
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

    if local_mtime > shared_mtime:
        shutil.copy2(local_path, shared_path)
        print(f"✓ Synced: {local_file} → shared (local newer)")
        return 0
    elif shared_mtime > local_mtime:
        shutil.copy2(shared_path, local_path)
        print(f"✓ Synced: shared → {local_file} (shared newer)")
        return 0
    else:
        print(f"✓ Already synced: {local_file}")
        return 0


def cmd_check(local_file):
    """Check the status of a file"""
    local_path = Path(local_file)
    shared_path = get_shared_path(local_file)

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
        if local_exists:
            local_time = format_time(local_path.stat().st_mtime)
            print(f"Local: Modified {local_time}")
        print("→ Use 'share put' or 'share push' to share")
        return 0

    if not local_exists:
        print("Status: ⊘ Only in shared (not in local)")
        shared_time = format_time(shared_path.stat().st_mtime)
        print(f"Shared: Modified {shared_time}")
        print("→ Use 'share get' or 'share pull' to retrieve")
        return 0

    # Both exist, compare
    local_mtime = local_path.stat().st_mtime
    shared_mtime = shared_path.stat().st_mtime

    local_time_str = format_time(local_mtime)
    shared_time_str = format_time(shared_mtime)

    print(f"Local:  Modified {local_time_str}")
    print(f"Shared: Modified {shared_time_str}")
    print()

    time_diff = abs(local_mtime - shared_mtime)

    if time_diff < 1:  # Less than 1 second difference
        print("Status: ✓ Synced")
    elif local_mtime > shared_mtime:
        print("Status: ⚠ Local is newer")
        print("→ Use 'share push' to update shared")
    else:
        print("Status: ⚠ Shared is newer")
        print("→ Use 'share pull' to update local")

    return 0


def cmd_remove(local_file):
    """Remove file from shared location"""
    shared_path = get_shared_path(local_file)

    if not shared_path.exists():
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


def cmd_status():
    """Show status of entire shared directory"""
    if not SHARED_ROOT.exists():
        print(f"Error: Shared directory does not exist\nCreating {SHARED_ROOT}...")
        SHARED_ROOT.mkdir(parents=True, exist_ok=True)
        print(f"Created shared directory: {SHARED_ROOT}")
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
        local_file = Path('/') / relative

        if not local_file.exists():
            only_shared.append((local_file, shared_file))
            continue

        local_mtime = local_file.stat().st_mtime
        shared_mtime = shared_file.stat().st_mtime

        time_diff = abs(local_mtime - shared_mtime)

        if time_diff < 1:
            synced.append(local_file)
        elif local_mtime > shared_mtime:
            need_push.append(local_file)
        else:
            need_pull.append(local_file)

    total = len(synced) + len(need_push) + len(need_pull) + len(only_shared)

    print(f"Shared directory: {SHARED_ROOT}")
    print(f"Total files tracked: {total}")
    print()

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


def main():
    parser = argparse.ArgumentParser(
        description='Share utility - Sync files between local and ~/Shared/dump',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  put <file>     Copy file to shared (always overwrite)
  push <file>    Copy to shared only if local is newer
  get <file>     Copy from shared to local (always overwrite)
  pull <file>    Copy from shared only if shared is newer
  sync <file>    Sync by copying whichever is newer
  check <file>   Check sync status of file
  rm <file>      Remove file from shared location
  status         Show status of entire shared directory

Examples:
  share put rust/cargo.toml
  share push rust/cargo.toml
  share check rust/cargo.toml
  share status
        """
    )

    parser.add_argument('command', help='Command to execute')
    parser.add_argument('file', nargs='?', help='File path (required for most commands)')

    if len(sys.argv) == 1:
        parser.print_help()
        return 0

    args = parser.parse_args()

    command = args.command.lower()
    file_path = args.file

    # Commands that don't require a file argument
    if command == 'status':
        return cmd_status()

    # All other commands require a file argument
    if not file_path:
        print(f"Error: '{command}' requires a file argument")
        return 1

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

    return commands[command](file_path)


if __name__ == "__main__":
    sys.exit(main())
