# relative_value — Relative value

- **ID idée** : R01
- **Edge** : La dispersion entre actifs liés se résorbe ; le risque directionnel est réduit par la paire.
- **Rules** : Long actif faible / short actif fort quand |z|>2 ; stop sur le spread à 2 sigma ; corrélation à recalculer chaque semaine.
- **Timeframes** : 1h/4h
- **Result** : non mesuré (aucun backtest avec coûts sur données réelles)
- **Risk** : pire cas non mesuré ; drawdown maximal autorisé par le playbook : 10 % depuis le HWM
- **Status** : PENDING — données synthétiques uniquement
- **Tests associés** : à renseigner avec l'ID du fichier dans `../backtests/`

Checklist avant passage en paper réel :
- [ ] 4+ ans de données dont un marché baissier
- [ ] fees / slippage / funding inclus
- [ ] walk-forward 12 mois tune / 3 mois test, 50+ trades hors-échantillon
- [ ] stress test avec slippage doublé, drawdown dans la limite
- [ ] meilleur que buy & hold risk-adjusted
