# volatility_breakout — Volatility breakout

- **ID idée** : V01
- **Edge** : La compression de volatilité précède l'expansion ; les strategies de volumes payent le move.
- **Rules** : Entrée à la clôture hors range après compression ; stop à 1 ATR ; taille réduite car le slippage est élevé.
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
