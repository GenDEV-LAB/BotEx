# carry_basis — Carry / basis

- **ID idée** : C02
- **Edge** : La porteuse est payée par les positions surchargées ; on ne la prend que dans le sens de la tendance.
- **Rules** : Long perps quand funding positif et prix > EMA200 ; stop sous EMA200 ; funding réel historique requis dans le backtest.
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
