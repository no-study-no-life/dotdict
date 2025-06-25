import copy
from typing import Iterable, Any
from .helper import to_dot_dict, from_dot_dict


class Dict(dict):
	""" 模仿Python的dict的行为, 但是支持 `.` 进行访问 """
	
	def __setattr__(self, key, value):
		""" self.key = value """
		if hasattr(self.__class__, key):
			raise AttributeError(f"`{self.__class__.__name__}` object attribute {key} is read-only")
		else:
			self[key] = value

	def __getattr__(self, key):
		""" self.key """
		if key not in self:
			raise AttributeError(f"`{self.__class__.__name__}` object has no attribute {key}")
		else:
			return self[key]

	def __delattr__(self, key):
		""" del self.key """
		if key not in self:
			raise AttributeError(f"`{self.__class__.__name__}` object has no attribute {key}")
		else:
			del self[key]

	def copy(self):
		return copy.copy(self)

	def __copy__(self):
		""" used by copy.copy """
		obj = self.__class__()
		for k, v in self.items():
			obj[k] = v
		return obj

	def deepcopy(self):
		return copy.deepcopy(self)

	def __deepcopy__(self, memo):
		""" used by copy.deepcopy """
		obj = self.__class__()
		memo[id(self)] = obj
		for k, v in self.items():
			obj[copy.deepcopy(k, memo)] = copy.deepcopy(v, memo)
		return obj

	def __or__(self, other):
		""" self | other, behavior like dict """
		if not isinstance(other, dict):
			return NotImplemented
		obj = self.copy()
		obj.update(other)
		return obj

	def __ror__(self, other):
		""" other | self, behavior like dict """
		if not isinstance(other, dict):
			return NotImplemented
		if isinstance(other, self.__class__):
			obj = other.copy()
		else:
			obj = self.__class__(other)  # maybe deepcopy
		obj.update(self)
		return obj

	def __ior__(self, other):
		""" self |= other, behavior like dict """
		self.update(other)
		return self

	def update(self, *args, **kwargs):
		other = self.__class__(*args, **kwargs)
		for k, v in other.items():
			self[k] = v


	def to_dict(self, force=True):
		""" convert self to python dict, like deepcopy """
		return from_dot_dict(self, force=force)



class DotDict(Dict):
	"""
	支持 `.` 运算符 的 dict, 参考 addict ;
	部分属性名无法通过 `.` 进行设置, 但是允许使用 `[]` 进行设置;

	1. 使用dict创建DotDict对象时, 会将其转换为DotDict对象, 因此:
		- 对于list与tuple对象, 会创建新对象 (因为其可能包含dict对象; 即使不包含dict对象, 也需要保持行为一致);
		- 对于dict对象, 会创建一个key一致的DotDict对象, value规则同上;
		>>> a = {"h": [1, 2, 3]}
		>>> b = DotDict(a)
		>>> a["h"] is b.h
		False

	2. 设置属性时, 默认将缺失值设置为新的DotDict对象;
		>>> a = DotDict()
		>>> a.b.c = "hello"
		>>> print(a.b.c)
		"hello"

	3. 设置属性操作时, 不会更改对象:
		>>> a = DotDict()
		>>> b = [1, 2, 3]
		>>> a.b = b
		>>> a.b is b
		True

	4. update支持嵌套dict的update;
		>>> a = DotDict({"h": {"k": 1}})
		>>> b = DotDict({"h": {"j": 2}})
		>>> a.update(b)
		>>> print(a)
		{"h": {"k": 1, "j": 2}}

	5. 对于copy等其他操作, 尽量与Python官方保持一致, 如:
		- __or__ / __ror__ 使用浅拷贝;
		- __ior__ 直接调用update方法;
		

	6. 新增to_dict方法, 将DotDict对象转回dict对象; 注意其细节与 从dict创建DotDict 类似:
		>>> a = DotDict()
		>>> a.b = [1, 2, 3]
		>>> b = a.to_dict()
		>>> b["b"] is a.b
		False

	"""

	def __init__(self, *args, **kwargs):
		cls = self.__class__
		if len(args) > 1:
			raise TypeError(
				f"unsupported args for {cls.__name__}: {args}"
			)
		for arg in args:
			if isinstance(arg, dict):
				# 从 dict 进行创建
				for k, v in arg.items():
					self[k] = to_dot_dict(v, cls, force=True)
			elif isinstance(arg, Iterable):
				# 从 [(k1, v1), (k2, v2), ...] 类似结构创建
				for k, v in iter(arg):
					self[k] = to_dot_dict(v, cls, force=True)
			else:
				raise TypeError(
					f"unsupported arg for {cls.__name__}: {type(arg)}"
				)

		for k, v in kwargs.items():
			self[k] = to_dot_dict(v, cls, force=True)

	def __getattr__(self, key):
		""" 使用__missing__处理attr不存在的情况, 而不是直接抛出错误 """
		return self.__getitem__(key)

	def __missing__(self, key):
		""" 处理 self[key] 不存在时的情况: 返回一个新的DotDict对象 """
		obj = self.__class__()
		super().__setitem__(key, obj)
		return obj

	def __add__(self, other):
		""" 用于支持 dot_dict[a][b][c] += k 类似操作 """
		if not self.keys():
			return other
		else:
			return NotImplemented

	def update(self, *args, **kwargs):
		""" 
		支持多层嵌套dict的update;
		"""
		other = self.__class__(*args, **kwargs)
		for k, v in other.items():
			if k not in self or not isinstance(self[k], dict) or not isinstance(v, dict):
				self[k] = v
			else:
				self[k].update(v)

