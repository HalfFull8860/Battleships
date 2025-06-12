run:
	python -m pip install flask_cors
	python -m pip install flask
	javac -cp ".;lib/json-20231013.jar" -d bin src/*.java
	python Makefile.py
