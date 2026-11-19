# Calendrier — événements et pauses

Tout est en **UTC**. Les heures ci-dessous sont des repères **à confirmer** sur les sites
officiels (BLS, FOMC, BCE, exchanges) avant chaque semaine ; elles ne doivent pas être
utilisées comme source de vérité pour un ordre.

## Événements récurrents à marquer chaque semaine

| Événement | Heure UTC habituelle | Fréquence | Action |
|---|---|---|---|
| CPI (BLS) | 13:30 | ~mensuel | pas d'entrée ±30 min ; après : 15 min d'attente, 2 sources, demi-taille |
| NFP (BLS) | 13:30 | 1er vendredi du mois | idem |
| FOMC decision + Powell | 19:00 / 19:30 | ~6 semaines | idem |
| FOMC minutes | 19:00 | ~6 semaines | idem |
| BCE / taux | 13:15 | variable | idem |
| Halving Bitcoin | variable | ~4 ans | même playbook |
| ETF decisions / listings | variable | ponctuel | même playbook |
| Expiration options/futures | 20:00 (crypto) | mensuel/trimestriel | vérifier le slippage |

## Playbook « survive first »

**Avant l'événement :**
1. Marquer l'événement dans ce fichier avec l'heure locale **et UTC**.
2. Aucune nouvelle entrée de −30 à +30 minutes autour de la publication.
3. Vérifier chaque position ouverte : stop déposé sur l'exchange, taille dans la limite, levier ≤ 5x.
4. Réduire la taille ou clore les positions qu'un gap traversant le stop pousserait au-delà de la perte journalière.
5. S'attendre à des spreads larges et de mauvais fills ; slippage souvent plusieurs fois normal.

**Après la publication :**
1. Ne rien faire pendant les 15 premières minutes.
2. Vérifier que les flux sont vivants et que les prix concordent sur deux sources.
3. Relire le régime : tendance, range ou forte volatilité ; seules les stratégies prévues pour ce régime peuvent trader.
4. Reprendre les entrées à demi-taille pour le reste du jour.
5. Journaliser l'événement, l'action du bot et le coût/résultat dans `learning.md`.
6. Si un exchange tombe ou gèle les retraits : arrêt immédiat des nouvelles entrées et alerte immédiate.
7. Ne jamais trader le titre de l'info : être rapide sur ce qu'on lit est un jeu qu'on perd contre des firms plus rapides.

Pour **XAUUSD**, marquer en priorité CPI, NFP, FOMC et décisions de taux : l'or réagit très
fortement à ces publications. Appliquer le même playbook « survive first » (pas d'entrée
±30 min, demi-taille après publication).

Les événements datés sont enregistrés dans `data/events.csv` (`ts_utc,label,source`) avec une
source officielle ; le bot bloque automatiquement les nouvelles entrées dans la fenêtre
±30 minutes définie dans `bot/config.json`. Aucune date n'est inventée par le bot.

## Fenêtre d'approbation propriétaire

Supposée 08:00–20:00 UTC (12h déclarées, à confirmer). Aucune modification de règle hors fenêtre.
