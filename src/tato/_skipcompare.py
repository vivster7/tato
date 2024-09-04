SKIP = object()


class SkipCompare(tuple):
    def __lt__(self, other: "SkipCompare") -> bool:
        for x, y in zip(self, other):
            if x is SKIP or y is SKIP:
                continue
            if x != y:
                return x < y
        return False
