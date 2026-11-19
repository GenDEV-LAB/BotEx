# Données vérifiées

Fichiers CSV prêts à l'emploi, colonnes :

```
ts,symbol,open,high,low,close,volume
```

`ts` est un epoch millisecondes UTC. Chaque fichier doit avoir une ligne correspondante
dans `../sources.md` et passer `python3 -m bot.cli check-data`.

Aucun fichier réel pour l'instant. Les smoke tests utilisent des fichiers temporaires
générés à la volée, jamais stockés ici.
