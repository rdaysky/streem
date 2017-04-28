# File encoding: UTF-8

from more_itertools import peekable

__all__ = ["LogicError", "ItemError", "SIMPLE_MAP", "SKIP_ITEM", "Item", "Node", "streem"]

class LogicError(RuntimeError):
    pass

class ItemError(RuntimeError):
    def __init__(self, what, item_value, item_level):
        super(ItemError, self).__init__(what, item_value, item_level)

    @property
    def item_value(self):
        return self.args[1]

    @property
    def item_level(self):
        return self.args[1]

SKIP_ITEM = object()

SIMPLE_MAP = object()
_REDUCE_DEFAULT = list

class Item(object):
    __slots__ = ["value", "level", "level_rel", "next_level", "next_level_rel"]

    def __init__(self, value=SKIP_ITEM, level=None, level_rel=None, next_level=None, next_level_rel=None):
        self.value = value

        if value is SKIP_ITEM and (level is not None or level_rel is not None):
            raise TypeError("level[_rel] can't be present without a value (use next_level[_rel] instead)")

        if level is not None and level_rel is not None:
            raise TypeError("level and level_rel can't both be present")

        if next_level is not None and next_level_rel is not None:
            raise TypeError("next_level and next_level_rel can't both be present")

        self.level = level
        self.level_rel = level_rel

        self.next_level = next_level
        self.next_level_rel = next_level_rel

    def get(self, current_level):
        item_level      = self.level      if self.level      is not None else current_level + (self.level_rel or 0)
        next_item_level = self.next_level if self.next_level is not None else item_level    + (self.next_level_rel or 0)
        return self.value, item_level, next_item_level

    def __repr__(self):
        return "Item({})".format(
            ", ".join(x for x in [repr(self.value) if self.value is not SKIP_ITEM else ""] + [
            ("{}={:+d}" if k.endswith("R") else "{}={}").format(k, v) for k, v in [
                ("L",   self.level),
                ("LR",  self.level_rel),
                ("NL",  self.next_level),
                ("NLR", self.next_level_rel),
            ] if v is not None] if x)
        )

class Node(object):
    __slots__ = ["level", "value", "children"]

    def __init__(self, level, value, children):
        self.level = level
        self.value = value
        self.children = list(children) if isinstance(children, NodeIterator) else children

    def __repr__(self):
        return "Node({!r}, {!r}, {!r})".format(self.level, self.value, self.children)

    def as_text(self, indent=".", _nest_level=0):
        return "{}[{}] {}{}".format(str(indent) * _nest_level, self.level, self.value,
            "".join("\n" + c.as_text(indent, _nest_level + 1) for c in self.children))

def with_levels(items, starting_level, mandatory_levels, mandatory_levels_all):
    level = starting_level
    last_level = starting_level - 1

    for item in items:
        item_value, item_level, level = item.get(level)

        if item_value is SKIP_ITEM:
            continue

        if mandatory_levels_all:
            for l in range(last_level + 1, item_level):
                yield None, l
        else:
            for l in mandatory_levels: # must be sorted
                if last_level < l < item_level:
                    yield None, l

        yield item_value, item_level
        last_level = item_level

class SourceData(object):
    __slots__ = ["mandatory_levels_max", "iter", "f_map", "f_reduce", "reduce_of_no_children", "ni_active"]

    def __init__(self, items, f_map, f_reduce, starting_level, mandatory_levels, mandatory_levels_all):
        self.mandatory_levels_max = max(mandatory_levels) if mandatory_levels else None
        self.iter = peekable(with_levels(items, starting_level=starting_level,
            mandatory_levels=(sorted(mandatory_levels) if not mandatory_levels_all else None),
            mandatory_levels_all=mandatory_levels_all,
        ))
        self.f_map = self.simple_struct_from_node if f_map is SIMPLE_MAP else (lambda x: x) if f_map is None else f_map
        self.f_reduce = f_reduce or _REDUCE_DEFAULT

        self.reduce_of_no_children = self.f_reduce([])

        self.ni_active = None

    def simple_struct_from_node(self, n):
        return (n.value, n.children) if n.children or (self.mandatory_levels_max is not None
            and n.level < self.mandatory_levels_max) else n.value

class NodeIterator(object):
    __slots__ = ["src", "level", "parent"]

    def __init__(self, src, parent=None):
        self.src = src
        self.level = self.src.iter.peek(default=(None, None))[1]
        self.parent = parent

        self.src.ni_active = self

    def __iter__(self):
        return self

    def advance(self, consume_only=False):
        if self.src.ni_active is not self:
            raise LogicError("iterator expired")

        item_value, item_level = self.src.iter.peek()
        assert item_level <= self.level
        if item_level < self.level:
            if self.parent is None or item_level > self.parent.level:
                raise ItemError("unexpected level {} (current {}, parent {})".format(
                    item_level, self.level, self.parent.level if self.parent else None), item_value, item_level)
            raise StopIteration()

        next(self.src.iter)

        if self.src.iter.peek(default=(None, self.level))[1] <= self.level:
            if consume_only:
                return

            return self.src.f_map(Node(item_level, item_value, self.src.reduce_of_no_children))

        ni_children = NodeIterator(self.src, self)
        result = None if consume_only else self.src.f_map(Node(item_level, item_value, self.src.f_reduce(ni_children)))
        try:
            while True:
                ni_children.advance(consume_only=True)
        except StopIteration:
            self.src.ni_active = self
            return result

    def __next__(self):
        return self.advance()
    next = __next__

def streem(items, map=SIMPLE_MAP, reduce=None, starting_level=0, mandatory_levels=[], mandatory_levels_all=False):
    return (reduce or _REDUCE_DEFAULT)(NodeIterator(
        SourceData(items, map, reduce, starting_level, mandatory_levels, mandatory_levels_all)))

