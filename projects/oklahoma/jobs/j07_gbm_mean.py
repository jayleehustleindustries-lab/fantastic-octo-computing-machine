"""J07: gradient-boosted Poisson mean vs the GLM (same inputs). Does a nonlinear mean beat the GLM?

Alpha (dispersion) is fit on a held-out season, not on the GBM's own training fit (which would be too tight).
Gate: adopt only if mean nll gain > 0.002 vs context_glm_plus2 in most market-seasons. Output: reports/jobs/j07_gbm.csv
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from jobs import common as C
from oklahoma.features import STATS
from oklahoma.models import MU_FLOOR, ContextGLMPlus2, fit_alpha, log_pmf


class GBMPoisson(ContextGLMPlus2):
    name = "gbm_poisson"
    iters = 300

    def _gbm(self):
        return HistGradientBoostingRegressor(loss="poisson", max_iter=self.iters, learning_rate=0.05, max_leaf_nodes=15,
                                             l2_regularization=1.0, min_samples_leaf=40, random_state=0)

    def fit(self, train):
        last = train["season"].max()
        inner, held = train[train.season < last], train[train.season == last]
        # base fit gives the league constants / usage fill the design matrix needs
        ContextGLMPlus2.fit(self, train)
        Xi = self._design(inner); mi = self._gbm().fit(Xi, inner[self.stat])
        mu_h = np.maximum(mi.predict(self._design(held)), MU_FLOOR); yh = held[self.stat].to_numpy()
        self.alpha_edges_ = np.quantile(mu_h, [0.2, 0.4, 0.6, 0.8])
        bins = np.digitize(mu_h, self.alpha_edges_)
        pooled = fit_alpha(yh, mu_h)
        self.alpha_bins_ = np.array([fit_alpha(yh[bins == b], mu_h[bins == b]) if (bins == b).sum() >= 200 else pooled for b in range(5)])
        self.gbm_ = self._gbm().fit(self._design(train), train[self.stat])
        return self

    def predict_mean(self, df):
        if hasattr(self, "gbm_"):
            return np.maximum(self.gbm_.predict(self._design(df)), MU_FLOOR)
        return super().predict_mean(df)


def main():
    args = C.parser(__doc__).parse_args()
    f = C.features(); rows = []
    markets = ["points"] if args.quick else STATS
    for market in markets:
        el = C.eligible(f, market)
        for s in C.seasons(args):
            train, test = C.split(el, s)
            y = test[market].to_numpy()
            glm = ContextGLMPlus2(market).fit(train); mg = glm.predict_mean(test)
            gb = GBMPoisson(market); gb.iters = 60 if args.quick else 300; gb.fit(train); mb = gb.predict_mean(test)
            rows.append({"market": market, "season": s, "nll_glm": float(-log_pmf(y, mg, glm.alpha_for(mg)).mean()),
                         "nll_gbm": float(-log_pmf(y, mb, gb.alpha_for(mb)).mean()),
                         "mae_glm": float(np.abs(y - mg).mean()), "mae_gbm": float(np.abs(y - mb).mean())})
    out = pd.DataFrame(rows).round(4); out["gain"] = (out.nll_glm - out.nll_gbm).round(4)
    C.OUT.mkdir(parents=True, exist_ok=True); out.to_csv(C.OUT / "j07_gbm.csv", index=False); print(out.to_string(index=False))


if __name__ == "__main__":
    main()
