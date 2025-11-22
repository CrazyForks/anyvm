#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import sys
import os
import platform
import subprocess
import time
import socket
import json
import getpass
import shutil
import shlex
import re
import threading

# Python 2/3 compatibility for urllib and input
try:
    # Python 3
    from urllib.request import urlopen, Request, urlretrieve
    from urllib.error import HTTPError, URLError
    input_func = input
except ImportError:
    # Python 2
    from urllib2 import urlopen, Request, HTTPError, URLError
    
    def urlretrieve(url, filename, reporthook=None):
        try:
            u = urlopen(url)
            total_size = 0
            try:
                total_size = int(u.headers.get('Content-Length'))
            except Exception:
                total_size = 0
            block_num = 0
            with open(filename, 'wb') as f:
                while True:
                    chunk = u.read(8192)
                    if not chunk:
                        if reporthook:
                            reporthook(block_num, 8192, total_size)
                        break
                    f.write(chunk)
                    if reporthook:
                        reporthook(block_num, len(chunk), total_size)
                    block_num += 1
        except Exception as e:
            raise e
    
    try:
        input_func = raw_input
    except NameError:
        input_func = input

IS_WINDOWS = (os.name == 'nt')

try:
    DEVNULL = subprocess.DEVNULL  # Python 3.3+
except AttributeError:
    DEVNULL = open(os.devnull, 'wb')

SSH_KNOWN_HOSTS_NULL = "NUL" if IS_WINDOWS else "/dev/null"

OPENBSD_E1000_RELEASES = {"7.3", "7.4", "7.5", "7.6"}
VERSION_TOKEN_RE = re.compile(r"[0-9]+|[A-Za-z]+")


def removesuffix(text, suffix):
    """Compatibility helper mirroring str.removesuffix."""
    if not suffix:
        return text
    if hasattr(text, "removesuffix"):
        return text.removesuffix(suffix)
    if text.endswith(suffix):
        return text[:-len(suffix)]
    return text

def format_command_for_display(cmd_list):
    """Pretty-print the QEMU command with platform-appropriate quoting."""
    if IS_WINDOWS:
        def quote(arg):
            if not arg:
                return '""'
            if any(ch in arg for ch in ' \t"'):
                return '"' + arg.replace('"', '""') + '"'
            return arg
        joiner = " ^\n  "
        return joiner.join(quote(arg) for arg in cmd_list)
    return " \\\n  ".join(shlex.quote(arg) for arg in cmd_list)

def log(msg):
    print(msg)

def fatal(msg):
    print("Error: {}".format(msg), file=sys.stderr)
    sys.exit(1)

def print_usage():
    print("""
Usage: python qemu.py [OPTIONS]

Description:
  Automated QEMU VM launcher script. Downloads images/keys and boots a VM 
  with SSH access and folder synchronization.

Options:
  --os <name>            Operating System name (Required).
                         Supported: freebsd, openbsd, netbsd, dragonflybsd, solaris
  --release <ver>        OS Release version (e.g., 15.0, 7.4). 
                         If invalid or omitted, tries to detect from available releases.
  --arch <arch>          Architecture: x86_64 or aarch64.
                         Default: Host architecture.
  --mem <MB>             Memory size in MB (Default: 2048).
  --cpu <num>            Number of CPU cores (Default: 2).
  --cpu-type <type>      Specific CPU model (e.g., cortex-a72, host).
  --nc <type>            Network card model (e.g., virtio-net-pci, e1000).
  --sshport <port>       Host port forwarding for SSH (Default: auto-detected free port).
  --serial <port>        Expose the VM serial console on the given TCP port (auto-select starting 7000 if omitted).
  -p <mapping>           Custom port mapping. Can be used multiple times.
                         Formats: host:guest, tcp:host:guest, udp:host:guest.
                         Example: -p 8080:80 -p udp:3000:3000
  -v <mapping>           Folder synchronization. Can be used multiple times.
                         Format: /host/path:/guest/path
                         Example: -v /home/user/data:/mnt/data
  --sync <mode>          Synchronization mode for -v folders.
                         Supported: sshfs (default), nfs, rsync, scp.
                         Note: sshfs/nfs/rsync not supported on Windows hosts.
  --workingdir <dir>     Directory to store images and metadata (Default: ./output).
  --disktype <type>      Disk interface type (e.g., virtio, ide).
                         Default: virtio (ide for dragonflybsd).
  --uefi                 Enable UEFI boot (Implicit for FreeBSD).
  --vnc <display>        Enable VNC on specified display (e.g., 0 for :0).
  --mon <port>           QEMU monitor telnet port (localhost).
  --public               Listen on 0.0.0.0 for mapped ports instead of 127.0.0.1.
  --whpx                 (Windows) Attempt to use WHPX acceleration instead of TCG.
  --detach, -d           Run QEMU in background.
  --console, -c          Run QEMU in foreground (console mode).
  --builder <ver>        Specify a specific vmactions builder version tag.
  --help, -h             Show this help message.

Examples:
  # Basic FreeBSD VM
  python qemu.py --os freebsd --release 14.0

  # ARM64 VM on x86_64 host with port mapping and folder sync
  python qemu.py --os openbsd --arch aarch64 -p 8080:80 -v $(pwd):/data

  # Windows host using SCP sync
  python qemu.py --os solaris --sync scp -v D:\\data:/data

""")

def get_free_port(start=10022, end=20000):
    for port in range(start, end):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        try:
            s.bind(('0.0.0.0', port))
            s.close()
            return port
        except socket.error:
            continue
    return None


def get_free_vnc_display(bind_addr, start=0, end=100):
    addr = bind_addr or "0.0.0.0"
    for disp in range(start, end):
        port = 5900 + disp
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        try:
            s.bind((addr, port))
            s.close()
            return disp
        except socket.error:
            continue
    return None

def fetch_url_content(url):
    attempts = 5
    for attempt in range(attempts):
        req = Request(url)
        req.add_header('User-Agent', 'python-qemu-script')
        try:
            resp = urlopen(req)
            return resp.read().decode('utf-8')
        except HTTPError as e:
            if e.code == 404:
                return None
        except Exception:
            pass
        if attempt < attempts - 1:
            time.sleep(3)
    return None

def get_remote_file_info(url):
    req = Request(url)
    req.add_header('User-Agent', 'python-qemu-script')
    if hasattr(req, 'method'):
        req.method = 'HEAD'
    else:
        try:
            req.get_method = lambda: 'HEAD'
        except Exception:
            pass
    try:
        resp = urlopen(req)
        length = int(resp.headers.get('Content-Length', '0'))
        accept_ranges = resp.headers.get('Accept-Ranges', '').lower() == 'bytes'
        try:
            resp.close()
        except Exception:
            pass
        return length, accept_ranges
    except Exception:
        return 0, False

def download_file_multithread(url, dest, total_size, show_progress):
    tmp_dest = dest + ".part"
    try:
        with open(tmp_dest, 'wb') as f:
            f.truncate(total_size)
    except IOError:
        return False

    num_threads = min(4, max(1, total_size // (8 * 1024 * 1024)))
    chunk_size = (total_size + num_threads - 1) // num_threads
    progress_lock = threading.Lock()
    downloaded = [0]
    last_percent = [-1]
    errors = []
    stop_event = threading.Event()

    def update_progress():
        if not show_progress:
            return
        percent = int(downloaded[0] * 100 / total_size)
        if percent != last_percent[0]:
            last_percent[0] = percent
            sys.stdout.write("\r  {:3d}% ({:.1f}/{:.1f} MB)".format(
                percent,
                downloaded[0] / (1024 * 1024.0),
                total_size / (1024 * 1024.0)
            ))
            sys.stdout.flush()

    def worker(start, end):
        if stop_event.is_set():
            return
        req = Request(url)
        req.add_header('User-Agent', 'python-qemu-script')
        req.add_header('Range', 'bytes={}-{}'.format(start, end))
        try:
            resp = urlopen(req)
            with open(tmp_dest, 'r+b') as f:
                f.seek(start)
                while not stop_event.is_set():
                    chunk = resp.read(128 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)
                    if show_progress:
                        with progress_lock:
                            downloaded[0] += len(chunk)
                            update_progress()
            try:
                resp.close()
            except Exception:
                pass
        except Exception as e:
            stop_event.set()
            with progress_lock:
                errors.append(e)

    threads = []
    for index in range(num_threads):
        start = index * chunk_size
        end = min(total_size - 1, start + chunk_size - 1)
        if start > end:
            break
        t = threading.Thread(target=worker, args=(start, end))
        t.daemon = True
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    if show_progress:
        sys.stdout.write("\n")
        sys.stdout.flush()

    if errors or stop_event.is_set():
        try:
            os.remove(tmp_dest)
        except OSError:
            pass
        return False

    try:
        if hasattr(os, 'replace'):
            os.replace(tmp_dest, dest)
        else:
            shutil.move(tmp_dest, dest)
    except Exception:
        return False
    return True

def download_file(url, dest):
    log("Downloading " + url)
    show_progress = sys.stdout.isatty()

    size, can_range = get_remote_file_info(url)
    if can_range and size > 0:
        if download_file_multithread(url, dest, size, show_progress):
            return True
        log("Falling back to single-thread download...")

    def make_progress_hook():
        if not show_progress:
            return None
        last_msg = {'percent': -1}

        def hook(block_num, block_size, total_size):
            downloaded = block_num * block_size
            if total_size > 0:
                percent = min(100, int(downloaded * 100 / total_size))
                if percent == last_msg['percent']:
                    return
                last_msg['percent'] = percent
                sys.stdout.write("\r  {:3d}% ({:.1f}/{:.1f} MB)".format(
                    percent,
                    downloaded / (1024 * 1024.0),
                    total_size / (1024 * 1024.0)
                ))
            else:
                sys.stdout.write("\r  {:.1f} MB".format(downloaded / (1024 * 1024.0)))
            sys.stdout.flush()

        return hook

    for i in range(5):
        hook = make_progress_hook()
        try:
            if hook:
                urlretrieve(url, dest, hook)
                sys.stdout.write("\n")
            else:
                urlretrieve(url, dest)
            return True
        except Exception:
            if hook:
                sys.stdout.write("\n")
            time.sleep(2)
    return False


def url_exists(url):
    req = Request(url)
    req.add_header('User-Agent', 'python-qemu-script')
    if not hasattr(req, 'method'):
        try:
            req.get_method = lambda: 'HEAD'
        except Exception:
            pass
    else:
        req.method = 'HEAD'
    try:
        urlopen(req)
        return True
    except HTTPError as e:
        if e.code == 404:
            return False
        return False
    except URLError:
        return False


def download_optional_parts(base_url, base_path, max_parts=9):
    for idx in range(1, max_parts + 1):
        part_url = "{}.{}".format(base_url, idx)
        if not url_exists(part_url):
            break
        log("Appending extra part: " + part_url)
        if not append_url_to_file(part_url, base_path):
            log("Warning: Failed to append optional part {}".format(part_url))
            break


def append_url_to_file(url, dest_path):
    req = Request(url)
    req.add_header('User-Agent', 'python-qemu-script')
    try:
        resp = urlopen(req)
    except Exception:
        return False

    try:
        with open(dest_path, 'ab') as f_main:
            start_pos = f_main.tell()
            try:
                while True:
                    chunk = resp.read(1024 * 1024)
                    if not chunk:
                        break
                    f_main.write(chunk)
            except Exception:
                f_main.truncate(start_pos)
                return False
    finally:
        try:
            resp.close()
        except Exception:
            pass
    return True

def create_sized_file(path, size_mb):
    """Creates a zero-filled file of size_mb."""
    chunk_size = 1024 * 1024 # 1MB
    try:
        with open(path, 'wb') as f:
            zeros = b'\0' * chunk_size
            for _ in range(size_mb):
                f.write(zeros)
    except IOError as e:
        fatal("Failed to create file {}: {}".format(path, e))

def copy_content_to_file(src, dest):
    """Copies content from src to the beginning of dest (like dd conv=notrunc)."""
    try:
        with open(src, 'rb') as f_src:
            content = f_src.read()
        
        # Open dest in read-write binary mode to overwrite without truncating
        with open(dest, 'r+b') as f_dest:
            f_dest.write(content)
    except IOError as e:
        fatal("Failed to copy content from {} to {}: {}".format(src, dest, e))

def find_qemu(binary_name):
    """Finds QEMU binary in PATH or default Windows location."""
    path = None
    # Try shutil.which (Python 3.3+)
    if hasattr(shutil, 'which'):
        path = shutil.which(binary_name)
    else:
        # Python 2 fallback
        try:
            from distutils.spawn import find_executable
            path = find_executable(binary_name)
        except ImportError:
            pass
    
    if path:
        return path
        
    if IS_WINDOWS:
        # Try default install location
        # Handle standard Program Files
        prog_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        candidate = os.path.join(prog_files, "qemu", binary_name + ".exe")
        if os.path.exists(candidate):
            return candidate
            
        # Handle x86 Program Files (less likely for 64-bit qemu but possible)
        prog_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
        candidate_x86 = os.path.join(prog_files_x86, "qemu", binary_name + ".exe")
        if os.path.exists(candidate_x86):
            return candidate_x86
            
    return None

def sync_sshfs(ssh_cmd, vhost, vguest, os_name):
    """Mounts a host directory into the guest using SSHFS."""
    if IS_WINDOWS:
        log("Warning: SSHFS sync not supported on Windows host.")
        return

    mount_script = """
mkdir -p "{vguest}"
if [ "{os}" = "netbsd" ]; then
  if ! /usr/sbin/mount_psshfs host:"{vhost}" "{vguest}" >/dev/null 2>&1; then
    exit 1
  fi
else
  if [ "{os}" = "freebsd" ]; then
    kldload fusefs || true
  fi
  if sshfs -o reconnect,ServerAliveCountMax=2,allow_other,default_permissions host:"{vhost}" "{vguest}" ; then
    /sbin/mount || mount
  else
    exit 1
  fi
fi
""".format(vguest=vguest, vhost=vhost, os=os_name)

    mounted = False
    for _ in range(10):
        p_mount = subprocess.Popen(ssh_cmd + ["sh"], stdin=subprocess.PIPE)
        p_mount.communicate(input=mount_script.encode('utf-8'))
        if p_mount.returncode == 0:
            mounted = True
            break
        log("SSHFS mount failed, retrying...")
        time.sleep(2)
    
    if not mounted:
        log("Warning: Failed to mount shared folder via sshfs.")

def sync_nfs(ssh_cmd, vhost, vguest, os_name, sudo_cmd):
    """Configures host NFS exports and mounts in guest."""
    if IS_WINDOWS:
        log("Warning: NFS sync not supported on Windows host.")
        return

    # Host side configuration
    uid = os.getuid()
    gid = os.getgid()
    entry_line = "{} *(rw,insecure,async,no_subtree_check,anonuid={},anongid={})".format(vhost, uid, gid)
    
    need_add = True
    try:
        if os.path.exists("/etc/exports"):
            with open("/etc/exports", "r") as f:
                if vhost in f.read():
                    need_add = False
    except:
        pass

    if need_add:
        log("Configuring NFS export on host (requires sudo)...")
        if sudo_cmd or os.geteuid() == 0:
            cmd_write = sudo_cmd + ["tee", "-a", "/etc/exports"]
            p_write = subprocess.Popen(cmd_write, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            p_write.communicate(input=(entry_line + "\n").encode('utf-8'))
            
            if p_write.returncode == 0:
                subprocess.call(sudo_cmd + ["exportfs", "-a"])
                if subprocess.call(sudo_cmd + ["service", "nfs-server", "restart"]) != 0:
                        subprocess.call(sudo_cmd + ["systemctl", "restart", "nfs-server"])
            else:
                log("Failed to write to /etc/exports")
        else:
            log("Warning: Cannot configure NFS without sudo/root.")

    # Guest side mounting
    mount_script = """
mkdir -p "{vguest}"
if [ "{os}" = "openbsd" ]; then
  mount -t nfs -o -T 192.168.122.2:"{vhost}" "{vguest}"
elif [ -e "/sbin/mount" ]; then
  /sbin/mount 192.168.122.2:"{vhost}" "{vguest}"
else
  mount 192.168.122.2:"{vhost}" "{vguest}"
fi
""".format(vguest=vguest, vhost=vhost, os=os_name)

    mounted = False
    for _ in range(10):
        p_mount = subprocess.Popen(ssh_cmd + ["sh"], stdin=subprocess.PIPE)
        p_mount.communicate(input=mount_script.encode('utf-8'))
        if p_mount.returncode == 0:
            mounted = True
            break
        log("NFS mount failed, retrying...")
        time.sleep(2)
    
    if not mounted:
        log("Warning: Failed to mount shared folder via NFS.")

def sync_rsync(ssh_cmd, vhost, vguest, os_name):
    """Syncs a host directory to the guest using rsync (Pull mode)."""
    if IS_WINDOWS:
        log("Warning: Rsync pull sync not supported on Windows host.")
        return

    log("Syncing via rsync: {} -> {}".format(vhost, vguest))
    
    mount_script = """
mkdir -p "{vguest}"
if command -v rsync >/dev/null 2>&1; then
  rsync -avrtopg --delete host:"{vhost}/" "{vguest}/"
else
  echo "Error: rsync not found in guest."
  exit 1
fi
""".format(vguest=vguest, vhost=vhost)

    synced = False
    for _ in range(10):
        p_sync = subprocess.Popen(ssh_cmd + ["sh"], stdin=subprocess.PIPE)
        p_sync.communicate(input=mount_script.encode('utf-8'))
        if p_sync.returncode == 0:
            synced = True
            break
        log("Rsync sync failed, retrying...")
        time.sleep(2)
    
    if not synced:
        log("Warning: Failed to sync shared folder via rsync.")

def sync_scp(ssh_cmd, vhost, vguest, sshport, hostid_file):
    """Syncs via scp (Push mode from host to guest)."""
    log("Syncing via scp: {} -> {}".format(vhost, vguest))
    
    # Ensure destination directory exists in guest
    try:
         # ssh_cmd is like ['ssh', ..., 'root@localhost']
         # We append mkdir command
         subprocess.call(ssh_cmd + ["mkdir", "-p", vguest])
    except Exception:
         pass

    # SCP command to push files
    # Added -O option for legacy protocol support
    cmd = [
        "scp", "-r", "-q", "-O",
        "-P", str(sshport),
        "-i", hostid_file,
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile={}".format(SSH_KNOWN_HOSTS_NULL),
        "-o", "LogLevel=ERROR",
        os.path.join(vhost, "."),
        "root@localhost:" + vguest + "/"
    ]
    
    if subprocess.call(cmd) != 0:
        log("Warning: SCP sync failed.")

def version_tokens(text):
    if not text:
        return []
    tokens = []
    for token in VERSION_TOKEN_RE.findall(text):
        if token.isdigit():
            tokens.append((0, int(token)))
        else:
            tokens.append((1, token.lower()))
    return tokens


def cmp_version(a, b):
    parts_a = version_tokens(a)
    parts_b = version_tokens(b)
    max_len = max(len(parts_a), len(parts_b))
    parts_a += [(0, 0)] * (max_len - len(parts_a))
    parts_b += [(0, 0)] * (max_len - len(parts_b))
    if parts_a > parts_b:
        return 1
    if parts_a < parts_b:
        return -1
    return 0



def main():
    # Default configuration
    config = {
        'mem': "2048",
        'cpu': "2",
        'cputype': "",
        'nc': "",
        'sshport': "",
        'console': False,
        'useefi': False,
        'detach': False,
        'vpaths': [],
        'ports': [],
        'vnc': "",
        'sync': "sshfs",
        'qmon': "",
        'disktype': "",
        'public': False,
        'os': "",
        'release': "",
        'arch': "",
        'builder': "",
        'whpx': False,
        'serialport': ""
    }

    script_home = os.path.dirname(os.path.abspath(__file__))
    working_dir = os.path.join(script_home, "output")
    
    if os.environ.get("GOOGLE_CLOUD_SHELL") == "true":
        working_dir = "/tmp/qemu.sh"
        if not os.path.exists(working_dir):
            os.makedirs(working_dir)

    # Manual argument parsing
    args = sys.argv[1:]
    
    if len(args) == 0 or "--help" in args or "-h" in args:
        print_usage()
        sys.exit(0)

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--os":
            config['os'] = args[i+1]
            i += 1
        elif arg == "--release":
            config['release'] = args[i+1]
            i += 1
        elif arg == "--arch":
            config['arch'] = args[i+1]
            i += 1
        elif arg == "--mem":
            config['mem'] = args[i+1]
            i += 1
        elif arg == "--cpu":
            config['cpu'] = args[i+1]
            i += 1
        elif arg == "--cpu-type":
            config['cputype'] = args[i+1]
            i += 1
        elif arg == "--workingdir":
            working_dir = args[i+1]
            i += 1
        elif arg == "--nc":
            config['nc'] = args[i+1]
            i += 1
        elif arg in ["--sshport", "--ssh-port"]:
            config['sshport'] = args[i+1]
            i += 1
        elif arg == "--builder":
            config['builder'] = args[i+1]
            i += 1
        elif arg == "--uefi":
            config['useefi'] = True
        elif arg in ["--detach", "-d"]:
            config['detach'] = True
        elif arg in ["--console", "-c"]:
            config['console'] = True
        elif arg == "-v":
            config['vpaths'].append(args[i+1])
            i += 1
        elif arg == "-p":
            config['ports'].append(args[i+1])
            i += 1
        elif arg == "--mon":
            config['qmon'] = args[i+1]
            i += 1
        elif arg == "--vnc":
            config['vnc'] = args[i+1]
            i += 1
        elif arg == "--sync":
            config['sync'] = args[i+1]
            i += 1
        elif arg == "--disktype":
            config['disktype'] = args[i+1]
            i += 1
        elif arg == "--public":
            config['public'] = True
        elif arg == "--whpx":
            config['whpx'] = True
        elif arg == "--serial":
            config['serialport'] = args[i+1]
            i += 1
        i += 1

    if not config['os']:
        print_usage()
        fatal("Missing required argument: --os")

    if config['os'] == "freebsd":
        config['useefi'] = True

    if config['whpx'] and not IS_WINDOWS:
        log("Warning: --whpx is only meaningful on Windows hosts; ignoring.")
        config['whpx'] = False

    # Arch detection
    host_machine = platform.machine()
    # Normalize Windows AMD64 to x86_64
    if host_machine == "AMD64":
        host_machine = "x86_64"
        
    if host_machine in ["arm64", "aarch64"]:
        host_arch = "aarch64"
    else:
        host_arch = host_machine
    
    if not config['arch']:
        log("Use host arch: " + host_arch)
        config['arch'] = host_arch

    # Normalize arch string
    if config['arch'] in ["x86_64", "amd64"]:
        config['arch'] = ""
    if config['arch'] in ["arm", "arm64"]:
        config['arch'] = "aarch64"

    builder_repo = "vmactions/{}-builder".format(config['os'])
    working_dir_os = os.path.join(working_dir, config['os'])
    if not os.path.exists(working_dir_os):
        os.makedirs(working_dir_os)

    if config['arch']:
        log("Using arch: " + config['arch'])
    else:
        log("Using arch: x86_64")

    # Fetch release info
    all_releases_file = os.path.join(working_dir_os, "all.json")
    
    def get_releases():
        if os.path.exists(all_releases_file):
            try:
                with open(all_releases_file, 'r') as f:
                    return json.load(f)
            except ValueError:
                pass
        
        url = "https://api.github.com/repos/{}/releases".format(builder_repo)
        content = fetch_url_content(url)
        if content:
            try:
                data = json.loads(content)
                with open(all_releases_file, 'w') as f:
                    f.write(content)
                return data
            except ValueError:
                return []
        return []

    releases_data = get_releases()
    zst_link = ""
    published_at = ""
    # Find release version if not provided
    if not config['release']:
        for r in releases_data:
            #log(r)
            for asset in r.get('assets', []):
                u = asset.get('browser_download_url', '')
                #log(u)
                if u.endswith("qcow2.zst") or u.endswith("qcow2.xz"):
                    if config['arch'] and config['arch'] not in u:
                        continue
                    # Extract version roughly
                    filename=u.split('/')[-1]
                    filename= removesuffix(filename, ".qcow2.zst")
                    filename= removesuffix(filename, ".qcow2.xz")
                    parts = filename.split('-')
                    if len(parts) > 1:
                        if published_at and published_at > r.get('published_at', ''):
                            continue
                        if not published_at:
                            published_at = r.get('published_at', '')
                            config['release'] = parts[1]
                        elif cmp_version(parts[1], config['release']) > 0:
                          published_at = r.get('published_at', '')
                          config['release'] = parts[1]
                          log("Found release: " + config['release'])


    log("Using release: " + config['release'])
    # Find download link
    if not zst_link:
        target_zst = "{}-{}.qcow2.zst".format(config['os'], config['release'])
        target_xz = "{}-{}.qcow2.xz".format(config['os'], config['release'])
        
        if config['arch']:
             target_zst = "{}-{}-{}.qcow2.zst".format(config['os'], config['release'], config['arch'])
             target_xz = "{}-{}-{}.qcow2.xz".format(config['os'], config['release'], config['arch'])

        for r in releases_data:
            for asset in r.get('assets', []):
                u = asset.get('browser_download_url', '')
                if u.endswith(target_zst) or u.endswith(target_xz):
                    zst_link = u
                    break
            if zst_link:
                break

    if not zst_link:
        fatal("Cannot find the image link.")

    log("Using link: " + zst_link)

    if not config['builder']:
        parts = zst_link.split('/')
        for p in parts:
            if p.startswith('v') and len(p) > 1 and p[1].isdigit():
                config['builder'] = p[1:]
                break
    
    output_dir = os.path.join(working_dir_os, "v" + config['builder'])
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    ova_file = os.path.join(output_dir, zst_link.split('/')[-1])
    qcow_name = ova_file.replace('.zst', '').replace('.xz', '')
    if not qcow_name.endswith('.qcow2'):
        qcow_name += ".qcow2"

    # Download and Extract
    if not os.path.exists(qcow_name):
        if not os.path.exists(ova_file):
            if download_file(zst_link, ova_file):
                download_optional_parts(zst_link, ova_file)
        
        log("Extracting " + ova_file)
        if ova_file.endswith('.zst'):
            if subprocess.call(['zstd', '-d', ova_file, '-o', qcow_name]) != 0:
                fatal("zstd extraction failed")
        elif ova_file.endswith('.xz'):
            with open(qcow_name, 'wb') as f:
                if subprocess.call(['xz', '-d', '-c', ova_file], stdout=f) != 0:
                    fatal("xz extraction failed")
        
        if not os.path.exists(qcow_name):
            fatal("Extraction failed")
        try:
            os.remove(ova_file)
        except OSError:
            pass

    # Key files
    vm_name = "{}-{}".format(config['os'], config['release'])
    if config['arch']:
        vm_name += "-" + config['arch']

    hostid_url = "https://github.com/{}/releases/download/v{}/{}-host.id_rsa".format(builder_repo, config['builder'], vm_name)
    hostid_file = os.path.join(output_dir, hostid_url.split('/')[-1])
    
    if not os.path.exists(hostid_file):
        download_file(hostid_url, hostid_file)
        if not IS_WINDOWS:
            os.chmod(hostid_file, 0o600)

    vmpub_url = "https://github.com/{}/releases/download/v{}/{}-id_rsa.pub".format(builder_repo, config['builder'], vm_name)
    vmpub_file = os.path.join(output_dir, vmpub_url.split('/')[-1])
    if not os.path.exists(vmpub_file):
        download_file(vmpub_url, vmpub_file)

    # Ports
    if not config['sshport']:
        config['sshport'] = get_free_port()
        if not config['sshport']:
            fatal("No free port")

    if config['public']:
        addr = ""
    else:
        addr = "127.0.0.1"

    serial_bind_addr = "0.0.0.0" if config['public'] else "127.0.0.1"
    if config['console']:
        serial_arg = "mon:stdio"
    else:
        if not config['serialport']:
            serial_port = get_free_port(start=7000, end=9000)
            if not serial_port:
                fatal("No free serial ports available")
            config['serialport'] = str(serial_port)
        serial_arg = "tcp:{}:{},server,nowait".format(serial_bind_addr, config['serialport'])
        log("Serial console listening on {}:{} (tcp)".format(serial_bind_addr, config['serialport']))

    # QEMU Construction
    bin_name = "qemu-system-aarch64" if config['arch'] == "aarch64" else "qemu-system-x86_64"
    qemu_bin = find_qemu(bin_name)
    
    if not qemu_bin:
        fatal("QEMU binary '{}' not found. Please install QEMU or check PATH.".format(bin_name))
    
    # Disk type selection
    if config['disktype']:
        disk_if = config['disktype']
    else:
        if config['os'] != "dragonflybsd":
            disk_if = "virtio"
        else:
            disk_if = "ide"

    # Build Netdev Argument
    # Always include standard SSH mapping
    netdev_args = "user,id=net0,net=192.168.122.0/24,dhcpstart=192.168.122.50"
    netdev_args += ",hostfwd=tcp:{}:{}-:22".format(addr, config['sshport'])
    
    # Add custom port mappings
    for p in config['ports']:
        parts = p.split(':')
        # Format: host:guest (tcp default), tcp:host:guest, udp:host:guest
        if len(parts) == 2:
            # host:guest -> tcp:addr:host-:guest
            netdev_args += ",hostfwd=tcp:{}:{}-:{}".format(addr, parts[0], parts[1])
        elif len(parts) == 3:
            # proto:host:guest -> proto:addr:host-:guest
            netdev_args += ",hostfwd={}:{}:{}-:{}".format(parts[0], addr, parts[1], parts[2])

    args_qemu = [
        "-serial", serial_arg,
        "-name", vm_name,
        "-smp", config['cpu'],
        "-m", config['mem'],
        "-netdev", netdev_args,
        "-drive", "file={},format=qcow2,if={}".format(qcow_name, disk_if)
    ]

    # Network card selection
    if config['nc']:
        net_card = config['nc']
    else:
        net_card = "e1000"
        if config['os'] == "openbsd" and config['release']:
            release_base = config['release'].split('-')[0]
            if release_base in OPENBSD_E1000_RELEASES:
                net_card = "e1000"
            else:
                net_card = "virtio-net-pci"

    # Platform specific args
    if config['arch'] == "aarch64":
        efi_path = os.path.join(output_dir, vm_name + "-QEMU_EFI.fd")
        vars_path = os.path.join(output_dir, vm_name + "-QEMU_EFI_VARS.fd")
        
        if not os.path.exists(efi_path):
            create_sized_file(efi_path, 64)
            candidates = ["/usr/share/qemu-efi-aarch64/QEMU_EFI.fd", "/opt/homebrew/share/qemu/edk2-aarch64-code.fd"]
            for c in candidates:
                if os.path.exists(c):
                    copy_content_to_file(c, efi_path)
                    break
        
        if not os.path.exists(vars_path):
            create_sized_file(vars_path, 64)

        accel = "tcg"
        if host_arch == "aarch64":
            if os.path.exists("/dev/kvm"):
                accel = "kvm"
            elif platform.system() == "Darwin":
                accel = "hvf"
        
        if config['cputype']:
            cpu = config['cputype']
        else:
            cpu = "cortex-a72"
            
        if accel == "kvm":
            cpu = "host"
        
        args_qemu.extend([
            "-machine", "virt,accel={},gic-version=3".format(accel),
            "-cpu", cpu,
            "-device", "{},netdev=net0".format(net_card),
            "-drive", "if=pflash,format=raw,readonly=on,file={}".format(efi_path),
            "-drive", "if=pflash,format=raw,file={},unit=1".format(vars_path)
        ])
    else:
        # x86_64
        accel = "tcg"
        if host_arch in ["x86_64", "amd64"]:
             if IS_WINDOWS:
                 if config['whpx']:
                     accel = "whpx:tcg"
             elif os.path.exists("/dev/kvm"):
                 accel = "kvm"
             elif platform.system() == "Darwin":
                 accel = "hvf"
        
        machine_opts = "pc,accel={},hpet=off,smm=off,graphics=off,vmport=off".format(accel)
        
        if accel == "kvm":
            cpu_opts = "host,kvm=on,l3-cache=on,+hypervisor,migratable=no,+invtsc"
        else:
            cpu_opts = "qemu64"
            
        args_qemu.extend([
            "-machine", machine_opts,
            "-cpu", cpu_opts,
            "-device", "{},netdev=net0,bus=pci.0,addr=0x3".format(net_card),
            "-device", "virtio-balloon-pci,bus=pci.0,addr=0x6"
        ])
        
        # x86 UEFI handling
        if config['useefi']:
            efi_src = "/usr/share/qemu/OVMF.fd"
            if IS_WINDOWS:
                prog_files = os.environ.get("ProgramFiles", r"C:\Program Files")
                efi_src = os.path.join(prog_files, "qemu", "share", "edk2-x86_64-code.fd")
            vars_path = os.path.join(output_dir, vm_name + "-OVMF_VARS.fd")
            if not os.path.exists(vars_path):
                create_sized_file(vars_path, 4)
            
            args_qemu.extend([
                "-drive", "if=pflash,format=raw,readonly=on,file={}".format(efi_src),
                "-drive", "if=pflash,format=raw,file={}".format(vars_path)
            ])

    # VNC and Monitor
    if config['vnc'] != "off":
        try:
            start_disp = int(config['vnc']) if config['vnc'] else 0
        except ValueError:
            start_disp = 0
        vnc_bind_addr = addr if addr else "0.0.0.0"
        disp = get_free_vnc_display(vnc_bind_addr, start=start_disp)
        if disp is None:
            fatal("No available VNC display ports")
        args_qemu.append("-display")
        args_qemu.append("vnc={}:{}".format(addr, disp))
    
    if config['qmon']:
        args_qemu.extend(["-monitor", "telnet:localhost:{},server,nowait,nodelay".format(config['qmon'])])

    # Execution
    cmd_list = [qemu_bin] + args_qemu
    cmd_text = format_command_for_display(cmd_list)
    log("CMD:\n  " + cmd_text)

    if config['console']:
        subprocess.call(cmd_list)
    else:
        # Background run
        try:
            proc = subprocess.Popen(cmd_list, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError as e:
            fatal("Failed to start QEMU: {}".format(e))

        def fail_with_output(reason):
            stdout_data = proc.stdout.read() or b""
            stderr_data = proc.stderr.read() or b""
            err_msg = stderr_data.decode('utf-8', errors='replace').strip()
            out_msg = stdout_data.decode('utf-8', errors='replace').strip()
            combined = err_msg or out_msg or "(no output)"
            fatal("{} (code {}). Output:\n{}".format(reason, proc.returncode, combined))

        time.sleep(1)
        if proc.poll() is not None:
            fail_with_output("QEMU exited immediately")


        log("Started QEMU (PID: {})".format(proc.pid))

        
        # Config SSH
        ssh_dir = os.path.join(os.path.expanduser("~"), ".ssh")
        if not os.path.exists(ssh_dir):
            os.makedirs(ssh_dir)
            if not IS_WINDOWS:
                os.chmod(ssh_dir, 0o700)
        
        with open(vmpub_file, 'r') as f:
            pub = f.read()
        with open(os.path.join(ssh_dir, "authorized_keys"), 'a') as f:
            f.write(pub)

        conf_path = os.path.join(ssh_dir, "config.d")
        if not os.path.exists(conf_path):
            os.makedirs(conf_path)
        
        ssh_config_content = "\nHost {}\n  StrictHostKeyChecking no\n  UserKnownHostsFile={}\n  User root\n  HostName localhost\n  Port {}\n  IdentityFile {}\n".format(vm_name, SSH_KNOWN_HOSTS_NULL, config['sshport'], hostid_file)
        
        os.unlink(os.path.join(conf_path, "{}.conf".format(vm_name))) if os.path.exists(os.path.join(conf_path, "{}.conf".format(vm_name))) else None
        
        # Write config for VM name
        with open(os.path.join(conf_path, "{}.conf".format(vm_name)), 'w') as f:
            f.write(ssh_config_content)

        if not IS_WINDOWS:
            os.chmod(os.path.join(conf_path, "{}.conf".format(vm_name)), 0o600)

        # Write config for Port
        port_conf_content = ssh_config_content.replace("Host " + vm_name, "Host " + str(config['sshport']))
        
        os.unlink(os.path.join(conf_path, "{}.conf".format(config['sshport']))) if os.path.exists(os.path.join(conf_path, "{}.conf".format(config['sshport']))) else None
        
        with open(os.path.join(conf_path, "{}.conf".format(config['sshport'])), 'w') as f: 
             f.write(port_conf_content)
        
        if not IS_WINDOWS:
            os.chmod(os.path.join(conf_path, "{}.conf".format(config['sshport'])), 0o600)

        main_conf = os.path.join(ssh_dir, "config")
        if not os.path.exists(main_conf):
            open(main_conf, 'w').close()
            if not IS_WINDOWS:
              os.chmod(main_conf, 0o600)
        
        with open(main_conf, 'r') as f:
            content = f.read()
            if "Include config.d" not in content:
                with open(main_conf, 'a') as fa:
                    fa.write("\nInclude config.d/*.conf\n")

        # Wait for boot
        log("Waiting for VM to boot (port {})...".format(config['sshport']))
        success = False
        
        ssh_base_cmd = [
            "ssh",
            "-o", "ConnectTimeout=5",
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile={}".format(SSH_KNOWN_HOSTS_NULL),
            "-o", "LogLevel=ERROR",
            "-i", hostid_file,
            "-p", str(config['sshport']),
            "root@localhost"
        ]
        
        for i in range(300):
            if proc.poll() is not None:
                fail_with_output("QEMU terminated during boot")
            ret = subprocess.call(
                ssh_base_cmd + ["exit"],
                stdout=DEVNULL,
                stderr=DEVNULL
            )
            if ret == 0:
                success = True
                break
            time.sleep(2)
        
        if not success:
            fatal("Boot timed out.")
        
        log("VM Ready! Connect with: ssh {}".format(vm_name))

        # Post-boot config: Setup reverse SSH config inside VM
        current_user = getpass.getuser()
        vm_ssh_config = """
StrictHostKeyChecking=no

Host host
  HostName  192.168.122.2
  User {}
  ServerAliveInterval 1
""".format(current_user)
        
        p = subprocess.Popen(ssh_base_cmd + ["cat - > .ssh/config"], stdin=subprocess.PIPE)
        p.communicate(input=vm_ssh_config.encode('utf-8'))
        p.wait()

        # Mount Shared Folders
        if config['vpaths']:
            sudo_cmd = []
            if config['sync'] == 'nfs':
                # Check if sudo exists in path (unix only)
                if not IS_WINDOWS:
                    try:
                        with open(os.devnull, 'w') as devnull:
                            if subprocess.call("command -v sudo", shell=True, stdout=devnull, stderr=devnull) == 0:
                                 sudo_cmd = ["sudo"]
                    except:
                        pass

            for vpath_str in config['vpaths']:
                try:
                    vhost, vguest = vpath_str.split(':')
                    log("Mounting host dir: {} to guest: {}".format(vhost, vguest))
                    
                    if config['sync'] == 'nfs':
                        sync_nfs(ssh_base_cmd, vhost, vguest, config['os'], sudo_cmd)
                    elif config['sync'] == 'rsync':
                        sync_rsync(ssh_base_cmd, vhost, vguest, config['os'])
                    elif config['sync'] == 'scp':
                        sync_scp(ssh_base_cmd, vhost, vguest, config['sshport'], hostid_file)
                    else:
                        sync_sshfs(ssh_base_cmd, vhost, vguest, config['os'])

                except ValueError:
                    log("Invalid format for -v. Use host_path:guest_path")

        if config['console']:
             log("======================================")
             log("")
             log("You can login the vm with: ssh " + vm_name)
             log("Or just:  ssh " + str(config['sshport']))
             log("======================================")
        
        if not config['detach']:
            subprocess.call(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile={}".format(SSH_KNOWN_HOSTS_NULL), "-i", hostid_file, "-p", str(config['sshport']), "root@localhost"])
        else:
            log("======================================")
            log("The vm is still running.")
            log("You can login the vm with:  ssh " + vm_name)
            log("Or just:  ssh " + str(config['sshport']))
            log("======================================")

if __name__ == '__main__':
    main()