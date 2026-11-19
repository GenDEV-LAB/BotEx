# event_calendar — Event / calendar

- **ID idée** : E01
- **Edge** : Le slippage et les gaps autour des événements détruisent les petits comptes ; c'est une règle de survie, pas un trade.
- **Rules** : Pas d'entrée de -30 à +30 min ; vérifier stops et levier avant ; après : 15 min d'attente, 2 sources, demi-taille.
- **Timeframes** : toutes
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
