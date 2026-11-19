# mean_reversion — Mean reversion

- **ID idée** : M01
- **Edge** : Les excursions intraday excessives se résorbent ; les market makers qui absorbent le déséquilibre paient le retour.
- **Rules** : Entrée contre l'excursion quand |z|>2 ; stop à 1,5 ATR ; sortie au retour à SMA20 ; pas d'ajout.
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
