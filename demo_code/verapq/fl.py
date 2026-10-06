"""Minimal federated logistic-regression on a synthetic IoT-intrusion-like tabular dataset.
Swap `make_data` for Edge-IIoTset / CICIoT2023 loaders in experiments (see README)."""
import numpy as np
from sklearn.datasets import make_classification
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, f1_score


def make_data(n_clients, n_features=30, samples_per_client=400, seed=0, non_iid_alpha=None):
    X, y = make_classification(n_samples=n_clients * samples_per_client + 2000, n_features=n_features,
                               n_informative=12, n_redundant=6, weights=[0.6, 0.4], flip_y=0.02,
                               class_sep=1.2, random_state=seed)
    X = StandardScaler().fit_transform(X)
    Xte, yte = X[-2000:], y[-2000:]
    X, y = X[:-2000], y[:-2000]
    rng = np.random.default_rng(seed)
    if non_iid_alpha is None:
        idx = rng.permutation(len(y))
        parts = np.array_split(idx, n_clients)
    else:  # Dirichlet label skew
        parts = [[] for _ in range(n_clients)]
        for c in (0, 1):
            ids = rng.permutation(np.where(y == c)[0])
            props = rng.dirichlet([non_iid_alpha] * n_clients)
            cuts = (np.cumsum(props) * len(ids)).astype(int)[:-1]
            for k, chunk in enumerate(np.split(ids, cuts)):
                parts[k].extend(chunk.tolist())
        parts = [np.array(p) for p in parts]
    return [(X[p], y[p]) for p in parts], (Xte, yte)


def load_csv(path, label_col, n_clients, normal_value=None, max_rows=200_000, seed=0, non_iid_alpha=None):
    """Load a tabular IoT IDS CSV (e.g. Edge-IIoTset 'Attack_label', CICIoT2023 'label').
    Label becomes binary: 0 = normal (== normal_value, or 0 if numeric), 1 = attack.
    Non-numeric feature columns are dropped (document this in the paper)."""
    import pandas as pd
    df = pd.read_csv(path, nrows=max_rows, low_memory=False).sample(frac=1.0, random_state=seed)
    y_raw = df.pop(label_col)
    y = (y_raw != (normal_value if normal_value is not None else 0)).astype(int).to_numpy()
    X = df.select_dtypes("number").replace([np.inf, -np.inf], np.nan).fillna(0).to_numpy(dtype=float)
    X = StandardScaler().fit_transform(X)
    n_te = min(20_000, len(y) // 5)
    Xte, yte, X, y = X[:n_te], y[:n_te], X[n_te:], y[n_te:]
    rng = np.random.default_rng(seed)
    if non_iid_alpha is None:
        parts = np.array_split(rng.permutation(len(y)), n_clients)
    else:
        parts = [[] for _ in range(n_clients)]
        for c in (0, 1):
            ids = rng.permutation(np.where(y == c)[0])
            cuts = (np.cumsum(rng.dirichlet([non_iid_alpha] * n_clients)) * len(ids)).astype(int)[:-1]
            for k, chunk in enumerate(np.split(ids, cuts)):
                parts[k].extend(chunk.tolist())
        parts = [np.array(p, dtype=int) for p in parts]
    return [(X[p], y[p]) for p in parts], (Xte, yte)


def _sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))


def local_train(w, X, y, epochs=2, lr=0.2, batch=64, seed=0):
    """Return model delta (w_new - w) after local SGD. w includes bias as last element."""
    rng = np.random.default_rng(seed)
    w = w.copy()
    Xb = np.hstack([X, np.ones((len(X), 1))])
    for _ in range(epochs):
        for s in range(0, len(y), batch):
            b = rng.permutation(len(y))[:batch]
            g = Xb[b].T @ (_sigmoid(Xb[b] @ w) - y[b]) / len(b)
            w -= lr * g
    return w


def poison(delta, kind, rng, scale=8.0):
    if kind == "signflip":
        return -scale * delta
    if kind == "gaussian":
        return rng.normal(0, scale * (np.std(delta) + 1e-3), size=delta.shape)
    return delta


def evaluate(w, Xte, yte):
    p = _sigmoid(np.hstack([Xte, np.ones((len(Xte), 1))]) @ w) >= 0.5
    return accuracy_score(yte, p), f1_score(yte, p)
