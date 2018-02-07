sync:
	rsync -av dev@120.76.233.55:csv/*.csv ./csv/
notebook:
	jupyter notebook
