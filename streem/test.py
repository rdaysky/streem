#!/usr/bin/python

import streem

import unittest
import re

s_test_data = """
#skip                 |
===a                  | [0] None
====b                 | .[1] None
====c                 | ..[3] a
    +if(...)          | ...[4] b
     {+               | ...[4] c
      do_this         | ....[5] if(...)
      do_that         | ....[5] {
     #}-              | .....[6] do_this
     while(...)       | .....[6] do_that
     {+               | ....[5] while(...)
      {+              | ....[5] {
       some           | .....[6] {
       compound       | ......[7] some
       statement      | ......[7] compound
       #skip          | ......[7] statement
       4th            | ......[7] 4th
       5th            |
      #}-             |
      more            | .....[6] more
      statements      | .....[6] statements
      4th             | .....[6] 4th
      5th             |
     #}-              |
     5th              |
=d                    | .[1] d
=========dd           | ..[3] None
===e                  | ...[9] dd
=======f              | ..[3] e
       #skip          | ...[7] f
=======ff             | ...[7] ff
       fff            | ...[7] fff
=======ffff           | ...[7] ffff
=======fffff          |
       +ignored       |
        +ignored      |
         ignored      |
         #skip        |
       -ignored       |
=======ffffff         |
===h                  | ..[3] h
====i                 | ...[4] i
=================j++  | ....[17] j
--k================== | ....[17] k
-l                    | ....[17] l
m-                    | ....[17] m
+n (5th)              |
===o                  | ..[3] o
=================p    | ...[17] p
x+                    | ...[17] x
 <hello>+             | ....[18] <hello>
  <world>+            | .....[19] <world>
   #skip              |
   some               | ......[20] some
   text               | ......[20] text
   nodes              | ......[20] nodes
   #skip              |
   #skip              |
   4th                | ......[20] 4th
   5th                |
  #</>-               |
  <empty>+            | .....[19] <empty>
  #</>-               |
 #</>--               |
y                     | ...[17] y
z                     | ...[17] z
=top                  | .[1] top
=====with_levels:     | ..[3] None
#{+                   | ...[5] with_levels:
  null value with     | ....[6] null value with
  next_level_rel      | ....[6] next_level_rel
 #}-                  |
THE_END               | ...[5] THE_END
"""

re_line = re.compile(r"^([=]*)([+]*)([-]*)([#]?)([^#=+-]+?)([=]*)([+]*)([-]*)$")
def to_item(line):
    l, lrp, lrm, skip, v, nl, nlrp, nlrm = re_line.match(line.strip()).groups()

    return streem.Item(value=(streem.SKIP_ITEM if skip else v.strip()),
        level=(len(l) or None),
        level_rel=(len(lrp) - len(lrm) or None),
        next_level=(len(nl) or None),
        next_level_rel=(len(nlrp) - len(nlrm) or None),
    )

class TestStreem(unittest.TestCase):

    def take(self, items, n):
        """ yield next() n times, then make sure another next() raises StopIteration """
        it = iter(items)
        try:
            for i in range(n):
                yield next(it)
        except StopIteration:
            self.assertRaises(StopIteration, next, it)
            # ...and exit this generator, implicitly re-raising StopIteration
            # (note that PEP 479 prohibits doing this explicitly)

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

    def test_bad_items(self):
        self.assertRaises(TypeError, streem.Item, "some_item", level=42, level_rel=42)
        self.assertRaises(TypeError, streem.Item, "some_item", next_level=42, next_level_rel=42)
        self.assertRaises(TypeError, streem.Item, level=42)
        self.assertRaises(TypeError, streem.Item, level_rel=42)

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

        self.assertEqual(all_inodes[0], []) # reduce_of_no_children
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

