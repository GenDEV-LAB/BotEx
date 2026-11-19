# BotEx — Playbook / mandat

> Ce fichier est la source de vérité pour les limites. Toute modification de ce fichier
> nécessite l'approbation du propriétaire (section 14.10 du prompt). Dernière mise à jour :
> 2026-11-18 (Jour 1 du kickoff).

## 1. Mandat (une phrase)

BotEx est un fonds individuel, automatisé et discipliné qui trade crypto, futures, forex,
matières premières et indices avec **1 000 USD de capital propre**, au maximum **1 % de
risque par trade**, avec un arrêt des nouvelles entrées à **−5 % sur la journée UTC** et un
kill-switch à **−10 % depuis le plus haut historique du compte**, sans levier au-delà de
**5x (confirmé le 2026-11-18)** ni short hors perps/futures, en restant en mode paper jusqu'à une
approbation explicite du passage en live.

## 2. Marchés et instruments

- Crypto : spot, perpetuals (levier et short autorisés sur perps uniquement).
- Futures : levier et short autorisés.
- Forex, matières premières, indices : à confirmer (cash uniquement tant que le courtier n'est pas précisé).
- **XAUUSD (or spot)** : ajouté à la watchlist le 2026-11-18 à la demande du propriétaire.
  Courtier et données réelles **non configurés**. `short_allowed=false` (le mandat interdit le
  short sur spot) ; proxy de test `SIMXAU`. Aucun ordre réel tant que deux sources indépendantes
  avec 4+ ans ne sont vérifiées.
- **Aucun compte exchange/broker existant n'a été déclaré.** Aucun compte n'est connecté.

## 3. Limites chiffrées

| Limite | Valeur | Source |
|---|---|---|
| Capital de départ | 1 000 USD | réponse 2 |
| Risque par trade | 1 % du capital | réponse 2, section 14.1 |
| Perte journalière max | 5 % → blocage des nouvelles entrées jusqu'au prochain jour UTC | réponse 2, section 14.2 |
| Kill-switch | −10 % depuis le high-water mark → tout s'arrête, les stops restent, on attend le propriétaire | réponse 2, section 14.3 |
| Levier max | 5x (**confirmé par le propriétaire le 2026-11-18**, au-dessus des 1–2x suggérés par le prompt) | réponse 7 + approbation |
| Short | autorisé sur perps/futures seulement ; interdit sur spot | réponse 7 |
| Nombre max de trades / jour | 5 (**confirmé le 2026-11-18**) | réponse 5 + approbation |
| Période de détention | intraday à quelques sessions (**à confirmer**) | hypothèse |
| Timeframes | 4h, 1h, 30m, 15m, 5m | réponse 5 |
| Historique requis avant validation | 4+ années, dont un marché baissier (ex. crypto 2022) | section 6 |
| Trades hors-échantillon min. | 50+ | section 6 |
| Walk-forward | 12 mois d'ajustement, 3 mois de test ; ne rapporter que les fenêtres de test combinées | section 6 |

## 4. Temps et disponibilité

- Fuseau : **UTC**. Tous les journaux et rapports sont horodatés UTC.
- Fenêtre d'approbation supposée : **08:00–20:00 UTC** (réponse « 12h » interprétée comme 12 heures d'éveil — **à confirmer**).
- Hors fenêtre : aucune modification de règle, aucun changement de taille, aucun passage en live.
- Cycle quotidien type (à caler sur la fenêtre ci-dessus) :
  - Petit matin : brief, calendrier économique, règles de pause.
  - Matin : health check ; soir : recherche nocturne, comparaison paper vs backtest, scoreboard.
  - Toutes les heures : monitoring automatique (section 11).

## 5. Outils et accès — état réel

| Outil | État | Action requise |
|---|---|---|
| Agent IA | actif | — |
| API exchange / broker | **non connectée** | à configurer seulement si tu veux trader réellement |
| Serveur 24/7 (VPS) | **non configuré** | prévoir une machine toujours allumée |
| Données de marché réelles | **non connectées** (adaptateurs `CsvFeed` / `CcxtFeed` prêts, aucun appel réseau par défaut) | choisir des sources nommées, 4+ ans, deux sources indépendantes pour valider un prix |
| Telegram | **non connecté** (workflow `/yes` / `/no` implémenté) | créer le bot, renseigner `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` dans l'environnement du serveur |
| Comptes existants | **aucun déclaré** | à renseigner avant tout accès réel |

Les clés ne sont **jamais** écrites dans le code, le chat, les logs ou les captures d'écran.
Un exemple sans secret est fourni dans `.env.example`.

## 6. Règles de risque et de sécurité

1. Risque par trade ≤ 1 % du compte, taille calculée depuis le stop.
2. À −5 % sur le jour UTC : plus aucune nouvelle entrée.
3. À −10 % depuis le high-water mark : kill-switch, on garde les stops, on attend le propriétaire.
4. Levier ≤ 5x (confirmé le 2026-11-18), pas de martingale, pas de moyennage à la baisse, pas d'élargissement ni de retrait d'un stop.
5. Chaque position a un stop **déposé sur l'exchange** dès son ouverture. Pas d'exception.
6. Clés trade-only, retraits désactivés, IP verrouillée, rotation toutes les 90 jours.
7. Aucun nombre inventé : prix, fills, backtests et P&L viennent de données journalisées. Toute estimation est étiquetée comme telle.
8. Argent du propriétaire uniquement ; jamais d'argent tiers.
9. Chaque trade est enregistré avec fees, slippage, funding et timestamp UTC dans `trades.csv`.
10. Approbation préalable pour : passage en live, hausse de taille ou de levier, nouveau marché ou
    exchange, changement de stratégie, achat/upgrade de plan, et toute modification de règle.

## 7. Règles de recherche et de validation

- Une stratégie n'entre dans le paper qu'après backtest avec coûts réels : fees (0,10 %/side spot,
  0,05 %/side perps si le tier est inconnu), slippage 0,05 %/side (x2 en stress), funding historique.
- Pas de résultat « prouvé », « garanti » ou « sans risque ». Pas de présentation de résultats paper comme des résultats live.
- Toujours montrer le pire cas à côté du meilleur, en USD et en R, après tous les coûts.
- Un prix n'est fiable que si deux sources indépendantes concordent ; sinon on n'entre pas.
- Pas d'entrée nouvelle dans les 30 minutes autour d'un événement majeur (CPI, FOMC, NFP…) ; voir `calendar.md`.
- Après publication : ne rien faire pendant 15 minutes, vérifier deux sources de prix, relire le régime,
  reprendre à demi-taille pour le reste du jour. Ne jamais trader le titre de l'info.

## 8. Kickoff 7 jours — progression

| Jour | Contenu | État |
|---|---|---|
| 1 | Questions de setup, mandat, limites, arborescence | ✅ fait |
| 2 | 4 ans de données, contrôles d'intégrité, checksums, calendrier | ⚠️ bloqué : sources réelles absentes (structure + checkers prêts) |
| 3 | 24 idées sur toutes les familles, backtests rapides | ✅ idées écrites ; tests rapides sur données synthétiques |
| 4 | Backtests avec coûts, walk-forward, robustesse (frais/slippage x2, paramètres, graines), cartes stratégies | ⚠️ framework prêt, preuve réelle impossible sans données |
| 5 | Bot complet autour de la meilleure stratégie, mode paper, test du stop/kill-switch/crash | ✅ implémenté (paper synthétique) |
| 6 | Paper trading, journal, comparaison backtest, cycle de recherche nocturne | ✅ cycle unique exécuté via `run-once` |
| 7 | Revue hebdomadaire automatisée, P&L, live vs backtest, slippage | ✅ générée ; playbook à mettre à jour après 7 jours de paper réel + approbation |

## 9. Hypothèses à confirmer

1. Courtier / exchange et sous-compte (réponse 1 : marchés donnés, pas de compte).
2. Outils réellement connectés (réponse 4 laissée vide) : pour l'instant : à considérer comme « aucun ».
3. Heures d'éveil : 08:00–20:00 UTC supposées.
4. Période de détention : intraday / quelques sessions supposée ; le smoke test utilise une
   sortie temporelle à 48 h et un objectif par défaut à 2R (`max_holding_hours`,
   `default_reward_risk` dans `bot/config.json`) — valeurs à confirmer avant tout live.

## 10. Approbations reçues

| date UTC | élément | décision |
|---|---|---|
| 2026-11-18T21:03Z | levier maximal | **5x confirmé** par le propriétaire (au-dessus des 1–2x du prompt). Le mode live reste soumis à un feu vert séparé. |
| 2026-11-18T21:06Z | max trades/jour | **5 confirmés** par le propriétaire ; exposition théorique max 5 %/jour, égale à la limite de perte journalière. |
| 2026-11-18T21:48Z | nouveau marché XAUUSD | **Ajouté à la watchlist** par le propriétaire ; courtier/données à connecter, long seulement sur spot, proxy `SIMXAU` pour les tests. |

> Tant que ces points ne sont pas confirmés, le bot reste en `paper` et `allow_real_symbols=false`.
