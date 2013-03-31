run:
	. env/bin/activate && ./run.py
	
kill:
	. env/bin/activate && ./kill-database.py

init:
	. env/bin/activate && ./init-database.py
