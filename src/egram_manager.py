from collections import deque

class FloatQueue:
    def __init__(self):
        self._items = deque()

    def is_empty(self):
        return not self._items

    def enqueue(self, item: float):
        if not isinstance(item, float):
            raise TypeError("Only float values can be enqueued")
        self._items.append(item)

    def dequeue(self):
        if self.is_empty():
            raise IndexError("Dequeue from an empty queue")
        return self._items.popleft()

    def peek(self):
        if self.is_empty():
            raise IndexError("Peek from an empty queue")
        return self._items[0]

    def size(self):
        return len(self._items)

    def __str__(self):
        return f"Front -> {list(self._items)}"