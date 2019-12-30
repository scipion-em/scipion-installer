rm -rf dist/*    # To clean the already uploaded modules
python setup.py sdist
twine upload dist/*