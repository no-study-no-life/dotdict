"""
一些用到的辅助函数;
"""


def to_dot_dict(value, type_, force=False):
	""" 
	尝试从value创建type_类型(dot_dict)的对象
	Args:
		value: 待转换对象;
		type_: 需要转换至的类型;
		force: 遇到type_类型的对象时, 是否也创建新实例转换;
	Return:
		转换完成的value; 非dict及子类不会发生转换; list与tuple会创建新对象; 
	"""
	if isinstance(value, dict):
		if not force and isinstance(value, type_):
			return value
		return type_(value)
	elif isinstance(value, (list, tuple)):
		# important: namedtuple不支持从迭代器创建实例;
		return type(value)(
			*(to_dot_dict(elem, type_, force) for elem in value)
		)
	else:
		return value


def from_dot_dict(value, force=False):
	"""
	尝试将value对象转换回dict对象;
	Args:
		value: 待转换对象
		force: 遇到python dict时, 是否也创建新实例转换
	Return:
		转换完成的value; 非dict及子类不会发生转换; list与tuple会创建新对象;
	"""
	if isinstance(value, dict):
		if not force and type(value) is dict:
			return value
		return {k: from_dot_dict(v, force) for k, v in value.items()}
	elif isinstance(value, (list, tuple)):
		# important: namedtuple不支持从迭代器创建实例;
		return type(value)(
			*(from_dot_dict(elem, force) for elem in value)
		)
	else:
		return value
