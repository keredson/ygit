import os, sh, shutil, tempfile, io

import ygit

# start test http server with:
# nginx -c "$(pwd)/misc/test_nginx.conf" -e stderr


REPOS_DIR = '/tmp/ygit_test_repos'

if os.path.isdir(REPOS_DIR): shutil.rmtree(REPOS_DIR)
os.mkdir(REPOS_DIR)


def build_repo():
  d = tempfile.mkdtemp(dir=REPOS_DIR, suffix='.git', prefix='ygit_')
  if os.path.isdir(d): shutil.rmtree(d)
  os.mkdir(d)
  git = sh.git.bake(C=d)
  git.init()
  git.config('--bool', 'http.receivepack', 'true')
  git.config('--bool', 'receive.denyCurrentBranch', 'false')
  print('build_repo', d)
  return git, d


def test_clone():
  git, d = build_repo()
  with open(os.path.join(d,'test.txt'),'w') as f:
    f.write('woot!')
  git.add('test.txt')
  git.commit('test.txt', message='-')
  with tempfile.TemporaryDirectory() as td:
    ygit.clone('http://localhost:8889/'+os.path.basename(d),td)
    assert sorted(os.listdir(td)) == ['.ygit', 'test.txt']
    assert sorted([s for s in os.listdir(os.path.join(td,'.ygit')) if not s.endswith('.pack')]) == ['config', 'idx', 'refs']
    assert len([s for s in os.listdir(os.path.join(td,'.ygit')) if s.endswith('.pack')]) == 1
    with open(os.path.join(td,'test.txt')) as f:
      assert f.read()=='woot!'

    
def test_clone_empty_repo():
  git, d = build_repo()
  with tempfile.TemporaryDirectory() as td:
    ygit.clone('http://localhost:8889/'+os.path.basename(d),td)
    assert os.path.isdir(os.path.join(td,'.ygit'))
    assert os.path.isfile(os.path.join(td,'.ygit','config'))
    assert os.path.isfile(os.path.join(td,'.ygit','idx'))
    assert sorted(os.listdir(os.path.join(td,'.ygit'))) == ['config', 'idx', 'refs']

    
def test_fetch_no_update():
  git, d = build_repo()
  with open(os.path.join(d,'test.txt'),'w') as f:
    f.write('woot!')
  git.add('test.txt')
  git.commit('test.txt', message='-')
  with tempfile.TemporaryDirectory() as td:
    repo = ygit.clone('http://localhost:8889/'+os.path.basename(d),td)
    assert len([s for s in os.listdir(os.path.join(td,'.ygit')) if s.endswith('.pack')]) == 1
    repo.fetch()
    assert len([s for s in os.listdir(os.path.join(td,'.ygit')) if s.endswith('.pack')]) == 1

    
def test_fetch_after_adding_to_empty_repo():
  git, d = build_repo()
  with tempfile.TemporaryDirectory() as td:
    repo = ygit.clone('http://localhost:8889/'+os.path.basename(d),td)
    assert len([s for s in os.listdir(os.path.join(td,'.ygit')) if s.endswith('.pack')]) == 0
    with open(os.path.join(d,'test.txt'),'w') as f:
      f.write('woot!')
    git.add('test.txt')
    git.commit('test.txt', message='-')
    repo.fetch()
    assert len([s for s in os.listdir(os.path.join(td,'.ygit')) if s.endswith('.pack')]) == 1
    
    
def test_updated_file():
  git, d = build_repo()
  with open(os.path.join(d,'test.txt'),'w') as f:
    f.write('v1')
  git.add('test.txt')
  git.commit('test.txt', message='v1')
  with tempfile.TemporaryDirectory() as td:
    repo = ygit.clone('http://localhost:8889/'+os.path.basename(d),td)
    with open(os.path.join(td,'test.txt')) as f:
      assert f.read()=='v1'
    with open(os.path.join(d,'test.txt'),'w') as f:
      f.write('v2')
    git.commit('test.txt', message='v2')
    repo.pull()
    with open(os.path.join(td,'test.txt')) as f:
      assert f.read()=='v2'
    assert len([s for s in os.listdir(os.path.join(td,'.ygit')) if s.endswith('.pack')]) == 2
    
def test_status():
  git, d = build_repo()
  with open(os.path.join(d,'test.txt'),'w') as f:
    f.write('v1')
  git.add('test.txt')
  git.commit('test.txt', message='v1')
  with tempfile.TemporaryDirectory() as td:
    repo = ygit.clone('http://localhost:8889/'+os.path.basename(d),td)
    out = io.StringIO()
    repo.status(out=out)
    assert ''==out.getvalue()
    with open(os.path.join(td,'test.txt'),'w') as f:
      f.write('v2')
    out = io.StringIO()
    repo.status(out=out)
    assert 'M /test.txt\n'==out.getvalue()
    
    
def test_branch():
  git, d = build_repo()
  with open(os.path.join(d,'test.txt'),'w') as f:
    f.write('v1')
  git.add('test.txt')
  git.commit('test.txt', message='v1')
  git.checkout('-b', 'abranch')
  with open(os.path.join(d,'branch.txt'),'w') as f:
    f.write('abranch')
  git.add('branch.txt')
  git.commit('branch.txt', message='added a branch')
  git.checkout('master')
  with tempfile.TemporaryDirectory() as td:
    repo = ygit.clone('http://localhost:8889/'+os.path.basename(d),td)
    with open(os.path.join(td,'test.txt')) as f:
      assert f.read()=='v1'
    assert not os.path.isfile(os.path.join(td,'branch.txt'))
    repo.checkout(ref='abranch')
    with open(os.path.join(td,'branch.txt')) as f:
      assert f.read()=='abranch'
    


