#!/usr/bin/env python3
# made with <3 by prodbyeternal for ThinkDifferentInc.
# huge thank you to acidanthera for leading the way of vanilla hackintoshing! :D

import sys
import subprocess

def ensure_package(package_name):
    try:
        __import__(package_name)
    except ImportError:
        print(f"Required package '{package_name}' not found. Installing...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", package_name],
                stdout=subprocess.DEVNULL
            )
        except subprocess.CalledProcessError:
            print(f"Failed to install '{package_name}'. Please install it manually.")
            sys.exit(1)

        try:
            __import__(package_name)
        except ImportError:
            print(f"Installation of '{package_name}' appears to have failed.")
            sys.exit(1)

ensure_package("rich")

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich.progress import (
    Progress, SpinnerColumn, BarColumn, TextColumn,
    TimeRemainingColumn, TransferSpeedColumn, DownloadColumn
)
from rich import box

import os
import hashlib
import struct
import random
import string
from dataclasses import dataclass
from urllib.request import Request, HTTPError, urlopen
from urllib.parse import urlparse

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.progress import (
        Progress, SpinnerColumn, BarColumn, TextColumn,
        TimeRemainingColumn, TransferSpeedColumn, DownloadColumn
    )
    from rich import box
except ImportError:
    print("This script requires the 'rich' package. Install it with: pip install rich")
    sys.exit(1)

console = Console()

# og macrecovery constants and cryptography

MLB_ZERO = '00000000000000000'
TYPE_SID = 16
TYPE_K = 64
TYPE_FG = 64

INFO_PRODUCT = 'AP'
INFO_IMAGE_LINK = 'AU'
INFO_IMAGE_HASH = 'AH'
INFO_IMAGE_SESS = 'AT'
INFO_SIGN_LINK = 'CU'
INFO_SIGN_HASH = 'CH'
INFO_SIGN_SESS = 'CT'
INFO_REQURED = [INFO_PRODUCT, INFO_IMAGE_LINK, INFO_IMAGE_HASH, INFO_IMAGE_SESS, INFO_SIGN_LINK, INFO_SIGN_HASH, INFO_SIGN_SESS]

Apple_EFI_ROM_public_key_1 = 0xC3E748CAD9CD384329E10E25A91E43E1A762FF529ADE578C935BDDF9B13F2179D4855E6FC89E9E29CA12517D17DFA1EDCE0BEBF0EA7B461FFE61D94E2BDF72C196F89ACD3536B644064014DAE25A15DB6BB0852ECBD120916318D1CCDEA3C84C92ED743FC176D0BACA920D3FCF3158AFF731F88CE0623182A8ED67E650515F75745909F07D415F55FC15A35654D118C55A462D37A3ACDA08612F3F3F6571761EFCCBCC299AEE99B3A4FD6212CCFFF5EF37A2C334E871191F7E1C31960E010A54E86FA3F62E6D6905E1CD57732410A3EB0C6B4DEFDABE9F59BF1618758C751CD56CEF851D1C0EAA1C558E37AC108DA9089863D20E2E7E4BF475EC66FE6B3EFDCF

ChunkListHeader = struct.Struct('<4sIBBBxQQQ')
Chunk = struct.Struct('<I32s')

# macrecovery core logic

def run_query(url, headers, post=None, raw=False):
    if post is not None:
        data = '\n'.join(entry + '=' + post[entry] for entry in post).encode()
    else:
        data = None
    req = Request(url=url, headers=headers, data=data)
    try:
        response = urlopen(req)
        if raw:
            return response
        return dict(response.info()), response.read()
    except HTTPError as e:
        console.print(f'[bold red]ERROR:[/bold red] "{e}" when connecting to {url}')
        sys.exit(1)

def generate_id(id_type, id_value=None):
    return id_value or ''.join(random.choices(string.hexdigits[:16].upper(), k=id_type))

def verify_chunklist(cnkpath):
    with open(cnkpath, 'rb') as f:
        hash_ctx = hashlib.sha256()
        data = f.read(ChunkListHeader.size)
        hash_ctx.update(data)
        magic, header_size, file_version, chunk_method, signature_method, chunk_count, chunk_offset, signature_offset = ChunkListHeader.unpack(data)
        assert magic == b'CNKL'
        assert header_size == ChunkListHeader.size
        assert file_version == 1
        assert chunk_method == 1
        assert signature_method in [1, 2]
        assert chunk_count > 0
        assert chunk_offset == 0x24
        assert signature_offset == chunk_offset + Chunk.size * chunk_count
        for _ in range(chunk_count):
            data = f.read(Chunk.size)
            hash_ctx.update(data)
            chunk_size, chunk_sha256 = Chunk.unpack(data)
            yield chunk_size, chunk_sha256
        digest = hash_ctx.digest()
        if signature_method == 1:
            data = f.read(256)
            signature = int.from_bytes(data, 'little')
            plaintext = int(f'0x1{"f"*404}003031300d060960864801650304020105000420{"0"*64}', 16) | int.from_bytes(digest, 'big')
            assert pow(signature, 0x10001, Apple_EFI_ROM_public_key_1) == plaintext
        elif signature_method == 2:
            data = f.read(32)
            assert data == digest
            raise RuntimeError('Chunklist missing digital signature')

def get_session():
    headers = {
        'Host': 'osrecovery.apple.com',
        'Connection': 'close',
        'User-Agent': 'InternetRecovery/1.0',
    }
    headers, _ = run_query('http://osrecovery.apple.com/', headers)
    for header in headers:
        if header.lower() == 'set-cookie':
            cookies = headers[header].split('; ')
            for cookie in cookies:
                return cookie if cookie.startswith('session=') else ...
    raise RuntimeError('No session in headers ' + str(headers))

def get_image_info(session, bid, mlb=MLB_ZERO, diag=False, os_type='default', cid=None):
    headers = {
        'Host': 'osrecovery.apple.com',
        'Connection': 'close',
        'User-Agent': 'InternetRecovery/1.0',
        'Cookie': session,
        'Content-Type': 'text/plain',
    }
    post = {
        'cid': generate_id(TYPE_SID, cid),
        'sn': mlb,
        'bid': bid,
        'k': generate_id(TYPE_K),
        'fg': generate_id(TYPE_FG)
    }
    
    url = 'http://osrecovery.apple.com/InstallationPayload/Diagnostics' if diag else 'http://osrecovery.apple.com/InstallationPayload/RecoveryImage'
    if not diag:
        post['os'] = os_type

    headers, output = run_query(url, headers, post)
    output = output.decode('utf-8')
    info = {}
    
    for line in output.split('\n'):
        try:
            key, value = line.split(': ')
            info[key] = value
        except ValueError:
            continue

    for k in INFO_REQURED:
        if k not in info:
            raise RuntimeError(f'Missing key {k}')
    return info

def save_image(url, sess, filename='', directory='', progress_obj=None, task_id=None):
    purl = urlparse(url)
    headers = {
        'Host': purl.hostname,
        'Connection': 'close',
        'User-Agent': 'InternetRecovery/1.0',
        'Cookie': '='.join(['AssetToken', sess])
    }

    if not os.path.exists(directory):
        os.makedirs(directory)

    if filename == '':
        filename = os.path.basename(purl.path)

    filepath = os.path.join(directory, filename)

    with open(filepath, 'wb') as fh:
        response = run_query(url, headers, raw=True)
        resp_headers = dict(response.headers)
        totalsize = -1
        
        for header in resp_headers:
            if header.lower() == 'content-length':
                totalsize = int(resp_headers[header])
                break

        if progress_obj and task_id is not None:
            progress_obj.update(task_id, total=totalsize if totalsize > 0 else None)

        size = 0
        while True:
            chunk = response.read(2**20)
            if not chunk:
                break
            fh.write(chunk)
            size += len(chunk)
            if progress_obj and task_id is not None:
                progress_obj.update(task_id, completed=size)

    return filepath

def verify_image(dmgpath, cnkpath):
    with console.status("[cyan]Verifying image integrity...[/cyan]") as status:
        with open(dmgpath, 'rb') as dmgf:
            for cnkcount, (cnksize, cnkhash) in enumerate(verify_chunklist(cnkpath), 1):
                status.update(f"[cyan]Verifying chunk {cnkcount} ({cnksize} bytes)...[/cyan]")
                cnk = dmgf.read(cnksize)
                if len(cnk) != cnksize:
                    raise RuntimeError(f'Invalid chunk {cnkcount} size: expected {cnksize}, read {len(cnk)}')
                if hashlib.sha256(cnk).digest() != cnkhash:
                    raise RuntimeError(f'Invalid chunk {cnkcount}: hash mismatch')
            if dmgf.read(1) != b'':
                raise RuntimeError('Invalid image: larger than chunklist')


# thank you nala

@dataclass
class MacOSVersion:
    name: str
    build: str
    model: str
    extra_args: list

VERSIONS = [
    MacOSVersion("Lion", "Mac-2E6FAB96566FE58C", "00000000000F25Y00", []),
    MacOSVersion("Mountain Lion", "Mac-7DF2A3B5E5D671ED", "00000000000F65100", []),
    MacOSVersion("Mavericks", "Mac-F60DEB81FF30ACF6", "00000000000FNN100", []),
    MacOSVersion("Yosemite", "Mac-E43C1C25D4880AD6", "00000000000GDVW00", []),
    MacOSVersion("El Capitan", "Mac-FFE5EF870D7BA81A", "00000000000GQRX00", []),
    MacOSVersion("Sierra", "Mac-77F17D7DA9285301", "00000000000J0DX00", []),
    MacOSVersion("High Sierra", "Mac-7BA5B2D9E42DDD94", "00000000000J80300", []),
    MacOSVersion("Mojave", "Mac-7BA5B2DFE22DDD8C", "00000000000KXPG00", []),
    MacOSVersion("Catalina", "Mac-CFF7D910A743CAAF", "00000000000PHCD00", []),
    MacOSVersion("Big Sur", "Mac-2BD1B31983FE1663", "00000000000000000", []),
    MacOSVersion("Monterey", "Mac-E43C1C25D4880AD6", "00000000000000000", []),
    MacOSVersion("Ventura", "Mac-B4831CEBD52A0C4C", "00000000000000000", []),
    MacOSVersion("Sonoma", "Mac-827FAC58A8FDFA22", "00000000000000000", []),
    MacOSVersion("Sequoia", "Mac-7BA5B2D9E42DDD94", "00000000000000000", []),
    MacOSVersion("Tahoe", "Mac-CFF7D910A743CAAF", "00000000000000000", ["-os", "latest"]),
]

def print_header():
    console.print(
        Panel.fit(
            "[bold cyan]ocrecovery[/bold cyan]  [green]•[/green]  recovery for the 21st century\n"
            "[dim]made with <3 by prodbyeternal.[/dim]",
            border_style="cyan",
        )
    )

def print_menu():
    table = Table(title="Available macOS Versions", box=box.SIMPLE_HEAVY)
    table.add_column("#", justify="right", style="bold")
    table.add_column("Version", style="cyan")
    table.add_column("Board ID", style="green")

    for idx, version in enumerate(VERSIONS, start=1):
        table.add_row(str(idx), version.name, version.build)

    console.print(table)

def run_download(version: MacOSVersion):
    console.print(Panel(f"[bold green]Fetching[/bold green] {version.name}", border_style="green"))

    # Parse arguments previously passed to subprocess
    os_type = 'latest' if '-os' in version.extra_args and 'latest' in version.extra_args else 'default'
    diag = '-diag' in version.extra_args
    outdir = "com.apple.recovery.boot"

    try:
        session = get_session()
        info = get_image_info(session, bid=version.build, mlb=version.model, diag=diag, os_type=os_type)

        with Progress(
            SpinnerColumn(style="cyan"),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=None, style="cyan", complete_style="green"),
            TextColumn("[bold]{task.percentage:>3.0f}%"),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console,
            transient=False,
        ) as progress:
            
            # Download Chunklist
            cnk_task = progress.add_task(f"Downloading Chunklist", total=100)
            cnkpath = save_image(info[INFO_SIGN_LINK], info[INFO_SIGN_SESS], '', outdir, progress, cnk_task)

            # Download DMG
            dmg_task = progress.add_task(f"Downloading BaseSystem.dmg", total=100)
            dmgpath = save_image(info[INFO_IMAGE_LINK], info[INFO_IMAGE_SESS], '', outdir, progress, dmg_task)

        # Verification step
        verify_image(dmgpath, cnkpath)
        console.print("\n[bold green]✔ All operations completed successfully[/bold green]")

    except Exception as e:
        console.print(f"\n[bold red]✖ Operation failed:[/bold red] {e}")

def main():
    print_header()
    print_menu()

    while True:
        choice = Prompt.ask("\nSelect version to download (or 'q' to quit)")

        if choice.lower() == "q":
            console.print("[bold yellow]Exiting...[/bold yellow]")
            sys.exit(0)

        if not choice.isdigit():
            console.print("[red]Invalid input. Enter a number.[/red]")
            continue

        index = int(choice) - 1

        if 0 <= index < len(VERSIONS):
            run_download(VERSIONS[index])
            break
        else:
            console.print("[red]Selection out of range.[/red]")

if __name__ == "__main__":
    main()
