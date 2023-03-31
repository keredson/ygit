Usage
=====

.. _installation:

Installation
------------

To use ygit:

.. code-block:: console

   $ wget https://raw.githubusercontent.com/keredson/ygit/main/ygit.py
   $ mpy-cross ygit.py
   $ ampy -p /dev/ttyUSB0 put ygit.mpy

Cloning a Repository
----------------


To clone a repo, run:

.. code-block:: python

  >>> repo = ygit.clone('https://github.com/turfptax/ugit_test.git')

If you don't want to clone into the root directory of your device, pass a target directory as a second 
argument. This will produce a shallow clone (at HEAD) by default. It will not delete any files in the
target directory, but it will overwrite them if conflicting. The normal git files you'd expect 
(config, *.pack, IDX) will be in .ygit. You only need to run this once.

To update:

.. code-block:: python

  >>> repo.pull()

Which is the same as:

.. code-block:: python

  >>> repo.fetch()
  >>> repo.checkout()

These are incremental operations. It will only download git objects you don't already have, and only update files when their SHA1 values don't match.



