# session_momentum — Micro-structure / sessions

- **ID idée** : S01
- **Edge** : Les sessions ont des profils de liquidité différents ; le flux de Londres pousse souvent la range asiatique.
- **Rules** : Entrée au breakout de la range Asie ; stop de l'autre côté de la range ; pas d'entrée si le spread est anormal.
- **Timeframes** : 15m/5m
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
