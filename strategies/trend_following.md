# trend_following — Trend following

- **ID idée** : T01
- **Edge** : Les tendances persistent sur les actifs liquides ; ce sont les stop-runs et les trend followers qui paient la sortie.
- **Rules** : Entrée long/short au croisement EMA20/EMA50 avec ADX>20 ; stop à 2 ATR sous/au-dessus l'entrée ; taille = 1% du capital / distance du stop.
- **Timeframes** : 4h/1h
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
