# Learning loop — leçons, règles actuelles, revues

Règles (sections 7 et 13) : une leçon par ligne, écrite le soir. Les propositions du bot
**ne modifient jamais** les règles seules : elles restent en attente d'approbation. On ne
change qu'une seule chose à la fois, on garde un test témoin, et on ne sur-optimise pas sur
une poignée de trades.

## Modèle de carte stratégie

```
[NOM]: [idée en une ligne]
- Edge: [pourquoi ça existe, qui paie]
- Rules: [entry exists, stop], [size], [risk]
- Result: [return], [exact result], [trades]
- Risk: [pière cas] from [start date]
- Status: PASSED / FAILED / PROPOSED — avec ID de test
```

## Règles actuelles (approuvées ou configurées)

| règle | valeur | origine |
|---|---|---|
| risque / trade | 1 % | réponse 2 |
| perte journalière | 5 % | réponse 2 |
| kill-switch | −10 % HWM | réponse 2 |
| levier | 5x max (confirmé le 2026-11-18) | réponse 7 + approbation |
| short | perps/futures seulement | réponse 7 |
| entrées | interdites ±30 min autour d'events majeurs | playbook |
| prix | 2 sources indépendantes requises | section 5.4 |
| arrêt | stop sur exchange obligatoire | section 14.5 |

## Journal des leçons

Format : `date | contexte | observation | action proposée | statut`

| date | contexte | observation | action proposée | statut |
|---|---|---|---|---|
| 2026-11-18 | setup jour 1 | capital 1 000 USD, 1 %/trade, −5 %/jour, −10 % HWM | écrire les limites dans `playbook.md` | ✅ appliqué |
| 2026-11-18 | setup jour 1 | aucun compte, API, serveur, flux ou Telegram connecté | rester en paper, ne pas toucher aux comptes | ✅ appliqué |
| 2026-11-18 | réponse 7 | 5x suggéré, au-dessus des 1–2x du prompt | confirmer ou ramener à 2x avant tout live | ✅ 5x confirmé le 2026-11-18 |
| 2026-11-18 | réponse 5 | timeframes 4h/1h/30m/15m/5m, détention et max trades non précisés | fixer détention et max trades/jour | ✅ 5 trades/jour confirmés le 2026-11-18 ; détention à confirmer |
| 2026-11-18T21:03Z | approbation du propriétaire | levier maximal fixé à 5x, au-dessus des 1–2x suggérés par le prompt | mettre à jour `playbook.md` et `bot/config.json` ; le passage en live reste soumis à un feu vert séparé | ✅ approuvé |
| 2026-11-18T21:06Z | approbation du propriétaire | max trades/jour fixé à 5 | mettre à jour `playbook.md`, `bot/config.json`, `howto.md` | ✅ approuvé |
| 2026-11-18T21:48Z | nouveau marché | XAUUSD demandé par le propriétaire | ajouter à la watchlist, rester long sur spot, attendre deux sources vérifiées | ✅ watchlist mise à jour ⏳ données manquantes |

## Revue quotidienne (template, à remplir chaque soir)

```
Date UTC :
Meilleur trade :            Pire trade :
P&L USD :                   P&L en R :
Live vs paper vs backtest :
Slippage observé vs modélisé :
Ce qui a cassé :
Une leçon écrite sous forme de règle :
Proposition (une seule chose) :       → approbation demandée : oui/non
```

## Revue hebdomadaire (template)

```
Semaine :
Trades / win rate / expectancy R / drawdown :
Survivants du leaderboard :
Champion en titre vs challengers (paper, 2 semaines min.) :
Règles modifiées (une seule) :
Prochaine semaine :
```

Le challenger ne prend la relève qu'après avoir battu le champion en paper pendant au moins
deux semaines. Un backtest gagnant n'est pas une preuve ; un seul trade n'est pas une règle.
| 2026-11-18T20:59:25Z | recherche nocturne : levier 5x non confirmé, au-dessus de la recommandation 1-2x du prompt | ⏳ en attente d'approbation |
| 2026-11-18T20:59:31Z | recherche nocturne : levier 5x non confirmé, au-dessus de la recommandation 1-2x du prompt | ⏳ en attente d'approbation |
| 2026-11-18T21:00:38Z | recherche nocturne : levier 5x non confirmé, au-dessus de la recommandation 1-2x du prompt | ⏳ en attente d'approbation |
| 2026-11-18T21:01:01Z | recherche nocturne : levier 5x non confirmé, au-dessus de la recommandation 1-2x du prompt | ⏳ en attente d'approbation |
| 2026-11-18T21:03:43Z | recherche nocturne : nombre max de trades/jour à confirmer (3 supposés) | ⏳ en attente d'approbation |
| 2026-11-18T21:05:23Z | recherche nocturne : fenêtre d'approbation 08:00–20:00 UTC à confirmer | ⏳ en attente d'approbation |
| 2026-11-18T21:14:22Z | recherche nocturne : fenêtre d'approbation 08:00–20:00 UTC à confirmer | ⏳ en attente d'approbation |
| 2026-11-18T21:14:33Z | recherche nocturne : fenêtre d'approbation 08:00–20:00 UTC à confirmer | ⏳ en attente d'approbation |
| 2026-11-18T21:17:45Z | recherche nocturne : fenêtre d'approbation 08:00–20:00 UTC à confirmer | ⏳ en attente d'approbation |
| 2026-11-18T21:18:27Z | recherche nocturne : fenêtre d'approbation 08:00–20:00 UTC à confirmer | ⏳ en attente d'approbation |
| 2026-11-18T21:20:01Z | recherche nocturne : fenêtre d'approbation 08:00–20:00 UTC à confirmer | ⏳ en attente d'approbation |
| 2026-11-18T21:20:18Z | recherche nocturne : fenêtre d'approbation 08:00–20:00 UTC à confirmer | ⏳ en attente d'approbation |
| 2026-11-18T21:25:36Z | recherche nocturne : fenêtre d'approbation 08:00–20:00 UTC à confirmer | ⏳ en attente d'approbation |
| 2026-11-19T02:40:52Z | recherche nocturne : fenêtre d'approbation 08:00–20:00 UTC à confirmer | ⏳ en attente d'approbation |
| 2026-11-19T02:41:39Z | recherche nocturne : fenêtre d'approbation 08:00–20:00 UTC à confirmer | ⏳ en attente d'approbation |
