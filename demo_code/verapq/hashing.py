"""Keccak-256 and EVM abi.encodePacked-compatible encodings, so Python and Solidity agree."""
try:
    from Crypto.Hash import keccak as _k  # pycryptodome

    def keccak(data: bytes) -> bytes:
        h = _k.new(digest_bits=256)
        h.update(data)
        return h.digest()
    KECCAK_IMPL = "pycryptodome"
except ImportError:  # pragma: no cover
    try:
        from eth_hash.auto import keccak as _ek

        def keccak(data: bytes) -> bytes:
            return _ek(data)
        KECCAK_IMPL = "eth-hash"
    except ImportError:
        import hashlib

        def keccak(data: bytes) -> bytes:  # NOT EVM-compatible; Python-only fallback
            return hashlib.sha3_256(data).digest()
        KECCAK_IMPL = "sha3_256 (fallback, EVM path disabled)"


def u256(x: int) -> bytes:
    assert 0 <= x < 2**256
    return x.to_bytes(32, "big")


def i256(x: int) -> bytes:
    assert -(2**255) <= x < 2**255
    return (x % 2**256).to_bytes(32, "big")


def leaf_value(value: int, index: int) -> bytes:
    """keccak256(abi.encodePacked(int256 value, uint256 index))"""
    return keccak(i256(value) + u256(index))


def leaf_client(client_id: int, update_root: bytes, sig_digest: bytes) -> bytes:
    """keccak256(abi.encodePacked(uint256 id, bytes32 root, bytes32 sigDigest))"""
    return keccak(u256(client_id) + update_root + sig_digest)


def round_message(round_id: int, client_id: int, update_root: bytes) -> bytes:
    """Message each IoT client signs with ML-DSA: domain-separated, 32 bytes after hashing."""
    return keccak(b"VERA-PQ/update/v1" + u256(round_id) + u256(client_id) + update_root)
