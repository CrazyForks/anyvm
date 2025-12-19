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
import random

# Python 2/3 compatibility for urllib and input
try:
    # Python 3
    from urllib.request import urlopen, Request, urlretrieve
    from urllib.error import HTTPError, URLError
    from urllib.parse import urljoin
    input_func = input
except ImportError:
    # Python 2
    from urllib2 import urlopen, Request, HTTPError, URLError
    from urlparse import urljoin
    
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


DEFAULT_BUILDER_VERSIONS = {
    "freebsd": "2.0.3",
    "openbsd": "2.0.0",
    "netbsd": "2.0.0",
    "dragonflybsd": "2.0.3",
    "solaris": "2.0.0",
    "omnios": "2.0.0",
    "openindiana": "2.0.0"
}

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

def debuglog(enabled, msg):
    """Conditional debug logger."""
    if enabled:
        print("[DEBUG] {}".format(msg))

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
  --cpu <num>            Number of CPU cores (Default: all host cores).
  --cpu-type <type>      Specific CPU model (e.g., cortex-a72, host).
  --nc <type>            Network card model (e.g., virtio-net-pci, e1000).
  --ssh-port <port>      Host port forwarding for SSH (Default: auto-detected free port).
  --ssh-name <name>      Add an extra SSH alias for the VM (e.g., ssh vmname).
                                                 When set, it will be added to the port-based alias entry.
  --host-ssh-port <port> Host SSH port reachable from the guest (Default: 22).
  --serial <port>        Expose the VM serial console on the given TCP port (auto-select starting 7000 if omitted).
  -p <mapping>           Custom port mapping. Can be used multiple times.
                         Formats: host:guest, tcp:host:guest, udp:host:guest.
                         Example: -p 8080:80 -p udp:3000:3000
  -v <mapping>           Folder synchronization. Can be used multiple times.
                         Format: /host/path:/guest/path
                         Example: -v /home/user/data:/mnt/data
  --sync <mode>          Synchronization mode for -v folders.
                         Supported: sshfs (default), nfs, rsync, scp.
                         Note: sshfs/nfs not supported on Windows hosts; rsync requires rsync.exe.
  --data-dir <dir>       Directory to store images and metadata (Default: ./output).
  --disktype <type>      Disk interface type (e.g., virtio, ide).
                         Default: virtio (ide for dragonflybsd).
  --uefi                 Enable UEFI boot (Implicit for FreeBSD).
  --vnc <display>        Enable VNC on specified display (e.g., 0 for :0).
  --mon <port>           QEMU monitor telnet port (localhost).
  --public               Listen on 0.0.0.0 for mapped ports instead of 127.0.0.1.
  --whpx                 (Windows) Attempt to use WHPX acceleration instead of TCG.
  --debug                Enable verbose debug logging.
  --detach, -d           Run QEMU in background.
  --console, -c          Run QEMU in foreground (console mode).
  --builder <ver>        Specify a specific vmactions builder version tag.
  --                     Send all following args to the final ssh command (executes inside the VM).
  --help, -h             Show this help message.

Examples:
  # Basic FreeBSD VM
  python qemu.py --os freebsd --release 14.0

  # ARM64 VM on x86_64 host with port mapping and folder sync
  python qemu.py --os openbsd --arch aarch64 -p 8080:80 -v $(pwd):/data

  # Windows host using SCP sync
  python qemu.py --os solaris --sync scp -v D:\\data:/data

  # Run a command inside the VM (arguments after -- go to ssh)
  python qemu.py --os freebsd -- uname -a

""")

def get_free_port(start=10022, end=20000):
    """Return an available TCP port that works for both 0.0.0.0 and 127.0.0.1 binds."""
    probe_addrs = ("0.0.0.0", "127.0.0.1")
    for port in range(start, end):
        for addr in probe_addrs:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            try:
                s.bind((addr, port))
            except Exception:
                break
            finally:
                try:
                    s.close()
                except Exception:
                    pass
        else:
            return port
    return None


def fetch_url_content(url, debug=False, headers=None):
    attempts = 20
    max_redirects = 5
    chrome_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    headers = headers or {}
    for attempt in range(attempts):
        current_url = url
        debuglog(debug, "fetch attempt {} for {}".format(attempt + 1, current_url))
        for _ in range(max_redirects):
            user_agents = [chrome_ua]
            for ua in user_agents:
                req = Request(current_url)
                req.add_header('User-Agent', ua)
                for hk, hv in headers.items():
                    req.add_header(hk, hv)
                try:
                    resp = urlopen(req)
                    try:
                        data = resp.read()
                    finally:
                        try:
                            resp.close()
                        except Exception:
                            pass
                    if data:
                        debuglog(debug, "fetched {} bytes from {} with UA {}".format(len(data), current_url, ua))
                        return data.decode('utf-8')
                    debuglog(debug, "empty response from {} with UA {}; retrying".format(current_url, ua))
                    break  # empty body, retry outer loop
                except HTTPError as e:
                    if e.code in (301, 302, 303, 307, 308):
                        loc = e.headers.get('Location')
                        if loc:
                            debuglog(debug, "redirect {} -> {} (UA {})".format(current_url, loc, ua))
                            current_url = urljoin(current_url, loc)
                            break  # follow redirect with default UA list
                    if e.code == 404:
                        log("404: " + current_url)
                        return None
                    debuglog(debug, "HTTPError {} on {} with UA {}".format(e.code, current_url, ua))
                    continue  # try next UA
                except Exception as exc:
                    debuglog(debug, "Exception on {} with UA {}: {}".format(current_url, ua, exc))
                    continue  # try next UA
            else:
                # exhausted user agents
                break
            # if we hit a redirect, restart UA loop with new URL
            continue
        if attempt < attempts - 1:
            delay = random.uniform(1, 20)
            debuglog(debug, "retrying in {:.1f}s".format(delay))
            time.sleep(delay)
    debuglog(debug, "fetch failed for {}".format(url))
    return None

def get_remote_file_info(url, debug=False):
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
        debuglog(debug, "HEAD {} -> length {}, accept_ranges {}".format(url, length, accept_ranges))
        try:
            resp.close()
        except Exception:
            pass
        return length, accept_ranges
    except Exception as exc:
        debuglog(debug, "HEAD failed for {}: {}".format(url, exc))
        return 0, False

def check_url_exists(url, debug=False):
    try:
        req = Request(url)
        req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        u = urlopen(req, timeout=10)
        u.close()
        return True
    except Exception as e:
        debuglog(debug, "Check URL failed: {} - {}".format(url, str(e)))
        return False

def download_file_multithread(url, dest, total_size, show_progress, debug=False):
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
    debuglog(debug, "multithread download: {} bytes, threads {}, chunk {}".format(total_size, num_threads, chunk_size))

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
            debuglog(debug, "worker range {}-{} failed: {}".format(start, end, e))

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
        debuglog(debug, "started worker {} range {}-{}".format(index, start, end))

    for t in threads:
        t.join()
    debuglog(debug, "all workers finished")

    if show_progress:
        sys.stdout.write("\n")
        sys.stdout.flush()

    if errors or stop_event.is_set():
        try:
            os.remove(tmp_dest)
        except OSError:
            pass
        debuglog(debug, "multithread download failed; errors: {}".format(errors))
        return False

    try:
        if hasattr(os, 'replace'):
            os.replace(tmp_dest, dest)
        else:
            shutil.move(tmp_dest, dest)
    except Exception:
        return False
    debuglog(debug, "multithread download succeeded: {}".format(dest))
    return True

def download_file(url, dest, debug=False):
    log("Downloading " + url)
    show_progress = sys.stdout.isatty()

    size, can_range = get_remote_file_info(url, debug)
    if can_range and size > 0:
        debuglog(debug, "server supports range; size {}".format(size))
        if download_file_multithread(url, dest, size, show_progress, debug):
            return True
        log("Falling back to single-thread download...")
    else:
        debuglog(debug, "range not supported or size unknown (size {}, can_range {})".format(size, can_range))

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
        except Exception as exc:
            debuglog(debug, "single-thread attempt {} failed: {}".format(i + 1, exc))
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


def download_optional_parts(base_url, base_path, max_parts=9, debug=False):
    for idx in range(1, max_parts + 1):
        part_url = "{}.{}".format(base_url, idx)
        if not url_exists(part_url):
            break
        log("Appending extra part: " + part_url)
        if not append_url_to_file(part_url, base_path, debug):
            log("Warning: Failed to append optional part {}".format(part_url))
            break


def append_url_to_file(url, dest_path, debug=False):
    req = Request(url)
    req.add_header('User-Agent', 'python-qemu-script')
    try:
        resp = urlopen(req)
    except Exception as exc:
        debuglog(debug, "failed to open {}: {}".format(url, exc))
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
            except Exception as exc:
                debuglog(debug, "failed while appending {}: {}".format(url, exc))
                f_main.truncate(start_pos)
                return False
    finally:
        try:
            resp.close()
        except Exception:
            pass
    debuglog(debug, "appended {}".format(url))
    return True

def terminate_process(proc, name="process", grace_seconds=10):
    """Attempts to gracefully stop a subprocess before forcing termination."""
    if not proc or proc.poll() is not None:
        return
    log("Terminating qemu")
    log("Stopping {} (PID: {})".format(name, proc.pid))
    try:
        proc.terminate()
    except Exception:
        pass

    deadline = time.time() + max(0, grace_seconds)
    while proc.poll() is None and time.time() < deadline:
        time.sleep(0.2)

    if proc.poll() is None:
        log("{} did not exit gracefully; killing.".format(name))
        try:
            proc.kill()
        except Exception:
            pass

def tighten_windows_permissions(path):
    """Removes inherited ACLs on Windows to mimic chmod 600 semantics."""
    if not IS_WINDOWS:
        return
    try:
        subprocess.check_call(["icacls", path, "/inheritance:r"], stdout=DEVNULL, stderr=DEVNULL)
        user = os.environ.get("USERNAME")
        if not user:
            return
        domain = os.environ.get("USERDOMAIN")
        principal = "{}\\{}".format(domain, user) if domain else user
        subprocess.check_call(["icacls", path, "/grant:r", "{}:F".format(principal)], stdout=DEVNULL, stderr=DEVNULL)
    except Exception as exc:
        log("Warning: Failed to adjust ACLs for {}: {}".format(path, exc))

def call_with_timeout(cmd, timeout_seconds, **popen_kwargs):
    """Runs a subprocess with a hard timeout, returning (returncode, timed_out)."""
    proc = subprocess.Popen(cmd, **popen_kwargs)
    deadline = time.time() + max(0, timeout_seconds)
    while True:
        ret = proc.poll()
        if ret is not None:
            return ret, False
        if time.time() >= deadline:
            break
        time.sleep(0.1)

    try:
        proc.terminate()
    except Exception:
        pass
    try:
        proc.wait(1)
    except Exception:
        pass
    return None, True

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

        # Handle MSYS2 UCRT64 location
        msys_path = r"C:\msys64\ucrt64\bin"
        candidate_msys = os.path.join(msys_path, binary_name + ".exe")
        if os.path.exists(candidate_msys):
            return candidate_msys
            
    return None

def find_rsync():
    """Find rsync on host; returns absolute path or None."""
    path = None
    if hasattr(shutil, 'which'):
        path = shutil.which("rsync")
    if path:
        return path
    candidates = [
        r"C:\Program Files\Git\usr\bin\rsync.exe",
        r"C:\Program Files (x86)\Git\usr\bin\rsync.exe",
        r"C:\msys64\usr\bin\rsync.exe",
        r"C:\cygwin64\bin\rsync.exe",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None

def hvf_supported():
    """Returns True if macOS Hypervisor.framework (HVF) is available."""
    if platform.system() != "Darwin":
        return False
    try:
        out = subprocess.check_output(["sysctl", "-n", "kern.hv_support"], stderr=DEVNULL)
        return out.strip() == b"1"
    except Exception:
        return False

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
    kldload fusefs >/dev/null 2>&1 || true
  fi
  if sshfs -o reconnect,ServerAliveCountMax=2,allow_other,default_permissions host:"{vhost}" "{vguest}" ; then
    /sbin/mount >/dev/null 2>&1 || mount >/dev/null 2>&1
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
                content = f.read()
                # Check if the exact path is already exported
                # Simple string check might be flaky, but good enough for now
                if vhost + " " in content:
                    need_add = False
    except:
        pass

    if need_add:
        log("Configuring NFS export on host (requires sudo)...")
        debuglog(True, "Adding export: " + entry_line)
        if sudo_cmd or os.geteuid() == 0:
            subprocess.call(sudo_cmd + ["mkdir", "-p", "/run/sendsigs.omit.d/"])
            cmd_write = sudo_cmd + ["tee", "-a", "/etc/exports"]
            p_write = subprocess.Popen(cmd_write, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            p_write.communicate(input=(entry_line + "\n").encode('utf-8'))
            
            if p_write.returncode == 0:
                subprocess.call(sudo_cmd + ["exportfs", "-a"])
                if subprocess.call(sudo_cmd + ["service", "nfs-kernel-server", "restart"]) != 0:
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
    host_rsync = find_rsync()
    if IS_WINDOWS and not host_rsync:
        log("Warning: rsync not found on host. Install rsync to use rsync sync mode.")
        return

    log("Syncing via rsync: {} -> {}".format(vhost, vguest))
    rsync_path_arg = '--rsync-path="{}"'.format(host_rsync.replace("\\", "/"))
    
    mount_script = """
mkdir -p "{vguest}"
if command -v rsync >/dev/null 2>&1; then
  rsync -avrtopg --delete {rsync_path} host:"{vhost}/" "{vguest}/"
else
  echo "Error: rsync not found in guest."
  exit 1
fi
""".format(vguest=vguest, vhost=vhost, rsync_path=rsync_path_arg)

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

    if not os.path.exists(vhost):
        log("Warning: Host path {} does not exist; skipping.".format(vhost))
        return

    if os.path.isdir(vhost):
        try:
            entries = os.listdir(vhost)
        except OSError as exc:
            log("Warning: Failed to read {}: {}".format(vhost, exc))
            return
        if not entries:
            log("Host dir {} is empty; nothing to sync.".format(vhost))
            return
        sources = [os.path.join(vhost, entry) for entry in entries]
    else:
        sources = [vhost]

    # SCP command to push files
    # Added -O option for legacy protocol support
    cmd = [
        "scp", "-r", "-q", "-O",
        "-P", str(sshport),
    ]
    if hostid_file:
        cmd.extend(["-i", hostid_file])
        
    cmd.extend([
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile={}".format(SSH_KNOWN_HOSTS_NULL),
        "-o", "LogLevel=ERROR",
    ] + sources + ["root@localhost:" + vguest + "/"])
    
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

def tail_serial_log(path, stop_event):
    # Wait for file creation
    start_wait = time.time()
    while not os.path.exists(path):
        if stop_event.is_set() or (time.time() - start_wait > 10):
            return
        time.sleep(0.1)
        
    try:
        with open(path, 'r') as f:
            while not stop_event.is_set():
                data = f.read()
                if data:
                    sys.stdout.write(data)
                    sys.stdout.flush()
                else:
                    time.sleep(0.1)
    except Exception:
        pass


def main():
    # Default configuration
    default_cpu = str(max(1, os.cpu_count() or 1))
    config = {
        'mem': "2048",
        'cpu': default_cpu,
        'cputype': "",
        'nc': "",
        'sshport': "",
        'sshname': "",
        'hostsshport': "",
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
        'serialport': "",
        'debug': False,
        'qcow2': ""
    }

    ssh_passthrough = []

    script_home = os.path.dirname(os.path.abspath(__file__))
    working_dir = os.path.join(script_home, "output")
    
    if os.environ.get("GOOGLE_CLOUD_SHELL") == "true":
        working_dir = "/tmp/anyvm.org"
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
        if arg == "--":
            ssh_passthrough = args[i+1:]
            break
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
        elif arg in ["--data-dir", "--workingdir"]:
            working_dir = os.path.abspath(args[i+1])
            i += 1
        elif arg == "--nc":
            config['nc'] = args[i+1]
            i += 1
        elif arg in ["--sshport", "--ssh-port"]:
            config['sshport'] = args[i+1]
            i += 1
        elif arg == "--ssh-name":
            config['sshname'] = args[i+1]
            i += 1
        elif arg == "--host-ssh-port":
            config['hostsshport'] = args[i+1]
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
        elif arg == "--debug":
            config['debug'] = True
        elif arg == "--public":
            config['public'] = True
        elif arg == "--whpx":
            config['whpx'] = True
        elif arg == "--serial":
            config['serialport'] = args[i+1]
            i += 1
        elif arg == "--qcow2":
            config['qcow2'] = args[i+1]
            i += 1
        i += 1

    if config['debug']:
        debuglog(True, "Debug logging enabled")

    if not config['os']:
        print_usage()
        fatal("Missing required argument: --os")

    if config.get('sshname'):
        # Keep this conservative: Host patterns are space-delimited in ssh config.
        # Disallow whitespace and other separators to avoid generating invalid config.
        if not re.match(r'^[A-Za-z0-9._-]+$', config['sshname']):
            fatal("Invalid --ssh-name value: {} (allowed: A-Z a-z 0-9 . _ -)".format(config['sshname']))

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
        
    if host_machine in ["arm64", "aarch64", "ARM64"]:
        host_arch = "aarch64"
    else:
        host_arch = host_machine
    
    if not config['arch']:
        debuglog(config['debug'], "Host arch: " + host_arch)
        config['arch'] = host_arch

    # Normalize arch string
    if config['arch'] in ["x86_64", "amd64"]:
        config['arch'] = ""
    if config['arch'] in ["arm", "arm64", "ARM64"]:
        config['arch'] = "aarch64"

    arepo = "vmactions/{}-builder".format(config['os'])
    brepo = "anyvm-org/{}-builder".format(config['os'])
    if config['builder']:
        builder_repo = brepo if cmp_version(config['builder'], "2.0.0") >= 0 else arepo
        release_repo_candidates = [builder_repo]
    elif config['release']:
        builder_repo = brepo
        release_repo_candidates = [brepo, arepo]
    else:
        builder_repo = brepo
        release_repo_candidates = [brepo]
    working_dir_os = os.path.join(working_dir, config['os'])
    if not os.path.exists(working_dir_os):
        os.makedirs(working_dir_os)

    # Fetch release info
    releases_cache = {}
    
    def get_releases(repo_slug):
        cache_name = "{}-releases.json".format(repo_slug.replace("/", "_"))
        cache_path = os.path.join(working_dir_os, cache_name)
        if repo_slug in releases_cache:
            return releases_cache[repo_slug]
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    releases_cache[repo_slug] = json.load(f)
                    return releases_cache[repo_slug]
            except ValueError:
                pass
        
        gh_headers = {
            "Accept": "application/vnd.github+json",
        }
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if token:
            gh_headers["Authorization"] = "Bearer {}".format(token)
            debuglog(config['debug'], "Using GitHub token auth for releases")

        url = "https://api.github.com/repos/{}/releases".format(repo_slug)
        content = fetch_url_content(url, config['debug'], headers=gh_headers)
        if content:
            try:
                data = json.loads(content)
                with open(cache_path, 'w') as f:
                    f.write(content)
                releases_cache[repo_slug] = data
                return data
            except ValueError:
                return []
        return []

    zst_link = ""

    if not config['builder'] and not config['qcow2'] and config['os'] in DEFAULT_BUILDER_VERSIONS:
        def_ver = DEFAULT_BUILDER_VERSIONS[config['os']]
        def_repo = brepo if cmp_version(def_ver, "2.0.0") >= 0 else arepo
        debuglog(config['debug'], "Checking default builder {} in {}".format(def_ver, def_repo))
        
        use_default = False
        found_zst_link = ""
        
        if config['release']:
            # Try to construct the URL directly
            target_zst = "{}-{}.qcow2.zst".format(config['os'], config['release'])
            if config['arch'] and config['arch'] != 'x86_64':
                target_zst = "{}-{}-{}.qcow2.zst".format(config['os'], config['release'], config['arch'])
            
            # URL format: https://github.com/{repo}/releases/download/v{ver}/{filename}
            tag = "v" + def_ver if not def_ver.startswith("v") else def_ver
            
            candidate_url = "https://github.com/{}/releases/download/{}/{}".format(def_repo, tag, target_zst)
            debuglog(config['debug'], "Checking candidate URL: {}".format(candidate_url))
            
            if check_url_exists(candidate_url, config['debug']):
                debuglog(config['debug'], "Candidate URL exists!")
                use_default = True
                found_zst_link = candidate_url
            else:
                debuglog(config['debug'], "Candidate URL not found, falling back to full search")
        else:
            use_default = True
            
        if use_default:
            config['builder'] = def_ver
            builder_repo = def_repo
            release_repo_candidates = [builder_repo]
            debuglog(config['debug'], "Using default builder: {} from {}".format(def_ver, def_repo))
            if found_zst_link:
                zst_link = found_zst_link

    if config['arch']:
        debuglog(config['debug'],"Using VM arch: " + config['arch'])
    else:
        debuglog(config['debug'],"Using VM arch: x86_64")

    if config['qcow2']:
        if not os.path.exists(config['qcow2']):
            fatal("Specified qcow2 file not found: " + config['qcow2'])
        qcow_name = os.path.abspath(config['qcow2'])
        output_dir = working_dir_os
        vm_name = "{}-custom".format(config['os'])
        hostid_file = None
        vmpub_file = None
        log("Using local qcow2: " + qcow_name)
    else:
        if not zst_link:
            releases_data = get_releases(builder_repo)
    
            if not releases_data and (config['builder'] or not config['release']):
                 fatal("Unsupported OS: {}. Builder repository {} not found.".format(config['os'], builder_repo))
    
            if config['builder']:
                target_tag = config['builder']
                if not target_tag.startswith('v'):
                    target_tag = "v" + target_tag
                releases_data = [r for r in releases_data if r.get('tag_name') == target_tag]
        else:
            releases_data = []

        published_at = ""
        # Find release version if not provided
        if not config['release']:
            for r in releases_data:
                #log(r)
                for asset in r.get('assets', []):
                    u = asset.get('browser_download_url', '')
                    #log(u)
                    if u.endswith("qcow2.zst") or u.endswith("qcow2.xz"):
                        if config['arch'] and config['arch'] != "x86_64" and config['arch'] not in u:
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
                              debuglog(config['debug'],"Found release: " + config['release'])


        log("Using release: " + config['release'])
        # Find download link
        def find_image_link(releases, target_zst, target_xz):
            for r in releases:
                for asset in r.get('assets', []):
                    u = asset.get('browser_download_url', '')
                    if u.endswith(target_zst) or u.endswith(target_xz):
                        return u
            return ""

        target_zst = "{}-{}.qcow2.zst".format(config['os'], config['release'])
        target_xz = "{}-{}.qcow2.xz".format(config['os'], config['release'])
        
        if config['arch'] and config['arch'] != 'x86_64':
            target_zst = "{}-{}-{}.qcow2.zst".format(config['os'], config['release'], config['arch'])
            target_xz = "{}-{}-{}.qcow2.xz".format(config['os'], config['release'], config['arch'])

        if not zst_link:
            search_repos = release_repo_candidates if config['release'] else [builder_repo]
            searched = set()
            for repo in search_repos:
                if repo in searched:
                    continue
                searched.add(repo)
                repo_releases = releases_data if repo == builder_repo else get_releases(repo)
                link = find_image_link(repo_releases, target_zst, target_xz)
                if link:
                    builder_repo = repo
                    releases_data = repo_releases
                    zst_link = link
                    break

        if not zst_link:
            fatal("Cannot find the image link.")

        debuglog(config['debug'],"Using link: " + zst_link)

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
                if download_file(zst_link, ova_file, config['debug']):
                    download_optional_parts(zst_link, ova_file, debug=config['debug'])
            
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
        if config['arch'] and config['arch'] != "x86_64":
            vm_name += "-" + config['arch']

        hostid_url = "https://github.com/{}/releases/download/v{}/{}-host.id_rsa".format(builder_repo, config['builder'], vm_name)
        hostid_file = os.path.join(output_dir, hostid_url.split('/')[-1])
        
        if not os.path.exists(hostid_file):
            download_file(hostid_url, hostid_file, config['debug'])
        if IS_WINDOWS:
            tighten_windows_permissions(hostid_file)
        else:
            os.chmod(hostid_file, 0o600)

        vmpub_url = "https://github.com/{}/releases/download/v{}/{}-id_rsa.pub".format(builder_repo, config['builder'], vm_name)
        vmpub_file = os.path.join(output_dir, vmpub_url.split('/')[-1])
        if not os.path.exists(vmpub_file):
            download_file(vmpub_url, vmpub_file, config['debug'])

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
    serial_chardev_def = None
    serial_log_file = None

    if config['console']:
        serial_arg = "mon:stdio"
    else:
        if not config['serialport']:
            serial_port = get_free_port(start=7000, end=9000)
            if not serial_port:
                fatal("No free serial ports available")
            config['serialport'] = str(serial_port)
        
        if config['debug']:
             serial_log_file = os.path.join(output_dir, "{}.serial.log".format(vm_name))
             if os.path.exists(serial_log_file):
                 try:
                     os.remove(serial_log_file)
                 except:
                     pass
             
             serial_chardev_id = "serial0"
             serial_chardev_def = "socket,id={},host={},port={},server=on,wait=off,logfile={}".format(
                 serial_chardev_id, serial_bind_addr, config['serialport'], serial_log_file)
             serial_arg = "chardev:{}".format(serial_chardev_id)
        else:
             serial_arg = "tcp:{}:{},server,nowait".format(serial_bind_addr, config['serialport'])

        debuglog(config['debug'],"Serial console listening on {}:{} (tcp)".format(serial_bind_addr, config['serialport']))

    # QEMU Construction
    bin_name = "qemu-system-x86_64"
    if config['arch'] == "riscv64":
        bin_name = "qemu-system-riscv64"
    elif config['arch'] == "aarch64":
        bin_name = "qemu-system-aarch64"
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

    args_qemu = []
    if serial_chardev_def:
        args_qemu.extend(["-chardev", serial_chardev_def])

    args_qemu.extend([
        "-serial", serial_arg,
        "-name", vm_name,
        "-smp", config['cpu'],
        "-m", config['mem'],
        "-netdev", netdev_args,
        "-drive", "file={},format=qcow2,if={}".format(qcow_name, disk_if)
    ])

    # Windows on ARM has DirectSound issues; disable audio only there.
    if IS_WINDOWS and host_arch == "aarch64":
        args_qemu.extend(["-audiodev", "none,id=snd"])

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
        elif config['os'] == "dragonflybsd":
            if config['release'] != "6.4.0":
                net_card = "virtio-net-pci"
        elif config['arch'] == "riscv64":
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
                if os.access("/dev/kvm", os.R_OK | os.W_OK):
                    accel = "kvm"
                else:
                    log("Warning: /dev/kvm exists but is not writable. Falling back to TCG.")
            elif platform.system() == "Darwin" and hvf_supported():
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
    elif config['arch'] == "riscv64":
        machine_opts = "virt,accel=tcg,graphics=off,usb=off,dump-guest-core=off,acpi=off"
        cpu_opts = "rv64"
        
        args_qemu.extend([
            "-machine", machine_opts,
            "-cpu", cpu_opts,
            "-device", "{},netdev=net0".format(net_card),
            "-kernel", "/usr/lib/u-boot/qemu-riscv64_smode/u-boot.bin",
            "-device", "virtio-balloon-pci"
        ])
    else:
        # x86_64
        accel = "tcg"
        if host_arch in ["x86_64", "amd64"]:
             if IS_WINDOWS:
                 if config['whpx']:
                     accel = "whpx"
             elif os.path.exists("/dev/kvm"):
                 if os.access("/dev/kvm", os.R_OK | os.W_OK):
                     accel = "kvm"
                 else:
                     log("Warning: /dev/kvm exists but is not writable. Falling back to TCG.")
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
            if IS_WINDOWS:
                prog_files = os.environ.get("ProgramFiles", r"C:\Program Files")
                efi_src = os.path.join(prog_files, "qemu", "share", "edk2-x86_64-code.fd")
                if not os.path.exists(efi_src):
                    msys_efi = r"C:\msys64\ucrt64\share\qemu\edk2-x86_64-code.fd"
                    if os.path.exists(msys_efi):
                        efi_src = msys_efi
            elif platform.system() == "Darwin":
                efi_src = "/opt/homebrew/share/qemu/edk2-x86_64-code.fd"
            else:
                efi_src = "/usr/share/qemu/OVMF.fd"
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
        port = get_free_port(start=5900 + start_disp, end=5900 + 100)
        if port is None:
            fatal("No available VNC display ports")
        disp = port - 5900
        args_qemu.append("-display")
        args_qemu.append("vnc={}:{}".format(addr, disp))
    
    if config['qmon']:
        args_qemu.extend(["-monitor", "telnet:localhost:{},server,nowait,nodelay".format(config['qmon'])])

    # Execution
    cmd_list = [qemu_bin] + args_qemu
    cmd_text = format_command_for_display(cmd_list)
    debuglog(config['debug'], "CMD:\n  " + cmd_text)

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

        try:
            time.sleep(1)
            if proc.poll() is not None:
                fail_with_output("QEMU exited immediately")


            log("Started QEMU (PID: {})".format(proc.pid))

            tail_stop_event = threading.Event()
            if config['debug'] and serial_log_file:
                 t = threading.Thread(target=tail_serial_log, args=(serial_log_file, tail_stop_event))
                 t.daemon = True
                 t.start()
            
            # Config SSH
            os.chmod(os.path.expanduser("~"), 0o755)
            ssh_dir = os.path.join(os.path.expanduser("~"), ".ssh")
            if not os.path.exists(ssh_dir):
                os.makedirs(ssh_dir)
                if IS_WINDOWS:
                    tighten_windows_permissions(ssh_dir)
                else:
                    os.chmod(ssh_dir, 0o700)
            
            if vmpub_file and os.path.exists(vmpub_file):
                with open(vmpub_file, 'r') as f:
                    pub = f.read()
                with open(os.path.join(ssh_dir, "authorized_keys"), 'a') as f:
                    f.write(pub)

            conf_path = os.path.join(ssh_dir, "config.d")
            if not os.path.exists(conf_path):
                os.makedirs(conf_path)

            global_identity_block = ""
            if hostid_file:
                # Apply the VM key to all SSH hosts (requested behavior).
                global_identity_block = "Host *\n  IdentityFile {}\n  StrictHostKeyChecking no\n  UserKnownHostsFile {}\n\n".format(
                    hostid_file,
                    SSH_KNOWN_HOSTS_NULL,
                )

            def build_ssh_host_config(host_aliases):
                host_spec = " ".join(str(x) for x in host_aliases if x)
                host_block = "Host {}\n  StrictHostKeyChecking no\n  UserKnownHostsFile {}\n  User root\n  HostName localhost\n  Port {}\n".format(
                    host_spec,
                    SSH_KNOWN_HOSTS_NULL,
                    config['sshport'],
                )
                return "\n" + global_identity_block + host_block

            # Primary alias (vm_name)
            ssh_config_content = build_ssh_host_config([vm_name])

            vm_conf_file = os.path.join(conf_path, "{}.conf".format(vm_name))
            debuglog(config['debug'], "Generated SSH config (vm name) -> {}:\n{}".format(vm_conf_file, ssh_config_content.strip()))
            
            os.unlink(vm_conf_file) if os.path.exists(vm_conf_file) else None
            
            # Write config for VM name
            with open(vm_conf_file, 'w') as f:
                f.write(ssh_config_content)

            if IS_WINDOWS:
                tighten_windows_permissions(os.path.join(conf_path, "{}.conf".format(vm_name)))
            else:
                os.chmod(os.path.join(conf_path, "{}.conf".format(vm_name)), 0o600)

            # Write config for Port
            port_aliases = [str(config['sshport'])]
            if config.get('sshname'):
                port_aliases.append(config['sshname'])
            port_conf_content = build_ssh_host_config(port_aliases)

            port_conf_file = os.path.join(conf_path, "{}.conf".format(config['sshport']))
            debuglog(config['debug'], "Generated SSH config (port alias) -> {}:\n{}".format(port_conf_file, port_conf_content.strip()))
            
            os.unlink(port_conf_file) if os.path.exists(port_conf_file) else None
            
            with open(port_conf_file, 'w') as f: 
                 f.write(port_conf_content)
            
            if IS_WINDOWS:
                tighten_windows_permissions(os.path.join(conf_path, "{}.conf".format(config['sshport'])))
            else:
                os.chmod(os.path.join(conf_path, "{}.conf".format(config['sshport'])), 0o600)

            main_conf = os.path.join(ssh_dir, "config")
            if not os.path.exists(main_conf):
                open(main_conf, 'w').close()
                if IS_WINDOWS:
                  tighten_windows_permissions(main_conf)
                else:
                  os.chmod(main_conf, 0o600)
            
            with open(main_conf, 'r') as f:
                content = f.read()
                if "Include config.d" not in content:
                    with open(main_conf, 'a') as fa:
                        fa.write("\nInclude config.d/*.conf\n")

            # Wait for boot
            wait_msg = "Waiting for VM to boot (port {})...".format(config['sshport'])
            debuglog(config['debug'], wait_msg)
            success = False
            interactive_wait = sys.stdout.isatty()
            wait_start = time.time()
            last_wait_tick = [-1]  # hundredth-of-a-second ticks
            wait_timer_stop = threading.Event()
            wait_timer_thread = None

            def update_wait_timer():
                if not interactive_wait:
                    return
                tick = int((time.time() - wait_start) * 100)
                if tick == last_wait_tick[0]:
                    return
                last_wait_tick[0] = tick
                elapsed = tick / 100.0

                def supports_ansi_color(stream):
                    try:
                        if not hasattr(stream, "isatty") or not stream.isatty():
                            return False
                    except Exception:
                        return False
                    if os.environ.get("NO_COLOR") is not None:
                        return False
                    if os.environ.get("TERM") == "dumb":
                        return False
                    if IS_WINDOWS:
                        # Best-effort heuristics: modern terminals set one of these.
                        if os.environ.get("WT_SESSION"):
                            return True
                        if os.environ.get("ANSICON"):
                            return True
                        if os.environ.get("ConEmuANSI", "").upper() == "ON":
                            return True
                        if os.environ.get("TERM"):
                            return True
                        return False
                    return True

                use_color = supports_ansi_color(sys.stdout)
                green = "\x1b[32m"
                reset = "\x1b[0m"

                try:
                    cols = shutil.get_terminal_size(fallback=(80, 20)).columns
                except Exception:
                    cols = 80

                prefix = "{} {:.2f}s".format(wait_msg, elapsed)

                # Leave at least a small bar area; if the terminal is too narrow, just print the prefix.
                bar_total = max(0, cols - len(prefix) - 1)
                if bar_total < 10:
                    line = prefix
                    visible_len = len(prefix)
                else:
                    # Build a progress bar that repeatedly:
                    # 1) fills left->right to full
                    # 2) clears left->right back to empty
                    inner = max(1, bar_total - 2)  # brackets take 2 chars

                    speed_cells_per_sec = 18.0

                    bg_char = "░"

                    def shade_for_fraction(filled_fraction):
                        # filled_fraction: 0.0 (empty) .. 1.0 (full)
                        # Only render a fully solid block when truly full.
                        if filled_fraction >= 1.0:
                            return "█"
                        if filled_fraction >= 0.75:
                            return "▓"
                        if filled_fraction >= 0.50:
                            return "▒"
                        if filled_fraction >= 0.25:
                            return "░"
                        return bg_char

                    cells = [bg_char] * inner
                    bright = [False] * inner
                    if inner == 1:
                        # Tiny terminal; just blink between empty/full-ish
                        frac = (elapsed * speed_cells_per_sec) % 1.0
                        cells[0] = shade_for_fraction(frac)
                        bright[0] = (cells[0] != bg_char)
                    else:
                        # One full cycle = fill across inner cells, then clear across inner cells.
                        fill_duration = float(inner) / max(0.001, speed_cells_per_sec)
                        cycle = 2.0 * fill_duration
                        t = elapsed % cycle

                        if t < fill_duration:
                            # Filling: boundary moves from 0 -> inner
                            boundary = t * speed_cells_per_sec
                            # Prevent float rounding from hitting the next cell early.
                            if boundary >= inner:
                                boundary = inner - 1e-9
                            full = int(boundary)
                            frac = boundary - full
                            for idx in range(min(full, inner)):
                                cells[idx] = "█"
                                bright[idx] = True
                            if 0 <= full < inner:
                                cells[full] = shade_for_fraction(frac)
                                bright[full] = (frac > 0.0)
                        else:
                            # Clearing: left edge moves from 0 -> inner
                            cleared = (t - fill_duration) * speed_cells_per_sec
                            if cleared >= inner:
                                cleared = inner - 1e-9
                            full_empty = int(cleared)
                            frac = cleared - full_empty
                            # left side empty
                            for idx in range(min(full_empty, inner)):
                                cells[idx] = bg_char
                                bright[idx] = False
                            # boundary cell fades out as we clear
                            if 0 <= full_empty < inner:
                                cells[full_empty] = shade_for_fraction(1.0 - frac)
                                bright[full_empty] = (frac < 1.0)
                            # remaining cells stay filled
                            for idx in range(full_empty + 1, inner):
                                cells[idx] = "█"
                                bright[idx] = True

                    bar_text = "[{}]".format("".join(cells))
                    if use_color:
                        dim_green = "\x1b[2;32m"
                        bar_cells = []
                        current_bright = None
                        for idx, ch in enumerate(cells):
                            want_bright = bright[idx]
                            if want_bright != current_bright:
                                bar_cells.append(green if want_bright else dim_green)
                                current_bright = want_bright
                            bar_cells.append(ch)
                        bar_render = "[" + "".join(bar_cells) + reset + "]"
                    else:
                        bar_render = bar_text
                    line = "{} {}".format(prefix, bar_render)
                    visible_len = len(prefix) + 1 + len(bar_text)

                # Pad to clear any leftover chars from previous frame.
                if cols and visible_len < cols:
                    line = line + (" " * (cols - visible_len))

                sys.stdout.write("\r" + line)
                sys.stdout.flush()

            if interactive_wait:
                def wait_timer_worker():
                    while not wait_timer_stop.is_set():
                        update_wait_timer()
                        # 15 updates per second
                        time.sleep(1.0 / 15.0)
                wait_timer_thread = threading.Thread(target=wait_timer_worker)
                wait_timer_thread.daemon = True
                wait_timer_thread.start()

            def finish_wait_timer():
                if not interactive_wait or last_wait_tick[0] < 0:
                    return
                # Render a final, fully-filled bar so the last frame doesn't look partial.
                elapsed = last_wait_tick[0] / 100.0

                def supports_ansi_color(stream):
                    try:
                        if not hasattr(stream, "isatty") or not stream.isatty():
                            return False
                    except Exception:
                        return False
                    if os.environ.get("NO_COLOR") is not None:
                        return False
                    if os.environ.get("TERM") == "dumb":
                        return False
                    if IS_WINDOWS:
                        if os.environ.get("WT_SESSION"):
                            return True
                        if os.environ.get("ANSICON"):
                            return True
                        if os.environ.get("ConEmuANSI", "").upper() == "ON":
                            return True
                        if os.environ.get("TERM"):
                            return True
                        return False
                    return True

                use_color = supports_ansi_color(sys.stdout)
                green = "\x1b[32m"
                reset = "\x1b[0m"

                try:
                    cols = shutil.get_terminal_size(fallback=(80, 20)).columns
                except Exception:
                    cols = 80

                prefix = "{} {:.2f}s".format(wait_msg, elapsed)
                bar_total = max(0, cols - len(prefix) - 1)
                if bar_total < 10:
                    line = prefix
                    visible_len = len(prefix)
                else:
                    inner = max(1, bar_total - 2)
                    bar_text = "[{}]".format("█" * inner)
                    if use_color:
                        bar_render = "[" + green + ("█" * inner) + reset + "]"
                    else:
                        bar_render = bar_text
                    line = "{} {}".format(prefix, bar_render)
                    visible_len = len(prefix) + 1 + len(bar_text)

                if cols and visible_len < cols:
                    line = line + (" " * (cols - visible_len))

                sys.stdout.write("\r" + line + "\n")
                sys.stdout.flush()
            
            ssh_base_cmd = [
                "ssh",
                "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile={}".format(SSH_KNOWN_HOSTS_NULL),
                "-o", "LogLevel=ERROR",
            ]
            if hostid_file:
                ssh_base_cmd.extend(["-i", hostid_file])
            
            ssh_base_cmd.extend([
                "-p", str(config['sshport']),
                "root@localhost"
            ])
            
            for i in range(300):
                if proc.poll() is not None:
                    fail_with_output("QEMU terminated during boot")
                ret, timed_out = call_with_timeout(
                    ssh_base_cmd + ["exit"],
                    timeout_seconds=5,
                    stdout=DEVNULL,
                    stderr=DEVNULL
                )
                if timed_out:
                    continue
                if ret == 0:
                    success = True
                    break
                time.sleep(2)
            
            wait_timer_stop.set()
            if wait_timer_thread:
                wait_timer_thread.join(0.2)
            finish_wait_timer()
            if not success:
                fatal("Boot timed out.")
            
            debuglog(config['debug'], "VM Ready! Connect with: ssh {}".format(vm_name))
            
            # Post-boot config: Setup reverse SSH config inside VM
            current_user = getpass.getuser()
            host_port_line = ""
            if config['hostsshport']:
                host_port_line = "  Port {}\n".format(config['hostsshport'])
            vm_ssh_config = """
StrictHostKeyChecking=no

Host host
  HostName  192.168.122.2
{host_port}  User {user}
  ServerAliveInterval 1
""".format(host_port=host_port_line, user=current_user)
            
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
                        if ':' not in vpath_str:
                            raise ValueError
                        debuglog(config['debug'], "Processing -v argument: {}".format(vpath_str))
                        vhost, vguest = vpath_str.rsplit(':', 1)
                        vhost = os.path.abspath(vhost)
                        if not vhost or not vguest:
                            raise ValueError
                        debuglog(config['debug'], "Mounting host dir: {} to guest: {}".format(vhost, vguest))
                        
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
                 if config.get('sshname'):
                     log("Or just:  ssh " + str(config['sshname']))
                 log("======================================")

            if not config['detach']:
                ssh_cmd = ssh_base_cmd + ssh_passthrough
                debuglog(config['debug'], "SSH command: {}".format(format_command_for_display(ssh_cmd)))
                subprocess.call(ssh_cmd)
            # Avoid noisy banner when running as PID 1 inside a container
            if os.getpid() != 1:
                log("======================================")
                log("The VM is still running in background.")
                log("You can login the VM with:  ssh " + vm_name)
                log("Or just:  ssh " + str(config['sshport']))
                if config.get('sshname'):
                    log("Or just:  ssh " + str(config['sshname']))
                log("======================================")
        except KeyboardInterrupt:
            if not config['detach']:
                terminate_process(proc, "QEMU")
            raise

if __name__ == '__main__':
    main()
