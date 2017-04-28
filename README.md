# Introduction

The **streem** module turns streams into trees. With it, hierarchical data stored as a sequence of values alongside their nesting levels can be transformed back into its tree form.

The module is iterator-based and does not build the whole tree in memory unless requested.

# Description

## Source data items

To use, first build a sequence of **streem.Item** objects from source data:

streem.**Item**([*value*=SKIP_ITEM, [*level* | *level_rel*]], [*next_level* | *next_level_rel*])

#### Parameters

* **value** — The value associated with the given item. If absent, no node will be output, but the next_level parameters will still be taken into account, possibly affecting subsequent items.
* **level** — The nesting level of the item, an integer.
* **level_rel** — The level relative to the default level (taken from the previous item), an integer.
* **next_level** — The default nesting level of the next item, an integer.
* **next_level_rel** — The next level relative to the level of this item, an integer.

If *level* is supplied, that’s the exact nesting level of the item. Items with higher levels result in nodes that are children of the most recent node with a lower level. If *level_rel* is supplied instead, the level is calculated as *default level* (see below) + *level_rel*. If none are supplied, *level_rel* = 0 is assumed. Both can’t be supplied at the same time.

The next_level parameters can be provided to affect the *default level* of the following item, which would otherwise be equal to the calculated level of the current item. While *next_level* sets it directly, *next_level_rel* is added to level of the current item. Both parameters can’t be supplied at the same time.

When no *value* is given, *level[_rel]* can’t be given either. Use *next_level[_rel]* to affect subsequent items. An *Item* without any parameters at all has no effect as though it weren't present in the sequence.

#### Examples

Source entries | Possible corresponding items
-------------- | ----------------------------
&lt;h1&gt;xyzzy&lt;/h1&gt;<br>&lt;h2&gt;plugh&lt;/h2&gt;<br>&lt;p&gt;text&lt;/p&gt; | *Item*(*value*="xyzzy", *level*=1)<br>*Item*(*value*="plugh", *level*=2)<br>*Item*(*value*="text", *level*=999)
&lt;outer&gt;<br>text node<br>&lt;inner&gt;<br>more text<br>&lt;/inner&gt;<br>&lt;/outer&gt; | *Item*(*value*=Element("outer"), *next_level_rel*=+1)<br>*Item*(*value*=TextNode("text node"))<br>*Item*(*value*=Element("inner"), *next_level_rel*=+1)<br>*Item*(*value*=TextNode("more text"))<br>*Item*(*next_level_rel*=-1)<br>*Item*(*next_level_rel*=-1)<br>


## The conversion

To create a tree of nodes from the items and pass the nodes to callbacks, call the **streem.streem** function:

streem.**streem**(*items*, *map*=SIMPLE_MAP, *reduce*=None, *starting_level*=0, *mandatory_levels*=[], *mandatory_levels_all*=False)

#### Parameters

* **items** — A sequence of *streem.Item* objects.
* **map**(*Node*) — callback over nodes returning any type *X*.
* **reduce**(sequence of *X*) — callback over sequences of nodes of the same level returning any type (goes into *Node.children*). Must be reentrant.
* **starting_level** — The default level of the first item.
* **mandatory_levels** — A sequence of integer levels at which nodes with values of *None* are to be inserted if the source data skips over those levels.
* **mandatory_levels_all** — Whether to behave as though all possible levels were present in *mandatory_levels*.

#### Return value
The return value of the outermost *reduce* call. See below.

#### Exceptions

* streem.**ItemError** — An error with construction of the *items* sequence, such as mismatched levels.
* streem.**LogicError** — Failure to follow prescribed usage of the function, such as using iterators provided to callbacks past their expiration point.

#### Callback invocation

The callbacks work with **streem.Node** objects that have three attributes:

* **level** — The calculated level of the corresponding item.
* **value** — The value of the corresponding item, or *None* if this node was inserted due to *mandatory_levels* requirements.
* **children** — The result of *reduce* call on the sequence of child nodes (after *map* calls).

Firstly, an iterator over top-level nodes is created and passed as argument to *reduce*. That iterator yields values that are the results of *map*(*Node*) calls. If a node has no child nodes, its *children* attribute is set to *reduce*(empty sequence), which is evaluated once at *streem* invocation. If child nodes are present, another iterator that yields values from that level is created and passed to another *reduce* call, and so on recursively, the results of *reduce* calls being saved as the *children* attribute of the parent *Node*.

The *reduce* callback can exit early after consuming only part of nodes provided by the iterator. In that case, items corresponding to nodes not consumed will be consumed from the source stream but not passed to any callbacks.

The example at the end of this page corresponds to the following expression in terms of callbacks:

```python
reduce([
    map(Node(1, "Tree (data structure)", reduce([
        map(Node(2, "Definition", NC)),
        map(Node(2, "Terminologies used in Trees", reduce([
            map(Node(3, "Data type vs. data structure", NC)),
            map(Node(3, "Recursive", NC)),
            map(Node(3, "Type theory", NC)),
            map(Node(3, "Mathematical", NC)),
        ]))),
        map(Node(2, "Terminology", NC)),
    ]))),
])
```

where *NC* = *reduce*(empty sequence).

#### Iterator expiration

The iterator passed to *reduce* must have its values consumed prior to the *reduce* callback exiting, and *reduce* can’t access the data through any other iterators, including ones passed to other *reduce* calls. Storing the iterator and attempting to extract values from it later is not permitted and will raise *streem.LogicError*. In particular, *reduce* can’t return a generator or another lazy object that hasn’t yet consumed data from the iterator. This is because the underlying iterator over *items* will have advanced to following items and the items required for constructing the nodes will no longer be available.

#### Default callbacks

The default *map* and *reduce* callbacks are such that the return value of *streem* is a list of simple Python objects. Each node is represented by (*value*, list of children) tuple or simply *value* for childless nodes. If an entry exists in *mandatory_levels* that is greater than the level of a node, its children are listed even if there are none, ensuring the (*value*, possibly empty list of children) tuple form. This is independent of the value of the *mandatory_levels_all* parameter.

Set *map* = *None* explicitly to get *Node* objects without any mapping, that is, identically to *map* = lambda *n*: *n*.

Using the default *reduce* callback is equivalent to setting *reduce* = list.

#### Mandatory levels

Mandatory levels are useful in case of missing hierarchy levels. For example, when parsing a configuration file similar to the following:

    foo=bar
    xyzzy=plugh

    [section]
    something-inside-section=some-value

assigning level 1 to group header lines and level 2 to lines with settings will raise *streem.ItemError* because there’s no level 1 parent for the top lines. Setting *mandatory_levels* = [1] will attach those entries to a *Node*(*level*=1, *value*=*None*), ensuring a consistent structure of the resulting tree.

# Example

A table of contents of a Markdown document can be generated like this (simplified):

```python
import streem
import pprint

src = """
# Tree (data structure)
In computer science, a tree is...

## Definition
A tree is a (possibly non-linear) data structure made up of nodes or vertices and edges without having any cycle. ...

## Terminologies used in Trees
Root – The top node in a tree. ...

### Data type vs. data structure
There is a distinction between a tree as an abstract data type and as a data structure, analogous to the distinction between a list and a linked list.
As a data type, ...

### Recursive
Recursively, as a data type a tree is defined as...

### Type theory
...

### Mathematical
...

## Terminology
...
"""

items = [streem.Item(
    value=line.lstrip("#").strip(),
    level=sum(1 for ch in line if ch == "#"),
) for line in src.splitlines() if line.startswith("#")]

pprint.pprint(streem.streem(items))
```

Result:

```python
[('Tree (data structure)',
  ['Definition',
   ('Terminologies used in Trees',
    ['Data type vs. data structure',
     'Recursive',
     'Type theory',
     'Mathematical']),
   'Terminology'])]
```
