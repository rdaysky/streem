#!/usr/bin/python

import streem

import unittest
import re

s_test_data = """
===a                  | [0] None
====b                 | .[1] None
====c                 | ..[3] a
    +if(...)          | ...[4] b
     {+               | ...[4] c
      do_this         | ....[5] if(...)
      do_that         | ....[5] {
     -#}              | .....[6] do_this
     while(...)       | .....[6] do_that
     {+               | ....[5] while(...)
      {+              | ....[5] {
       some           | .....[6] {
       compound       | ......[7] some
       statement      | ......[7] compound
       4th            | ......[7] statement
       5th            | ......[7] 4th
      -#}             | .....[6] more
      more            | .....[6] statements
      statements      | .....[6] 4th
      4th             |
      5th             |
     -#}              |
     5th              |
=d                    | .[1] d
=========dd           | ..[3] None
===e                  | ...[9] dd
=======f              | ..[3] e
=======ff             | ...[7] f
=======fff            | ...[7] ff
=======ffff           | ...[7] fff
=======fffff          | ...[7] ffff
       +ignored       |
        +ignored      |
         ignored      |
       -ignored       |
=======ffffff         |
===h                  | ..[3] h
====i                 | ...[4] i
=================j++  | ....[17] j
--k================== | ....[17] k
-l                    | ....[17] l
m-                    | ....[17] m
+n (5th)              | ..[3] o
===o                  | ...[17] p
=================p    | ...[17] x
x+                    | ....[18] <hello>
 <hello>+             | .....[19] <world>
  <world>+            | ......[20] some
   some               | ......[20] text
   text               | ......[20] nodes
   nodes              | ......[20] 4th
   4th                | .....[19] <empty>
   5th                | ...[17] y
  -#</>               | ...[17] z
  <empty>+            |
  -#</>               |
 -#</>-               |
y                     |
z                     |
=top                  | .[1] top
=====with_levels:     | ..[3] None
#{+                   | ...[5] with_levels:
  null value with     | ....[6] null value with
  next_level_rel      | ....[6] next_level_rel
 -#}                  | 
THE_END               | ...[5] THE_END
"""

re_line = re.compile(r"^([=]*)([+]*)([-]*)([#]?)([^#=+-]+?)([=]*)([+]*)([-]*)$")
def to_item(line):
    l, lrp, lrm, exclude, v, nl, nlrp, nlrm = re_line.match(line.strip()).groups()

    return streem.Item(value=(None if exclude else v.strip()),
        level=(len(l) or None),
        level_rel=(len(lrp) - len(lrm) or None),
        next_level=(len(nl) or None),
        next_level_rel=(len(nlrp) - len(nlrm) or None),
    )

class TestStreem(unittest.TestCase):

    def take(self, items, n):
        it = iter(items)
        try:
            for i in range(n):
                yield next(it)
        except StopIteration:
            self.assertRaises(StopIteration, next, it)
            raise StopIteration()

    def setUp(self):
        self.items = [to_item(line.partition("|")[0]) for line in s_test_data.strip().splitlines()]

    def test_result(self):
        nodes = streem.streem(
            self.items,
            map=None,
            reduce=lambda nodes: list(self.take(nodes, 4)),
            mandatory_levels=[0, 1, 3],
        )

        self.assertEqual(
            "\n".join(n.as_text() for n in nodes),
            "\n".join(x for x in (line.partition("|")[2].strip() for line in s_test_data.strip().splitlines()) if x).rstrip("\n"),
        )

    def test_level_enforcement(self):
        self.assertRaises(streem.ItemError, streem.streem,
            self.items,
            mandatory_levels=[0, 1],
        )

    def test_iterator_locking(self):
        all_inodes = []
        def reduce_storing_iterators(inodes):
            all_inodes.append(inodes)
            return inodes

        nodes = list(streem.streem(
            self.items,
            map=None,
            reduce=reduce_storing_iterators,
            mandatory_levels=[0, 1, 3],
        ))

        self.assertEqual(all_inodes[0], [])
        self.assertRaises(StopIteration, next, all_inodes[1])
        for it in all_inodes[2:]:
            if isinstance(it, list):
                self.assertEqual(it, [])
            else:
                self.assertRaises(streem.LogicError, next, it)

    def test_empty(self):
        self.assertEqual(streem.streem([]), [])

if __name__ == "__main__":
    unittest.main()

