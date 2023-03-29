![header](misc/header.png)

# ygit
A tiny (yocto) git client for MicroPython.

## Install
```bash
$ ampy -p /dev/ttyUSB0 put ygit.py
```

## Get Started
To clone a repo, run:
```python
>>> ygit.clone('https://github.com/turfptax/ugit_test.git','.')
```
The second argument is the target directory (usually `'.'`).  This will produce a shallow clone (at `HEAD`) by default.  It will not delete any files in the target directory, but it will overwrite them if conflicting.  The normal git files you'd expect (`config`, `*.pack`, `IDX`) will be in `.ygit`.  You only need to run this once.

To update:
```python
>>> ygit.pull('.')
```
Which is the same as:
```python
>>> ygit.fetch('.')
>>> ygit.checkout('.')
```
These are incremental operations.  It will only download git objects you don't already have, and only update files when their SHA1 values don't match.

## API
```python
ygit.init(repo, directory, cone=None)
ygit.clone(repo, directory, shallow=True, cone=None, quiet=False, ref='HEAD')
ygit.checkout(directory, ref='HEAD')
ygit.pull(directory, shallow=True, quiet=False, ref='HEAD')
ygit.fetch(directory, shallow=True, quiet=False, ref='HEAD')
ygit.status(directory, ref='HEAD')
```
A `ref` is one of: 
- `HEAD`
- a commit id (40 character hex string)
- a branch name
- a tag

### Shallow Cloning
By default clones are [shallow](https://github.blog/2020-12-21-get-up-to-speed-with-partial-clone-and-shallow-clone/) to
save space.  If you try to checkout an unknown ref, `ygit` will fetch a new packfile from the original server.


### Subdirectory Cloning
Usually I don't want to clone an entire project onto my ESP32.  The python I want on the device is in a subdirectory of a larger project.  The `cone` argument will take a path, and only files in that directory will be checked out (as if it were the top level).

## Design
This is a partial `git` client implemented in pure python, targeting MicroPython.   It speaks to HTTP servers using the [smart client protocol](https://www.git-scm.com/docs/http-protocol).

## Related
This was inspired by [ugit](https://github.com/turfptax/ugit), which didn't work for my use case.  (Talking to a non-github server, checking out only a subdirectory, and supporting incremental updates.)

## Roadmap
- HTTP authentication for non-public projects.
- `cone` is currently unfinished.

## Tests
- `pytest test_localhost.py` (run `nginx -c "$(pwd)/test_nginx.conf" -e stderr` in the background)
- `pytest test_gh.py` (runs tests against github)
- `pytest test_esp32.py` (**WARNING:** will wipe all files except `boot.py` from your device.)
