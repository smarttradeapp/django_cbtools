find . -name "*.pyc" -exec rm -rf {} \;
find . -name ".DS_Store" -exec rm -rf {} \;

rm -rf dist django_cbtools.egg-info

# python setup.py sdist
# python setup.py register

python setup.py sdist upload
