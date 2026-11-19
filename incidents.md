# Incidents — pannes, erreurs, violations de règle, correctifs

Tout incident est journalisé avec timestamp UTC, gravité, impact, cause, correctif et
vérification. Un incident majeur déclenche une alerte immédiate (kill-switch, arrêt d'un
exchange, recharge impossible, stop manquant).

Format :

```
YYYY-MM-DDTHH:MM:SSZ | gravité | titre
Contexte :
Impact :
Cause :
Correctif :
Vérification :
```

## Journal

| date UTC | gravité | titre | état |
|---|---|---|---|
| 2026-11-18 | info | Aucun exchange / broker, API, serveur, flux de données ou Telegram connecté | en attente de configuration |
| 2026-11-18 | info | Aucune donnée réelle téléchargée : backtests limités à des smoke tests synthétiques | en attente de sources |
| 2026-11-18 | info | Réponse 4 laissée vide : outils supposés non connectés | à confirmer |

Aucun incident d'exécution pour l'instant : le bot n'a pas encore accès à un compte.
