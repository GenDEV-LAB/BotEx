# cross_sectional_momentum — Cross-sectional momentum

- **ID idée** : X01
- **Edge** : Le momentum relatif persiste ; la diversification between actifs réduit le risque idiosyncratique.
- **Rules** : Rebalancing toutes les 12h ; long top 2 / short bottom 2 ; stop par jambe à 2 ATR ; autorisé sur perps/futures uniquement.
- **Timeframes** : 4h
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
