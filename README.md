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
- `--yes` / `-y`: Automatic yes to prompts (for auto command)

## Usage
```
share <path>                 # A shortcut for 'share sync <path>'. Works only for a single path.
share info                   # Show configuration information.
share auto                   # Perform automatic actions based on current directory context.
share list                   # List all files in shared directory.
share put <path> [...]       # Copy file(s) to shared (always overwrite). If input is a directory, put all files under it.
share push <path> [...]      # Copy to shared only if local is newer. If input is a directory, push all files under it.
share pushall                # Push all local files to shared if local is newer
share get <path> [...]       # Copy from shared to local (always overwrite).
share pull <path> [...]      # Copy from shared only if shared is newer. If input is a directory, pull all files under it.
share pullall                # Pull all shared files to local if shared is newer.
share sync <path> [...]      # Sync by copying whichever is newer. If input is a directory, sync all files under it.
share syncall                # Sync all files by copying whichever is newer.
share check <path> [...]     # Check sync status of file(s). If input is a directory, check all files under it.
share rm <path> [...]        # Remove file(s) from shared location. If input is a directory, remove all files under it.
share audit <path> [...]     # Audit local file(s) to check on files marked as synced. If input is a directory, audit all files under it.
share auditall               # Audit entire shared directory to verify synced files.
share status [dir ...]       # Show status of local directory (or directories). If no dir specified, show status of all tracked files.
share preview <cmd> [...]    # Preview the specified command without making changes.
```

## Example
```
share put rust/cargo.toml
share README.md
share push rust/cargo.toml src/main.rs
share check rust/cargo.toml src/main.rs
share list
share status
share status rust src
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

## More On: The Name

The name "sheepshaver" is inspired by the classic Macintosh emulator "SheepShaver," which allowed users to run older Mac OS versions on modern hardware. The origial inspiration behind the utility was to facilitate file sharing between dual-boot systems, similar to how SheepShaver bridged the gap between old and new Mac environments. The purpose of this utility is now extended to general local file sharing scenarios, but the name still reflects the philosophy of bridging different environments in a simple and effective way.

## More On: Python

Currently, sheepshaver is implemented in Python for its ease of use, readability, and cross-platform compatibility. This make writing and maintaining the codebase simpler, especially for a command-line utility that needs to run on various Unix-like systems.

In the future, if performance becomes a concern or if there is a need for tighter integration with system-level features, it will be rewriten in Rust. However, most users have python installed by default and the python inplementation have not shown any significant performance issues for typical use cases.

## More On: Why This Exists

This is written to solve a specific kind of problem that comes up often on Unix-like systems, but is rarely addressed directly:  
moving files **locally** and **predictably** between two places on the same machine or storage device without the overhead of version control or networked file systems.

Sure, running a bunch of `mv` or `cp` commands can work, but it quickly becomes tedious and error-prone, especially when dealing with many files or complex directory structures. Existing tools like `rsync` are powerful but they are not only overkill for simple use cases, but also often not configurable enough to handle specific local sharing scenarios without additional scripting.

The problem with version control systems like Git, Mercurial, or SVN is that they introduce complexity and overhead that is unnecessary for simple file sharing tasks and don't work well for binary files or large files that change frequently. They offer tools to resolve conflicts, manage branches, and track history, which are not needed when the goal is simply to keep files in sync between two locations and conflicts are rare or non-existent.

The problem with networked file systems or cloud storage solutions is that they require network connectivity, setup, and maintenance. They also often introduce latency and reduce privacy, which may not be acceptable in certain scenarios. sheepshaver is entirely local and requires no network setup beyound mounting devices.

This tool assumes the filesystem is the source of truth, and that the user knows when files should be shared. Actions are explicit and no background processes run. There is no hidden database or index, and everything can be inspected with standard filesystem tools.

The tool is for developers and power users who prefer command line interfaces and value simplicity, transparency, and control over convenience or automation. sheepshaver follows the Unix philosophy of building small, focused, well-documented tools that do one thing well and can be combined with other tools. This is why a man page is provided and the interface is currently command line only. A GUI or TUI application could be built on top of this tool if desired.

### Dual-boot systems

On dual-boot machines (for example macOS to Linux or Linux to Linux):

- A single partition is often shared between operating systems, often formatted as exFAT, FAT32, or NTFS
- The same files are edited from different environments
- Paths and directory layouts need to stay identical
- Network services, repositories, or background sync are unnecessary because the files are on the same physical device and they are never accessed simultaneously

sheepshaver treats the shared partition as just another filesystem tree.  
Files are copied by relative path, timestamps are compared, and actions are explicit.

Once mounted, it is recommended to create a `shared` directory in the shared partition, and set that as the SHARED_ROOT using the `.shareroot` configuration file. Nothing runs on the background and no further configuration is needed.

### Sharing files between users on one machine

On multi-user systems such as servers, lab machines, or shared workstations:

- Users need access to common data
- Some files are large, binary, or transient
- Version control is often unnecessary or impractical
- Network services or cloud storage cannot be used due to security or privacy concerns

sheepshaver allows users to easily push and pull files to a shared directory that is accessible by multiple users. Each user can have their own local root directory, and the shared root can be a common directory on the system. There is no central index, no per-user database, and no long-running process. Everything can be inspected with standard tools.

### External drives and removable media

On systems where external drives or removable media are used for file sharing:

- External SSDs
- USB drives
- Offline or air-gapped systems
- Periodic, intentional copying

Often the content needed for copying is not continuously changing, so copying entire directories back and forth is inefficient. Often, not all files in a directory can be shared, so selective copying is needed. sheepshaver allows users to easily manage which files are shared to and from the external drive, using simple commands to push, pull, and sync files as needed.

sheepshaver stores no additional metadata beyond what is already present in the filesystem (timestamps, paths). This makes it easy to use with any file system and removable media, as there is no need to maintain a separate database or index.

### How sheepshaver approaches the problem

sheepshaver is built around a few simple ideas:

- The filesystem is powerful and sufficient
- Explicitness is better than magic
- Simplicity is a virtue
- Compatibility arises from basic operations
- Software should give transparency and freedom to the user

In practice, this means:

- Files live under well-defined roots
- Relative paths are preserved
- Most operations are decided using metadata
- Expensive verification is explicit and opt-in
- No daemon or background process runs
- No hidden databases or indexes are created
- Nothing happens unless the user asks for it
- Commands are simple and composable
- Released under a permissive license (GPLv2 or later)
- Command line interface only, no GUI