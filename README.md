# BotEx — lancer le bot

Une seule commande :

```bash
./run.sh
```

Elle exécute le cycle complet et affiche un rapport court : stratégies testées, trades paper,
equity, kill-switch, alertes, approbations en attente, chemin du rapport détaillé.

Tout tourne en **paper** avec des données synthétiques. Aucun compte, aucune clé, aucun
serveur, aucun courtier n'est nécessaire pour commencer. `XAUUSD` est déjà dans la watchlist
sous le proxy `SIMXAU`.

## Vérifications (optionnel)

```bash
python3 -m unittest discover -s bot/tests -v   # tests
python3 -m bot.cli --json acceptance           # contrôle global
python3 -m bot.cli --help                      # toutes les commandes avancées
```

## Règles d'or

1. Pas de stop sur l'exchange → pas de trade.
2. Pas de backtest avec tous les coûts → pas de trade.
3. Pas de ticker réel sans deux sources vérifiées → pas d'argent réel.
4. Pas de « go live » explicite → jamais de mode live.

Limites configurées : 1 000 USD, 1 %/trade, −5 %/jour, kill-switch −10 %, levier 5x,
5 trades/jour. Détails dans [`playbook.md`](playbook.md). Le rapport du dernier passage est
dans `reports/`, les tests dans `backtests/`, les trades dans `trades.csv`.
