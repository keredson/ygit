set -x
set -e
python setup.py sdist
twine upload "dist/$(ls -1v dist/ | tail -n 1)"
