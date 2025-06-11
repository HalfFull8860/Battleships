run:
	javac -d bin src/*.java
	python -m pip install flask_cors
	python -m pip install flask
	python Makefile.py
