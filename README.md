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

## Design

### Shallow Cloning
By default clones are [shallow](https://github.blog/2020-12-21-get-up-to-speed-with-partial-clone-and-shallow-clone/) to
save space.  If you try to checkout an unknown ref, `ygit` will fetch a new packfile from the original server.


### Subdirectory Cloning
Usually I don't want to clone an entire project onto my ESP32.  The python I want on the device is in a subdirectory of a larger project.  The `cone` argument will take a path, and only files in that directory will be checked out (as if it were the top level).

**TODO:** Do a blob filter to only fetch objects we intend to check out.


### Authentication
Supply a username/password to `clone()`.  The credentials will be stored on the device, AES encrypted with the machine id as the key.  For GitHub, use your [personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) as the password (just like w/ regular `git`).


## Tests
- *Prereq:* Run `nginx -c "$(pwd)/misc/test_nginx.conf" -e stderr` in the background for the local teets.
- `pytest test_localhost.py` (runs local tests) 
- `pytest test_gh.py` (runs github tests)
- `pytest test_micropython.py` (**WARNING:** will wipe all files except `boot.py` from your MicroPython device at `/dev/ttyUSB0`.)
