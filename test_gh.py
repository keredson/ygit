import os, tempfile, hashlib, subprocess

import ygit


def test_clone():
  with tempfile.TemporaryDirectory() as td:
    repo = ygit.clone('https://github.com/turfptax/ugit_test.git',td)
    assert os.path.isdir(os.path.join(td,'.ygit'))
    assert os.path.isfile(os.path.join(td,'.ygit','config'))
    assert os.path.isfile(os.path.join(td,'.ygit','idx'))
    assert os.path.isfile(os.path.join(td,'boot.py'))

    
def test_big_clone():
  with tempfile.TemporaryDirectory() as td:
    repo = ygit.clone('https://github.com/gitpython-developers/GitPython.git', td, ref='f25333525425ee1497366fd300a60127aa652d79')
    assert os.path.isfile(os.path.join(td,'.ygit','idx'))
    assert os.path.isfile(os.path.join(td,'test','performance','lib.py'))
    assert os.path.isfile(os.path.join(td,'.github','workflows','pythonpackage.yml'))
    ppfn = os.path.join(td,'.github','workflows','pythonpackage.yml')
    h = hashlib.sha1()
    with open(ppfn,'rb') as f:
      h.update(f.read())
    assert h.hexdigest() == '24cc06819e2c1d8cbf1db84e693e5e87323b2d2d'
    # repo has 184, but that includes a submodule gitdb (submodules are not supported)
    assert int(subprocess.check_output(f'find {td}/* | wc -l', shell=True).decode().strip()) == 183
    assert sorted(repo.branches()) == sorted(['Fix-#1334', 'black-fmt', 'experiment-2012', 'fix', 'fix-1103', 'fix-ci-tests', 'fix-non-ascii-chars-in-status-lines', 'issue-232-reproduction', 'issue-301-reproduction', 'main', 'master', 'more-robust-git-diff', 'no_devnull_open', 'py2', 'revert-357-autointerrupt_deadlock_fix', 'typing'])


def test_checkout_older_history_and_update():
  with tempfile.TemporaryDirectory() as td:
    repo = ygit.clone('https://github.com/turfptax/ugit_test.git',td, ref='7e5c62596935f96518a931f97ded52b6e8b01594')
    assert sorted(os.listdir(os.path.join(td,'.ygit'))) == ['1.pack', 'config', 'idx', 'refs']
    assert sorted(os.listdir(os.path.join(td))) == ['.ygit', 'ugit_boot.py']
    # 2fd2d73227f2101770fae925ecc062b6ae4590ff is unknown because we did a shallow copy
    # this will perform another fetch to backfill missing objects
    repo.checkout(ref='2fd2d73227f2101770fae925ecc062b6ae4590ff')
    assert sorted(os.listdir(os.path.join(td,'.ygit'))) == ['1.pack', '2.pack', 'config', 'idx', 'refs']
    assert sorted(os.listdir(os.path.join(td))) == ['.ygit', 'InMainDir', 'README.md', 'ugit_boot.py']
    # ditto
    repo.checkout(ref='cde9c4e1c7a178bb81ccaefb74824cc01e3638e7')
    assert sorted(os.listdir(os.path.join(td,'.ygit'))) == ['1.pack', '2.pack', '3.pack', 'config', 'idx', 'refs']
    # InMainDir and ugit_boot.py shouldn't be here, but i haven't implemented deleting files yet
    assert sorted(os.listdir(os.path.join(td))) == ['.ygit', 'Folder', 'InMainDir', 'README.md', 'boot.py', 'ugit_boot.py']
    assert sorted(repo.branches()) == ['main']
    


