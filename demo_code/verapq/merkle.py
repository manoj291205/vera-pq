"""Positional binary Merkle tree over 32-byte leaves (padded with zero leaves to a power of two)."""
from .hashing import keccak

ZERO = b"\x00" * 32


class MerkleTree:
    def __init__(self, leaves):
        n = max(1, len(leaves))
        size = 1
        while size < n:
            size *= 2
        self.n = len(leaves)
        self.levels = [list(leaves) + [ZERO] * (size - len(leaves))]
        while len(self.levels[-1]) > 1:
            prev = self.levels[-1]
            self.levels.append([keccak(prev[i] + prev[i + 1]) for i in range(0, len(prev), 2)])

    @property
    def root(self) -> bytes:
        return self.levels[-1][0]

    @property
    def depth(self) -> int:
        return len(self.levels) - 1

    def proof(self, index: int):
        path = []
        for level in self.levels[:-1]:
            path.append(level[index ^ 1])
            index //= 2
        return path


def verify_path(leaf: bytes, index: int, path, root: bytes) -> bool:
    cur = leaf
    for sib in path:
        cur = keccak(sib + cur) if index & 1 else keccak(cur + sib)
        index //= 2
    return cur == root
