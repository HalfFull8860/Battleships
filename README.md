# Battleships

This repository contains the full codebase for a client-server Battleship game, developed as a project for COMP8860 in Summer 2025, by team HalfFull8860. The application features a robust Python backend and an interactive Java desktop frontend, allowing for multiple game modes.

The frontend is a Java Swing application and the backend is a Python Flask app with a small SQLite database.

Technology Stack
Backend: Python with the Flask web framework.

Frontend: Java with the Swing GUI toolkit.

API: Custom RESTful API using JSON for communication.

Storage: Game sessions are stored in-memory on the server (they do not persist if the server restarts).

# Running the game locally (unfinished)

You can run the game locally by launching it from the terminal. 

**Requirements:**
- Git
- Java
- Python

Setup and Prerequisites
Before running the game, ensure you have the following installed:
Git
Python 3.x
Java Development Kit (JDK) 8 or newer
You will also need the org.json library for the Java frontend.

1. Start by cloning the master branch of this repository, `git clone https://github.com/HalfFull8860`
2. Enter the newly created local repository, `cd HalfFull8860`
3. If you don't have pymake installed, run `python -m pip install py-make`
4. Run `python -m pymake`. This will install the missing packages, compile the java files, start the flask app and the desktop application.
5. Open a new terminal in your code editor.
6. Run app.py using the command 'python app.py'.
7. Open another new terminal and enter the following commands in order.
   'cd src'
   
   'javac -cp "..;../lib/json-20231013.jar" BattleshipConnector.java Game.java'
   
   'java -cp ".;../lib/json-20231013.jar" Game'
   
9. Follow the instructions on the UI of the game.
10. If playing two player, once the first player has generated a code and opened up their game window. From a new terminal enter the following commands 'cd src', 'java -cp ".;../lib/json-20231013.jar" Game', and click 'Join Game' and then enter the code received from the player who set up the game. 
