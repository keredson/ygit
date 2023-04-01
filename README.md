![header](misc/header.png)

# ygit
A tiny (yocto) git client for [MicroPython](https://micropython.org/) microcontrollers / other memory-constrained environments (<100k)
like the [$6](https://www.amazon.com/Teyleten-Robot-ESP-WROOM-32-Development-Microcontroller/dp/B08246MCL5) 
[ESP32](https://en.wikipedia.org/wiki/ESP32).  It speaks to git HTTP/HTTPS servers using the ubiquitous 
[smart client protocol](https://www.git-scm.com/docs/http-protocol#_smart_clients).  I use it to remotely deploy/update code.


## Install
```bash
$ wget https://raw.githubusercontent.com/keredson/ygit/main/ygit.py
$ mpy-cross ygit.py
$ ampy -p /dev/ttyUSB0 put ygit.mpy
```

## Get Started
To clone a repo, run:
```python
>>> repo = ygit.clone('https://github.com/turfptax/ugit_test.git')
```
If you don't want to clone into the root directory of your device, pass a target directory as a second argument.  This will produce a shallow clone (at `HEAD`) by default.  It will not delete any files in the target directory, but it will overwrite them if conflicting.  The normal git files you'd expect (`config`, `*.pack`, `IDX`) will be in `.ygit`.  You only need to run this once.

To update:
```python
>>> repo.pull()
```
Which is the same as:
```python
>>> repo.fetch()
>>> repo.checkout()
```
These are incremental operations.  It will only download git objects you don't already have, and only update files when their SHA1 values don't match.


## API

```python
# make a new clone
repo = ygit.clone(repo, directory='.', shallow=True, cone=None, 
                  quiet=False, ref='HEAD', username=None, password=None)

# control an already cloned repository
repo = ygit.Repo(directory='.')

# control
repo.checkout(ref='HEAD')
repo.pull(shallow=True, quiet=False, ref='HEAD')
repo.fetch(shallow=True, quiet=False, ref='HEAD')
repo.status(ref='HEAD')
repo.tags()
repo.branches()
repo.pulls()
repo.update_authentication(username, password)
repo.log()
```
A `ref` is one of: 
- `HEAD`
- a commit (ex: `7b36b4cb1616694d8562f3adea656a709b9831d9`)
- a branch / tag / pull

Read the [full documentation](https://ygit.readthedocs.io/en/latest/api.html).


## Design

### Shallow Cloning
By default clones are [shallow](https://github.blog/2020-12-21-get-up-to-speed-with-partial-clone-and-shallow-clone/) to
save space.  If you try to checkout an unknown ref, `ygit` will fetch a new packfile from the original server.


### Subdirectory Cloning
Usually I don't want to clone an entire project onto my ESP32.  The python I want on the device is in a subdirectory of a larger project.  The `cone` argument will take a path, and only files in that directory will be checked out (as if it were the top level).

**TODO:** Do a blob filter to only fetch objects we intend to check out.


### Authentication
Supply a username/password to `clone()`.  The credentials will be stored on the device, AES encrypted with the machine
id as the key.  For GitHub, use your [personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
as the password (just like w/ regular `git`).


## Tests
- *Prereq:* Run `nginx -c "$(pwd)/misc/test_nginx.conf" -e stderr` in the background for the local teets.
- `pytest test_localhost.py` (runs local tests) 
- `pytest test_gh.py` (runs github tests)
- `pytest test_micropython.py` (**WARNING:** will wipe all files except `boot.py` from your MicroPython device at `/dev/ttyUSB0`.)


## Example Run
```
$ picocom /dev/ttyUSB0 -b 115200

MicroPython v1.19.1 on 2022-06-18; ESP32 module with ESP32
Type "help()" for more information.

>>> import ygit
>>> repo = ygit.clone('https://github.com/keredson/ygit.git','ygit')
cloning https://github.com/keredson/ygit.git into ygit @ HEAD
fetching: https://github.com/keredson/ygit.git @ HEAD
fetching commit: bc0f8c042d06f3c78be2066af11419357d1b6e0e
Enumerating objects: 26, done.
Counting objects:   3% (1/26)
Counting objects:   7% (2/26)
Counting objects:  11% (3/26)
Counting objects:  23% (6/26)
Counting objects:  34% (9/26)
Counting objects:  38% (10/26)
Counting objects:  46% (12/26)
Counting objects:  53% (14/26)
Counting objects:  57% (15/26)
Counting objects:  65% (17/26)
Counting objects:  69% (18/26)
Counting objects:  76% (20/26)
Counting objects:  84% (22/26)
Counting objects:  92% (24/26)
Counting objects:  96% (25/26)
Counting objects: 100% (26/26)
Counting objects: 100% (26/26), done.
Compressing objects:   8% (2/24)
Compressing objects:  12% (3/24)
Compressing objects:  16% (4/24)
Compressing objects:  20% (5/24)
Compressing objects:  25% (6/24)
Compressing objects:  29% (7/24)
Compressing objects:  33% (8/24)
Compressing objects:  37% (9/24)
Compressing objects:  41% (10/24)
Compressing objects:  45% (11/24)
Compressing objects:  54% (13/24)
Compressing objects:  58% (14/24)
Compressing objects:  62% (15/24)
Compressing objects:  66% (16/24)
Compressing objects:  75% (18/24)
Compressing objects:  79% (19/24)
Compressing objects:  95% (22/24)
(23/24)
Compressing objects: 100% (24/24)
Compressing objects: 100% (24/24), done.
>>>>>>>>>>>>>>>>>>>>>>>
Total 26 (delta 0), reused 15 (delta 0), pack-reused 0
##########################
checking out bc0f8c042d06f3c78be2066af11419357d1b6e0e
writing: ygit/.gitignore (BLOB)
writing: ygit/.readthedocs.yml (BLOB)
writing: ygit/LICENSE (BLOB)
writing: ygit/README.md (BLOB)
writing: ygit/deploy.sh (BLOB)
writing: ygit/pyproject.toml (BLOB)
writing: ygit/requirements.txt (BLOB)
writing: ygit/setup.py (BLOB)
writing: ygit/test_gh.py (BLOB)
writing: ygit/test_localhost.py (BLOB)
writing: ygit/test_micropython.py (BLOB)
writing: ygit/ygit.py (BLOB)
writing: ygit/docs/Makefile (BLOB)
writing: ygit/docs/api.rst (BLOB)
writing: ygit/docs/conf.py (BLOB)
writing: ygit/docs/index.rst (BLOB)
writing: ygit/docs/make.bat (BLOB)
writing: ygit/docs/usage.rst (BLOB)
writing: ygit/docs/source/api.rst (BLOB)
writing: ygit/docs/source/conf.py (BLOB)
writing: ygit/docs/source/index.rst (BLOB)
writing: ygit/docs/source/usage.rst (BLOB)
writing: ygit/misc/header.png (BLOB)
writing: ygit/misc/header.xcf (BLOB)
writing: ygit/misc/test_nginx.conf (BLOB)
>>> 
>>> repo.pull()
fetching: https://github.com/keredson/ygit.git @ HEAD
fetching commit: bc0f8c042d06f3c78be2066af11419357d1b6e0e
up to date!

```
