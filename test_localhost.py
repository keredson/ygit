import os, sh, shutil, tempfile

import ygit

# start test http server with:
# nginx -c "$(pwd)/test_nginx.conf" -e stderr


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
    assert sorted([s for s in os.listdir(os.path.join(td,'.ygit')) if not s.endswith('.pack')]) == ['config', 'idx']
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
    assert sorted(os.listdir(os.path.join(td,'.ygit'))) == ['config', 'idx']

    
def test_fetch_no_update():
  git, d = build_repo()
  with open(os.path.join(d,'test.txt'),'w') as f:
    f.write('woot!')
  git.add('test.txt')
  git.commit('test.txt', message='-')
  with tempfile.TemporaryDirectory() as td:
    ygit.clone('http://localhost:8889/'+os.path.basename(d),td)
    assert len([s for s in os.listdir(os.path.join(td,'.ygit')) if s.endswith('.pack')]) == 1
    ygit.fetch(td)
    assert len([s for s in os.listdir(os.path.join(td,'.ygit')) if s.endswith('.pack')]) == 1

    
def test_fetch_after_adding_to_empty_repo():
  git, d = build_repo()
  with tempfile.TemporaryDirectory() as td:
    ygit.clone('http://localhost:8889/'+os.path.basename(d),td)
    assert len([s for s in os.listdir(os.path.join(td,'.ygit')) if s.endswith('.pack')]) == 0
    with open(os.path.join(d,'test.txt'),'w') as f:
      f.write('woot!')
    git.add('test.txt')
    git.commit('test.txt', message='-')
    ygit.fetch(td)
    assert len([s for s in os.listdir(os.path.join(td,'.ygit')) if s.endswith('.pack')]) == 1
    
    
def test_updated_file():
  git, d = build_repo()
  with open(os.path.join(d,'test.txt'),'w') as f:
    f.write('v1')
  git.add('test.txt')
  git.commit('test.txt', message='v1')
  with tempfile.TemporaryDirectory() as td:
    ygit.clone('http://localhost:8889/'+os.path.basename(d),td)
    with open(os.path.join(td,'test.txt')) as f:
      assert f.read()=='v1'
    with open(os.path.join(d,'test.txt'),'w') as f:
      f.write('v2')
    git.commit('test.txt', message='v2')
    ygit.pull(td)
    with open(os.path.join(td,'test.txt')) as f:
      assert f.read()=='v2'
    assert len([s for s in os.listdir(os.path.join(td,'.ygit')) if s.endswith('.pack')]) == 2
    

