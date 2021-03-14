import multiprocessing

workers = 1
bind = 'unix:flaskrest.sock'
umask = 0o007
reload = True

# logging
accesslog = '-'
errorlog = '-'
