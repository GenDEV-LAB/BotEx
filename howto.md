# Mode d'emploi (simple)

## Tous les jours

```bash
./run.sh
```

C'est tout. Le script lance le cycle complet et affiche un rapport en français :

- stratégies évaluées avec fees/slippage/funding,
- meilleure stratégie et nombre de trades,
- trades paper, equity, kill-switch,
- alertes et approbations en attente,
- chemin du rapport détaillé dans `reports/`.

## Si tu veux regarder plus loin

```bash
python3 -m bot.cli --help                 # liste des commandes avancées
python3 -m bot.cli status                 # état et limites
python3 -m bot.cli --json acceptance      # contrôle global
python3 -m unittest discover -s bot/tests -v
```

`backtests/` contient chaque test avec ses réglages, `strategies/leaderboard.md` le classement,
`strategies/selection.md` les critères de validation, `trades.csv` tous les trades paper,
`learning.md` les leçons et décisions.

XAUUSD est suivi via le proxy synthétique `SIMXAU` tant qu'aucune source de prix réelle n'est
connectée. Le short reste désactivé sur spot, et le mode live reste verrouillé par les règles d'or.
