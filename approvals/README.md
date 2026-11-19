# Approbations

Aucune approbation n'est actuellement accordée.

Pour autoriser un changement, le propriétaire doit écrire un fichier daté et signé dans ce
dossier, par exemple `go_live-2026-11-18.md`, contenant explicitement :

```
J'autorise BotEx à passer en mode live le <date> sur <exchange> avec <capital>.
Signé : <nom>
```

Le bot refuse tout passage en live tant qu'un tel fichier et la variable d'environnement
`BOTEX_LIVE_APPROVAL=GO_LIVE` ne sont pas présents simultanément. Les clés API ne doivent
jamais être copiées dans ces fichiers.
