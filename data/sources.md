# Sources de données — registre

Règles (section 5 du prompt) :

- Un prix n'est accepté que s'il vient d'une source **nommée**, avec un timestamp et un checksum.
- Deux sources indépendantes doivent concorder avant tout ordre réel.
- Pour les actions : Polygon, Alpaca (vérifier les conditions d'usage et le prix).
- Pour la crypto : Binance (API publique, klines ; la librairie CCXT donne une interface Python commune) ;
  Hyperliquid ne conserve que les 5 000 dernières bougies → sauvegarder quotidiennement pour construire l'historique.
- Données gratuites alternatives : DefiLlama (TVL, stablecoins, yields), Dune (requêtes SQL),
  FRED (taux, inflation, liquidité), calendriers économiques officiels (BLS, FOMC, BCE).
- Aucune donnée réelle n'a encore été téléchargée dans ce dépôt.

## Registre des datasets

| dataset_id | source | URL | symbols | timeframe | couverture UTC | sha256 | récupéré à | licence | contrôles |
|---|---|---|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — | — | — | — |

Remplir une ligne par fichier, puis exécuter `python3 -m bot.cli check-data`.
Un fichier sans ligne ici est ignoré par le bot.

## Contrôles d'intégrité obligatoires

1. Le fichier est listé ci-dessus et son sha256 correspond.
2. Les timestamps sont UTC, uniques, triés et sans doublon.
3. Les gaps dépassant 2x l'intervalle attendu sont journalisés comme incidents.
4. `high >= max(open, close)` et `low <= min(open, close)`, prix > 0.
5. Deux sources indépendantes concordent à 0,05 % près sur les prix used.
6. Aucune valeur manquante n'est comblée par une estimation : le test échoue, on attend la source.

## Données synthétiques

Les fichiers générés par `python3 -m bot.cli make-synthetic` portent le suffixe `.synthetic.csv`
et des symboles `SIM01`… uniquement. Ils servent uniquement aux smoke tests ; ils ne peuvent
pas alimenter une décision réelle (`allow_real_symbols=false` dans `bot/config.json`).
