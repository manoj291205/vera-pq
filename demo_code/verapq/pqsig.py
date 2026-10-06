"""ML-DSA (FIPS 204) signatures with two interchangeable backends.

1. liboqs-python (fast, native liboqs; algorithm names like "ML-DSA-44")
2. dilithium-py (pure Python; always installs; slow but correct sizes)

Select with env VERAPQ_PQ_BACKEND=liboqs|pure (default: try liboqs, else pure).
"""
import os

_ALG = os.environ.get("VERAPQ_PQ_ALG", "ML-DSA-44")
_PREF = os.environ.get("VERAPQ_PQ_BACKEND", "auto")

BACKEND = None
_oqs = None
if _PREF in ("auto", "liboqs"):
    try:
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            if "OQS_INSTALL_PATH" in os.environ or os.path.exists(os.path.expanduser("~/_oqs")):
                import oqs as _oqs  # only imported when a liboqs install exists (avoids slow auto-build)
                _probe = _oqs.Signature(_ALG)  # raises if the algorithm is not enabled
                BACKEND = "liboqs " + _oqs.oqs_version()
    except Exception:
        _oqs = None
if BACKEND is None:
    from dilithium_py.ml_dsa import ML_DSA_44, ML_DSA_65, ML_DSA_87
    _PURE = {"ML-DSA-44": ML_DSA_44, "ML-DSA-65": ML_DSA_65, "ML-DSA-87": ML_DSA_87}[_ALG]
    BACKEND = "dilithium-py (pure Python)"

ALG = _ALG


class Signer:
    def __init__(self):
        if _oqs is not None:
            self._s = _oqs.Signature(ALG)
            self.pk = self._s.generate_keypair()
        else:
            self.pk, self._sk = _PURE.keygen()

    def sign(self, msg: bytes) -> bytes:
        if _oqs is not None:
            return self._s.sign(msg)
        return _PURE.sign(self._sk, msg)


def verify(pk: bytes, msg: bytes, sig: bytes) -> bool:
    if _oqs is not None:
        with _oqs.Signature(ALG) as v:
            return v.verify(msg, sig, pk)
    return _PURE.verify(pk, msg, sig)
