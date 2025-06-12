# Battleships

This is a repository for the COMP8860 group project from summer 2025. It's a battleship desktop game with multiplayer functionality.

The frontend is a Java Swing application and the backend is a Python Flask app with a small SQLite database.

# Running the game locally (unfinished)

You can run the game locally by launching it from the terminal. 

**Requirements:**
- Git
- Java
- Python

**To run the game:**
1. Start by cloning the master branch of this repository, `git clone https://github.com/HalfFull8860`
2. Enter the newly created local repository, `cd HalfFull8860`
3. If you don't have pymake installed, run `python -m pip install py-make`
4. Run `python -m pymake`. This will install the missing packages, compile the java files, start the flask app and the desktop application.
5. Open a new terminal in your code editor.
6. Run app.py using the command 'python app.py'.
7. Open a new terminal and enter the following commands in order. 'cd src', 'javac -cp "..;../lib/json-20231013.jar" BattleshipConnector.java Game.java', 'java -cp ".;../lib/json-20231013.jar" Game'.
8. If playing two player, once the first player has generated a code and opened up their game window. From a new terminal enter the following commands 'cd src', 'java -cp ".;../lib/json-20231013.jar" Game', and click 'Join Game' and then enter code received. 
