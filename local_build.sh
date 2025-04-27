rm -rf "./dist"
pip install build
python -m build
pip install ./dist/django_firefly_tasks-*.whl --force-reinstall
