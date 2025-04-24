# studi-bars

Dockerfile/compose von https://github.com/testdrivenio/django-on-docker/

# Local Development 

I recommend [PyCharm **Professional**](https://www.jetbrains.com/pycharm/download/) (Not the Community Edition. That edition can not auto complete django models etc.). The Professional Edition [is free for students](https://www.jetbrains.com/shop/eform/students).

1. Create a virtual environment: `python -m venv venv`
2. Activate the venv: `source venv/bin/activate` (done automatically in the PyCharm Terminal)
3. Install dependencies: `pip install -r requirements.txt`
4. Migrate Database: `python3 manage.py migrate`
5. Create initial Superuser: `python3 manage.py createsuperuser`
6. Run dev server: `python3 manage.py runserver`
