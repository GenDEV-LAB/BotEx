# breakout_pullback — Breakout / pullbacks

- **ID idée** : B01
- **Edge** : Le retest transforme une cassure brute en entrée avec stop serré ; ce sont les stops des breakouteurs trop tôt qui paient.
- **Rules** : Entrée au retest de la cassure confirmée ; stop sous le niveau cassé ; pas d'entrée si spread > 2x normal.
- **Timeframes** : 1h/30m
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
