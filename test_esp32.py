import os, tempfile, zlib, io, socket, hashlib

import ampy.files
import ampy.pyboard

import ygit

from test_localhost import build_repo

pyb = None
initted = False

def init_board():
  global pyb, initted
  if not pyb:
    pyb = ampy.pyboard.Pyboard('/dev/ttyUSB0', baudrate=115200)
  board_files = ampy.files.Files(pyb)
  existing_files = board_files.ls(long_format=False)
  for fn in existing_files:
    if fn in ('/boot.py','/ygit.py',): continue
    print('removing', fn)
    try:
      board_files.rm(fn)
    except ampy.pyboard.PyboardError:
      board_files.rmdir(fn)
  if initted: return pyb
  if check_ygit_file(pyb):
    copy_ygit_file(pyb, board_files)
  initted = True
  return pyb  


def check_ygit_file(pyb):
  pyb.enter_raw_repl()
  try:
    h = hashlib.sha1()
    with open('ygit.py','rb') as f:
      h.update(f.read())
    sig = h.hexdigest()
    cmd = '''import hashlib, binascii
h = hashlib.sha1()
f = open('ygit.py','rb')
h.update(f.read())
print(binascii.hexlify(h.digest()).decode())
del h
f.close()
del f'''
    board_sig = pyb.exec_(cmd).decode().strip()
    print('ygit.py board/local sha1:', board_sig, sig)
    return board_sig != sig
  finally:
    pyb.exit_raw_repl()
  

def copy_ygit_file(pyb, board_files):
  print('copying ygit...')
  with open('ygit.py','rb') as f:
    board_files.put('ygit.py.gz', zlib.compress(f.read()))
  pyb.enter_raw_repl()
  try:
    pyb.exec_('''import zlib, os
with open('ygit.py.gz','rb') as fin:
  with open('ygit.py','wb') as fout:
    s = zlib.DecompIO(fin)
    while data:=s.read(256):
      fout.write(data)
del s, fin, fout
os.remove('ygit.py.gz')
gc.collect()
    ''', stream_output=True)
  finally:
    pyb.exit_raw_repl()


def test_gh():
  pyb = init_board()
  pyb.enter_raw_repl()
  pyb.exec_('import ygit', stream_output=True)
  pyb.exec_("ygit.init('https://github.com/turfptax/ugit_test.git','ugit_test')", stream_output=True)
  pyb.exec_("ygit.fetch('ugit_test')", stream_output=True)
  pyb.exec_("ygit.checkout('ugit_test')", stream_output=True)
  pyb.exit_raw_repl()


def test_checkout_status():
  pyb = init_board()
  pyb.enter_raw_repl()
  pyb.exec_('import ygit, io', stream_output=True)
  pyb.exec_("ygit.init('https://github.com/turfptax/ugit_test.git','ugit_test')", stream_output=True)
  pyb.exec_("ygit.fetch('ugit_test', ref='7e5c62596935f96518a931f97ded52b6e8b01594')", stream_output=True)
  pyb.exec_("ygit.checkout('ugit_test', ref='7e5c62596935f96518a931f97ded52b6e8b01594')", stream_output=True)
  pyb.exec_("ygit.fetch('ugit_test', ref='cde9c4e1c7a178bb81ccaefb74824cc01e3638e7')", stream_output=True)
  pyb.exec_('out = io.StringIO()', stream_output=True)
  pyb.exec_("ygit.status('ugit_test', ref='cde9c4e1c7a178bb81ccaefb74824cc01e3638e7', out=out)", stream_output=True)
  out = pyb.exec_('print(out.getvalue())')
  pyb.exit_raw_repl()
  assert out==b'A ugit_test/Folder\r\nA ugit_test/Folder\r\nD /README.md\r\nD /boot.py\r\nA ugit_test/Folder/SubFolder\r\nA ugit_test/Folder/SubFolder\r\nD /Folder/in_second.py\r\nD /Folder/SubFolder/third_layer.py\r\n\r\n'


def test_branch():
  pyb = init_board()
  pyb.enter_raw_repl()
  git, d = build_repo()
  with open(os.path.join(d,'test.txt'),'w') as f:
    f.write('v1')
  git.add('test.txt')
  git.commit('test.txt', message='v1')
  git.checkout('-b', 'abranch')
  with open(os.path.join(d,'branch.txt'),'w') as f:
    f.write('a branch')
  git.add('branch.txt')
  git.commit('branch.txt', message='added a branch')
  git.checkout('master')
  pyb.exec_('import ygit, io, os', stream_output=True)
  pyb.exec_(f"ygit.init('http://{get_ip()}:8889/{os.path.basename(d)}','test_branch')", stream_output=True)
  pyb.exec_("ygit.fetch('test_branch')", stream_output=True)
  pyb.exec_("ygit.checkout('test_branch')", stream_output=True)
  assert b'v1\r\n' == pyb.exec_("f = open('test_branch/test.txt','r'); print(f.read())")
  pyb.exec_("ygit.checkout('test_branch', ref='abranch')", stream_output=True)
  assert b'a branch\r\n' == pyb.exec_("f = open('test_branch/branch.txt','r'); print(f.read())")


def get_ip():
  import socket
  with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]

# this repo will fill up the flash, then OSError: 28
# ygit.clone('https://github.com/gitpython-developers/GitPython.git','GitPython', ref='f25333525425ee1497366fd300a60127aa652d79')


if __name__=='__main__':
  init_board()
  print('maybe try:')
  print("import ygit; ygit.clone('https://github.com/turfptax/ugit_test.git','ugit_test')")
  print("import ygit; ygit.clone('https://github.com/gitpython-developers/GitPython.git','GitPython')")
  

