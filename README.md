# share (File Sharing Utility)

A simple utility to sync files between a local directory tree and a shared directory, preserving relative paths. Useful for sharing files between different users or systems.

This is entirely local and does not require any network setup or cloud services. It only manages files under a configurable local root directory (SHARE_PATH) and syncs them to/from a shared root directory (SHARED_ROOT).

## Intention
Personally, I run dual boot macOS and Linux on my laptop. I wanted a simple way to share files between the two OSes without relying on cloud services or complex network setups. This utility allows me to easily push and pull files to a shared directory that both OSes can access.

I also own a server, where many users access, and it has became tedious to manually manage file sharing between different users. This utility can also be used to sync files between a user's home directory and a shared directory on the server, or a computer in general.

Talking about content sharing and syncing, many people intuitively think of git. However, git is not designed for simple file sharing and syncing. It introduces unnecessary complexity with version control, branching, and merging, which are not needed for basic file sharing tasks. This utility focuses on simplicity and ease of use for straightforward file synchronization.

## Simple Installation
Run on the command line:
```bash
curl -fsSL https://raw.githubusercontent.com/williamwutq/sheepshaver/main/install.sh | bash -s share
```

## Clone and Install Manually
```bash
git clone https://www.github.com/williamwutq/sheepshaver
cd sheepshaver
sudo cp share.py /usr/local/bin/share
chmod +x /usr/local/bin/share
sudo cp share.1 /usr/local/share/man/man1/share.1
```

## Features
- Sync files between your local directory and a shared directory
- Only manages files under a configurable local root (SHARE_PATH)
- Shared root (SHARED_ROOT) is also configurable
- Supports push, pull, put, get, sync, check, remove, and status commands
- Supports multiple files and directories as input for most commands
- Configurable ignore patterns similar to .gitignore
- Informative output with configurable verbosity levels

## Configuration
- Set your local root by creating a file `~/.sharepath` containing the absolute path
- Set your shared root by creating a file `~/.shareroot` containing the absolute path (defaults to `~/Shared/dump` if not set)
- Configurable ignore patterns via `~/.shareignore` (similar to .gitignore)
- Only files under SHARE_PATH are managed; attempts to share files outside this path will be rejected
- Most commands support specifying multiple files at once (e.g., `share put file1 file2 file3`)

## Flags
- `--suppress-extra` / `--no-extra` / `-next` / `-sext`: Suppress extra informational messages
- `--suppress-error` / `--no-error` / `-nerr` / `-serr`: Suppress error messages
- `--suppress-critical` / `--no-critical` / `-ncrt` / `-scrt`: Suppress critical error messages
- `--suppress` / `--no` / `-no` / `-s`: Suppress all messages except critical errors
- `--ignore` / `-i`: Add ignore pattern (can be used multiple times)

## Usage
```
share list                   # List all files in shared directory.
share put <file> [...]       # Copy file(s) to shared (always overwrite). If input is a directory, put all files under it.
share push <file> [...]      # Copy to shared only if local is newer. If input is a directory, push all files under it.
share pushall                # Push all local files to shared if local is newer
share get <file> [...]       # Copy from shared to local (always overwrite).
share pull <file> [...]      # Copy from shared only if shared is newer. If input is a directory, pull all files under it.
share pullall                # Pull all shared files to local if shared is newer.
share sync <file> [...]      # Sync by copying whichever is newer. If input is a directory, sync all files under it.
share syncall                # Sync all files by copying whichever is newer.
share check <file> [...]     # Check sync status of file(s). If input is a directory, check all files under it.
share rm <file> [...]        # Remove file(s) from shared location. If input is a directory, remove all files under it.
share status                 # Show status of entire shared directory
```

## Example
```
share put rust/cargo.toml
share push rust/cargo.toml src/main.rs
share check rust/cargo.toml src/main.rs
share list
share status
```

## Man Page
A man page is included for detailed usage instructions. Access it via:
```
man share
```

## License
GPLv2 or later

## Author
William Wu, 2026
