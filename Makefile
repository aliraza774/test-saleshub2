.PHONY: migrations migrate run format

BACKEND := backend
SRC := src

migrations:
	cd $(BACKEND) && python manage.py makemigrations

migrate:
	cd $(BACKEND) && python manage.py migrate

run:
	cd $(BACKEND) && python manage.py runserver 9000

