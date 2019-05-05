class Var:
    __slots__ = [
		'conn', 'db', 'spot', 'downloading',
		'session', 'CSRFToken', 'loop']


var = Var()
