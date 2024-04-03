from argparse import ArgumentParser
from os import rmdir, remove, makedirs, listdir, system
from random import randint, uniform
from threading import Thread, Lock, enumerate
from time import sleep
from cffi import FFI
from requests import head, get
from termcolor import cprint, colored
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

ap = ArgumentParser('Thread Downloader', 'Download files quickly.',
                    '''This is a thread downloader.\nYou can use it Download large file quickly.''')
ap.add_argument('--URL', '-u', type=str, required=True, help='URL')
ap.add_argument('--dir', '-d', type=str, required=True, help='Download dir')
ap.add_argument('--thread-num', '-t', type=int, required=False, default=16, help='Thread num')
meg = ap.add_mutually_exclusive_group()
meg.add_argument('--shut', '-S', action='store_true', required=False,
                 help='Use "shutdown /p" to shutdown your computer.')
meg.add_argument('--sleep', '-s', action='store_true', required=False, help='Use "shutdown /h" to sleep your computer.')
meg.add_argument('--reboot', '-r', action='store_true', required=False,
                 help='Use "shutdown /r /t 0" to reboot your computer.')
ap.add_argument('--no-ssl-verify', action='store_false', required=False)
args = vars(ap.parse_args())
del ap, meg


def download(url: str, _from: int, to: int, id):
    global rates, FILE
    rates.append(0)
    reponse = get(url, headers={'Range': f"bytes={_from}-{to}",
                                'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0"},
                  stream=True, verify=args['no_ssl_verify'],
                  proxies={'http': None, 'https': None})
    if reponse.ok:
        length = int(reponse.headers['Content-Length'])
        with open(TMPDIR + f'\\{id}', 'wb+') as file:
            for ch in reponse:
                file.write(ch)
                rates[id] = file.tell() / length
            reponse.close()
    else:
        cprint(f'\nError:{reponse.status_code} {reponse.reason}', 'red')
        exit(1)


def mktmpdir(downloaddir) -> str:
    seed = hex(randint(0x100000, 0x999999)).lstrip("0x")
    tmp_dir = downloaddir + f'\\.tmp\\{seed}'
    try:
        makedirs(tmp_dir)
        return tmp_dir
    except FileExistsError:
        return mktmpdir(downloaddir)


disable_warnings(InsecureRequestWarning)

ffi=FFI()
kernel32 = ffi.dlopen('kernel32.dll')
SetThreadExecutionState = kernel32.SetThreadExecutionState
SetThreadExecutionState.argtypes = [ffi.c_ulong]
SetThreadExecutionState.restype = ffi.c_ulong
SetThreadExecutionState(0x00000001 | 0x00000002)
del ffi,kernel32,SetThreadExecutionState

cprint('Finding file...', 'green')
reponse = head(args['URL'], allow_redirects=True)
if not reponse.ok:
    cprint(f'Error:{reponse.status_code} {reponse.reason}', 'red')
    exit(1)
match reponse.headers.get('Accept-Ranges'):
    case 'bytes':
        cprint('Server support "Range" header.', 'green')
    case 'none' | None:
        cprint('Server don\'t support "Range" header.', 'red')
        exit(1)
    case _:
        cprint('This server can\'t threading download.', 'red')
        exit(1)
LENGTH = int(reponse.headers.get('Content-Length', 0))

v1 = reponse.url.rfind('/') + 1
v2 = reponse.url.rfind('?', v1)
if v2 == -1:
    _name = reponse.url[v1:].rstrip('?')
else:
    _name = reponse.url[v1:v2]
del v1, v2

name = input(colored(f'Please enter the file name[{_name}]:'))
if not name:
    FILENAME = _name
else:
    FILENAME = name
del name, _name

print('File found:' + colored(f'{FILENAME}', "blue"), 'Size:' + colored(f'{LENGTH} B', ),
      'Type:' + colored(f'{reponse.headers.get("Content-Type")}', 'grey'), sep='\n')
if LENGTH == 0:
    cprint('URL is not right.', 'red')
    exit(1)
ONELENGTH = (LENGTH - 1) // args.get('thread_num')

TMPDIR = mktmpdir(args.get('dir'))

# print(f"Progress(downloading):{0.0:.2f}%[", colored(f"{' ' * 50}", 'green'), "]", sep='', end='\r')
rates = []
i = -1
lock = Lock()
for i in range(args.get('thread_num') - 1):
    start, end = i * ONELENGTH, (i + 1) * ONELENGTH
    t = Thread(target=download, args=(reponse.url, start, end - 1, i), daemon=True)
    cprint(f'Start thread {i}/{args.get('thread_num')}', 'green',end='\r')
    t.start()
    sleep(uniform(0,5))
start, end = i * ONELENGTH, (i + 1) * ONELENGTH
t = Thread(target=download, args=(reponse.url, ONELENGTH * (i + 1), LENGTH, i + 1))
t.start()
del i, t

while True:
    try:
        rate = sum(rates) / len(rates)
    except ZeroDivisionError:
        rate = 0.0
    print(f"Progress(downloading):{rate * 100:.2f}%[", colored(f"{round(rate * 50) * '—': <50}", 'green'), "]", sep='',
          end='\r')
    for thread in enumerate():
        if not thread.is_alive(): thread.join()
    if rate == 1: break
cprint('\nDownloading is over.', 'green')

mfile = open(args.get('dir') + '\\' + FILENAME, 'wb')
for i in range(0, listdir(TMPDIR).__len__()):
    sfile = open(TMPDIR + '\\' + str(i), 'rb')
    while True:
        data = sfile.read(4096)
        if not data: break
        mfile.write(data)
        rate = mfile.tell() / LENGTH
        print(f"Progress(copying-{i}):{rate * 100:.2f}%[", colored(f"{round(rate * 50) * '—': <50}", 'green'), "]",
              sep='', end='\r')
    sfile.close()
    remove(sfile.name)
    mfile.flush()
try:
    rmdir(TMPDIR)
    rmdir(args.get('dir') + '\\.tmp')
except OSError:
    cprint('\nTemp dir can\'t remove.', 'yellow')
cprint('\nCopying is over.', 'green')
cprint('\nAll is over.', 'green')

if args.get('shut', False):
    system('shutdown /p')
if args.get('sleep', False):
    system('shutdown /h')
if args.get('reboot', False):
    system('shutdown /r /t 0')
