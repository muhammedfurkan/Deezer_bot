class AttrDict(dict):
	""" Nested Attribute Dictionary

	A class to convert a nested Dictionary into an object with key-values
	accessibly using attribute notation (AttrDict.attribute) in addition to
	key notation (Dict["key"]). This class recursively sets Dicts to objects,
	allowing you to recurse down nested dicts (like: AttrDict.attr.attr)
	"""

	def __init__(self, mapping):
		super(AttrDict, self).__init__()
		try:
			for key, value in mapping.items():
				self.__setitem__(key, value)
		except AttributeError as exc:
			raise ValueError(mapping) from exc

	def __setitem__(self, key, value):
		if isinstance(value, dict):
			value = AttrDict(value)
		super(AttrDict, self).__setitem__(key, value)

	def __getattr__(self, item):
		try:
			if isinstance(self.__getitem__(item), list):
				return [self.__class__(x) for x in self.__getitem__(item)]
			return self.__getitem__(item)
		except KeyError:
			return None

	__setattr__ = __setitem__
