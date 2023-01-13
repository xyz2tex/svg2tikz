# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 Martin Owens <doctormo@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc.,Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
"""
When elements are selected, these structures provide an advanced API.
"""

from collections import OrderedDict

class ElementList(OrderedDict):
    """
    A list of elements, selected by id, iterator or xpath

    This may look like a dictionary, but it is really a list of elements.
    The default iterator is the element objects themselves (not keys) and it is
    possible to key elements by their numerical index.

    It is also possible to look up items by their id and the element object itself.
    """
    def __init__(self, svg, _iter=None):
        self.svg = svg
        self.ids = OrderedDict()
        super().__init__()
        if _iter:
            self.set(*list(_iter))

    def __iter__(self):
        return self.values().__iter__()

    def __getitem__(self, key):
        return super().__getitem__(self._to_key(key))

    def __contains__(self, key):
        return super().__contains__(self._to_key(key))

    def __setitem__(self, orig_key, elem):
        from ._base import BaseElement
        if orig_key != elem and orig_key != elem.get('id'):
            raise ValueError(f"Refusing to set bad key in ElementList {orig_key}")
        if isinstance(elem, str):
            key = elem
            elem = self.svg.getElementById(elem)
            if elem is None:
                return
        if isinstance(elem, BaseElement):
            # Selection is a list of elements to select
            key = elem.xml_path
            element_id = elem.get('id')
            if element_id is not None:
                self.ids[element_id] = key
            super().__setitem__(key, elem)
        else:
            kind = type(elem).__name__
            raise ValueError(f"Unknown element type: {kind}")

    def _to_key(self, key, default=None):
        """Takes a key (id, element, etc) and returns an xml_path key"""
        from ._base import BaseElement
        if self and key is None:
            key = default
        if isinstance(key, int):
            return list(self.keys())[key]
        elif isinstance(key, BaseElement):
            return key.xml_path
        elif isinstance(key, str) and key[0] != '/':
            return self.ids.get(key, key)
        return key

    def clear(self):
        """Also clear ids"""
        self.ids.clear()
        super().clear()

    def set(self, *ids):
        """
        Sets the currently selected elements to these ids, any existing
        selection is cleared.

        Arguments a list of element ids, element objects or
            a single xpath expression starting with "//".

        All element objects must have an id to be correctly set.

        >>> selection.set("rect123", "path456", "text789")
        >>> selection.set(elem1, elem2, elem3)
        >>> selection.set("//rect")
        """
        self.clear()
        self.add(*ids)

    def pop(self, key=None):
        """Remove the key item or remove the last item selected"""
        item = super().pop(self._to_key(key, default=-1))
        self.ids.pop(item.get('id'))
        return item

    def add(self, *ids):
        """Like set() but does not clear first"""
        # Allow selecting of xpath elements directly
        if len(ids) == 1 and isinstance(ids[0], str) and ids[0].startswith('//'):
            ids = self.svg.xpath(ids[0])

        for elem in ids:
            self[elem] = elem # This doesn't matter

    def paint_order(self):
        """Get the selected elements, but ordered by their appearance in the document"""
        new_list = ElementList(self.svg)
        new_list.set(*[elem for _, elem in sorted(self.items(), key=lambda x: x[0])])
        return new_list

    def filter(self, *types):
        """Filter selected elements of the given type, returns a new SelectedElements object"""
        return ElementList(self.svg, [e for e in self if not types or isinstance(e, types)])

    def get(self, *types):
        """Like filter, but will enter each element searching for any child of the given types"""
        def _recurse(elem):
            if not types or isinstance(elem, types):
                yield elem
            for child in elem:
                yield from _recurse(child)
        return ElementList(self.svg, [r for e in self for r in _recurse(e)])

    def id_dict(self):
        """For compatibility, return regular dictionary of id -> element pairs"""
        return dict([(eid, self[xid]) for eid, xid in self.ids.items()])

    def bounding_box(self):
        """
        Gets a :class:`inkex.transforms.BoundingBox` object for the selected items.

        Text objects have a bounding box without width or height that only
        reflects the coordinate of their anchor. If a text object is a part of
        the selection's boundary, the bounding box may be inaccurate.

        When no object is selected or when the object's location cannot be
        determined (e.g. empty group or layer), all coordinates will be None.
        """
        return sum([elem.bounding_box() for elem in self], None)

    def first(self):
        """Returns the first item in the selected list"""
        for elem in self:
            return elem
        return None
