import os, tempfile, zlib, io

import ampy.files
import ampy.pyboard

import ygit

from test_localhost import build_repo

pyb = None

def init_board():
  global pyb
  if pyb: return pyb
  print('clearing esp32...')
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
  print('copying ygit...')
  with open('ygit.py','rb') as f:
    board_files.put('ygit.py.gz', zlib.compress(f.read()))
  pyb.enter_raw_repl()
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
  pyb.exit_raw_repl()
  return pyb  


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
  pyb.exec_("ygit.fetch('ugit_test', commit='7e5c62596935f96518a931f97ded52b6e8b01594')", stream_output=True)
  pyb.exec_("ygit.checkout('ugit_test', commit='7e5c62596935f96518a931f97ded52b6e8b01594')", stream_output=True)
  pyb.exec_("ygit.fetch('ugit_test', commit='cde9c4e1c7a178bb81ccaefb74824cc01e3638e7')", stream_output=True)
  pyb.exec_('out = io.StringIO()', stream_output=True)
  pyb.exec_("ygit.status('ugit_test', commit='cde9c4e1c7a178bb81ccaefb74824cc01e3638e7', out=out)", stream_output=True)
  out = pyb.exec_('print(out.getvalue())')
  pyb.exit_raw_repl()
  assert out==b'A ugit_test/Folder\r\nA ugit_test/Folder\r\nD /README.md\r\nD /boot.py\r\nA ugit_test/Folder/SubFolder\r\nA ugit_test/Folder/SubFolder\r\nD /Folder/in_second.py\r\nD /Folder/SubFolder/third_layer.py\r\n\r\n'



# this repo will fill up the flash, then OSError: 28
# ygit.clone('https://github.com/gitpython-developers/GitPython.git','GitPython', commit='f25333525425ee1497366fd300a60127aa652d79')


if __name__=='__main__':
  init_board()
  print('maybe try:')
  print("import ygit; ygit.clone('https://github.com/turfptax/ugit_test.git','ugit_test')")
  print("import ygit; ygit.clone('https://github.com/gitpython-developers/GitPython.git','GitPython')")
  

