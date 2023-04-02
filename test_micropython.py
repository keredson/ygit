import os, tempfile, zlib, io, socket, hashlib, json, pytest, mpy_cross, sys

import ampy.files
import ampy.pyboard

import ygit

from test_localhost import build_repo

pyb = None
initted = False

def init_board(clear=True):
  global pyb, initted
  if not pyb:
    pyb = ampy.pyboard.Pyboard('/dev/ttyUSB0', baudrate=115200)
  board_files = ampy.files.Files(pyb)
  if clear:
    existing_files = board_files.ls(long_format=False)
    for fn in existing_files:
      if fn in ('/boot.py','/ygit.mpy','/small.z',): continue
      print('removing', fn)
      try:
        board_files.rm(fn)
      except ampy.pyboard.PyboardError:
        board_files.rmdir(fn)
  if initted: return pyb
  mpy_cross.run('ygit.py')
  if check_ygit_file(pyb):
    copy_ygit_file(pyb, board_files)
  initted = True
  return pyb  


def check_ygit_file(pyb):
  pyb.enter_raw_repl()
  try:
    h = hashlib.sha1()
    with open('ygit.mpy','rb') as f:
      h.update(f.read())
    sig = h.hexdigest()
    cmd = '''import hashlib, binascii
h = hashlib.sha1()
f = open('ygit.mpy','rb')
h.update(f.read())
print(binascii.hexlify(h.digest()).decode())
del h
f.close()
del f'''
    board_sig = pyb.exec_(cmd).decode().strip()
    #print('ygit.mpy board/local sha1:', board_sig, sig)
    return board_sig != sig
  finally:
    pyb.exit_raw_repl()
  

def copy_ygit_file(pyb, board_files):
  print('copying: ygit.mpy')
  with open('ygit.mpy','rb') as f:
    board_files.put('ygit.mpy.gz', zlib.compress(f.read()))
  pyb.enter_raw_repl()
  try:
    pyb.exec_('''import zlib, os
with open('ygit.mpy.gz','rb') as fin:
  with open('ygit.mpy','wb') as fout:
    s = zlib.DecompIO(fin)
    while data:=s.read(256):
      fout.write(data)
del s, fin, fout
os.remove('ygit.mpy.gz')
gc.collect()
    ''', stream_output=True)
  finally:
    pyb.exit_raw_repl()


def test_gh():
  pyb = init_board()
  pyb.enter_raw_repl()
  pyb.exec_('import ygit, os', stream_output=True)
  pyb.exec_("repo = ygit.Repo('ugit_test')", stream_output=True)
  pyb.exec_("repo._init('https://github.com/turfptax/ugit_test.git')", stream_output=True)
  pyb.exec_("repo.fetch()", stream_output=True)
  pyb.exec_("repo.checkout()", stream_output=True)
  out = pyb.exec_("print(os.listdir('ugit_test'))")
  assert out.decode().strip() == "['.ygit', 'Folder', 'README.md', 'boot.py']"
  pyb.exit_raw_repl()


def test_bigger_clone():
  pyb = init_board()
  pyb.enter_raw_repl()
  pyb.exec_('import ygit, os', stream_output=True)
  pyb.exec_("repo = ygit.Repo('ygit')", stream_output=True)
  pyb.exec_("repo._init('https://github.com/keredson/ygit.git')", stream_output=True)
  pyb.exec_("repo.fetch()", stream_output=True)
  pyb.exec_("repo.checkout()", stream_output=True)
  assert 'ygit.py' in pyb.exec_("print(os.listdir('ygit'))").decode().strip()
  pyb.exit_raw_repl()


def test_checkout_status():
  pyb = init_board()
  pyb.enter_raw_repl()
  pyb.exec_('import ygit, io', stream_output=True)
  pyb.exec_("repo = ygit.Repo('ugit_test')", stream_output=True)
  pyb.exec_("repo._init('https://github.com/turfptax/ugit_test.git')", stream_output=True)
  pyb.exec_("repo.fetch(ref='7e5c62596935f96518a931f97ded52b6e8b01594')", stream_output=True)
  pyb.exec_("repo.checkout(ref='7e5c62596935f96518a931f97ded52b6e8b01594')", stream_output=True)
  pyb.exec_("repo.fetch(ref='cde9c4e1c7a178bb81ccaefb74824cc01e3638e7')", stream_output=True)
  pyb.exec_('out = io.StringIO()', stream_output=True)
  pyb.exec_("repo.status(ref='cde9c4e1c7a178bb81ccaefb74824cc01e3638e7', out=out)", stream_output=True)
  out = pyb.exec_('print(out.getvalue())')
  pyb.exit_raw_repl()
  assert out==b'A ugit_test/Folder\r\nD /README.md\r\nD /boot.py\r\nA ugit_test/Folder\r\nA ugit_test/Folder/SubFolder\r\nD /Folder/in_second.py\r\nA ugit_test/Folder/SubFolder\r\nD /Folder/SubFolder/third_layer.py\r\n\r\n'



def test_branch():
  pyb = init_board()
  pyb.enter_raw_repl()
  git, d = build_repo()
  with open(os.path.join(d,'test.txt'),'w') as f:
    f.write('v1')
  git.add('test.txt')
  git.commit('test.txt', message='v1')
  main_branch = git.branch(show_current=True).strip()
  git.checkout('-b', 'abranch')
  with open(os.path.join(d,'branch.txt'),'w') as f:
    f.write('a branch')
  git.add('branch.txt')
  git.commit('branch.txt', message='added a branch')
  git.checkout(main_branch)
  pyb.exec_('import ygit, io, os', stream_output=True)
  pyb.exec_("repo = ygit.Repo('test_branch')", stream_output=True)
  pyb.exec_(f"repo._init('http://{get_ip()}:8889/{os.path.basename(d)}')", stream_output=True)
  pyb.exec_("repo.fetch()", stream_output=True)
  pyb.exec_("repo.checkout()", stream_output=True)
  assert b'v1\r\n' == pyb.exec_("f = open('test_branch/test.txt','r'); print(f.read())")
  pyb.exec_("repo.checkout(ref='abranch')", stream_output=True)
  assert b'a branch\r\n' == pyb.exec_("f = open('test_branch/branch.txt','r'); print(f.read())")


def test_auth():
  pyb = init_board()
  if not os.path.isfile('test_secrets.json'):
    print('skipping test because test_secrets.json is missing')
    return
  with open('test_secrets.json') as f:
    test_secrets = json.load(f)
  pyb.enter_raw_repl()
  try:
    pyb.exec_('import ygit', stream_output=True)
    private_repo = test_secrets['github']['private_repo']
    username = test_secrets['github']['username']
    password = test_secrets['github']['password']
    ret = pyb.exec_(f"repo = ygit.clone({repr(private_repo)}, 'private_repo', username={repr(username)}, password={repr(password)})", stream_output=True)
    assert b'writing:' in ret
  finally:
    pyb.exit_raw_repl()


def test_update_auth():
  pyb = init_board()
  if not os.path.isfile('test_secrets.json'):
    print('skipping test because test_secrets.json is missing')
    return
  with open('test_secrets.json') as f:
    test_secrets = json.load(f)
  pyb.enter_raw_repl()
  try:
    pyb.exec_('import ygit', stream_output=True)
    private_repo = test_secrets['github']['private_repo']
    username = test_secrets['github']['username']
    password = test_secrets['github']['password']
    pyb.exec_("repo = ygit.Repo('private_repo')", stream_output=True)
    pyb.exec_(f"repo._init({repr(private_repo)})", stream_output=True)
    with pytest.raises(ampy.pyboard.PyboardError) as e:
      pyb.exec_("repo.fetch()", stream_output=True)
    pyb.exec_(f"repo.update_authentication({repr(username)}, {repr(password)})", stream_output=True)
    pyb.exec_(f"repo.fetch()", stream_output=True)
    assert b'writing:' in pyb.exec_(f"repo.checkout()", stream_output=True)
  finally:
    pyb.exit_raw_repl()


def test_cone_on_device():
  pyb = init_board()
  pyb.enter_raw_repl()
  pyb.exec_('import ygit', stream_output=True)
  pyb.exec_("repo = ygit.clone('https://github.com/turfptax/ugit_test.git', 'ugit_test', cone='Folder')", stream_output=True)
  pyb.exit_raw_repl()



def get_ip():
  import socket
  with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]

# this repo will fill up the flash, then OSError: 28
# ygit.clone('https://github.com/gitpython-developers/GitPython.git','GitPython', ref='f25333525425ee1497366fd300a60127aa652d79')


if __name__=='__main__':
  init_board(clear='--no-clear' not in sys.argv)
  print('maybe try (small, medium, large):')
  print("import ygit; repo = ygit.clone('https://github.com/turfptax/ugit_test.git','ugit_test')")
  print("import ygit; repo = ygit.clone('https://github.com/keredson/ygit.git','ygit_shallow')")
  print("import ygit; repo = ygit.clone('https://github.com/gitpython-developers/GitPython.git','GitPython')")
  print("import ygit; repo = ygit.clone('https://github.com/keredson/ygit.git','ygit_deep', shallow=False)")
  

