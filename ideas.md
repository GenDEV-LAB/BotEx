# Idées de stratégies — 24 idées, 9 familles

Règle (section 6) : chaque idée a une raison d'être en une ligne, un test rapide, puis un
test complet avec coûts si elle survit. Les idées rejetées ne sont pas retentées dans le mois
sauf changement de régime de marché. Statut initial : `à tester`. Aucun résultat ci-dessous
n'est une preuve ; les identifiants de test seront renseignés après exécution.

## 1. Trend following — suivre la tendance, couper les pertes

| id | idée (une ligne) | raison | statut |
|---|---|---|---|
| T01 | Cross EMA 20/50 sur 1h, stop ATR 2x | les tendances persistent ; les stops limitent le risque | à tester |
| T02 | Donchian 20 breakup sur 4h, sortie sous EMA 20 | breakout suivi, sortie simple | à tester |
| T03 | ADX > 25 + pullback sur EMA 50 | évite les marchés sans tendance | à tester |
| T04 | SuperTrend ATR 3 sur 4h, confirmation 1h | suit les tendances avec un stop intégré | à tester |

## 2. Mean reversion — retour à la moyenne, sorties rapides

| id | idée (une ligne) | raison | statut |
|---|---|---|---|
| M01 | Z-score de clôture 20 > 2 sur 15m, retour à SMA20 | les excursions intraday se résorbent | à tester |
| M02 | Rejet de bande de Bollinger + RSI < 30 | achat de dislocation courte | à tester |
| M03 | Gap comblé dans les 4h | les gaps se comblent souvent en crypto | à tester |
| M04 | VWAP déviation > 1,5 sigma, retour au VWAP | ancrage institutionnel | à tester |

## 3. Breakout et pullbacks — faux breakouts à éviter

| id | idée (une ligne) | raison | statut |
|---|---|---|---|
| B01 | Cassure du plus haut de la session puis retest | le retest filtre les fausses cassures | à tester |
| B02 | Compression de range 6h puis expansion | la compression précède l'expansion | à tester |
| B03 | Breakout avec volume > 1,5x moyenne | le volume confirme la participation | à tester |
| B04 | Opening range 30m, cassure avec stop sous la range | règle intraday classique | à tester |

## 4. Carry / basis — récolter la prime, jamais nu

| id | idée (une ligne) | raison | statut |
|---|---|---|---|
| C01 | Long spot / short perps quand le funding est très positif | capture du funding, risque de basis | à tester |
| C02 | Funding > 0,05 %/8h avec prix au-dessus EMA 200 | porteuse payée dans la direction de la tendance | à tester |
| C03 | Term structure en contango sur futures, roll calé | le roll rapporte si le marché reste calme | à tester |

## 5. Relative value — paires, corrélation, dispersion

| id | idée (une ligne) | raison | statut |
|---|---|---|---|
| R01 | Z-score du spread entre deux actifs corrélés | la dispersion se résorbe | à tester |
| R02 | Ratio de deux paires sectorielles, retour à la moyenne | exposition neutre au marché | à tester |
| R03 | Basis PERP/spot après choc, convergence | dislocation temporaire | à tester |

## 6. Volatility breakout — ATR haut mais règles strictes

| id | idée (une ligne) | raison | statut |
|---|---|---|---|
| V01 | ATR(14) sous son 20e percentile puis clôture hors range | les basses volatilités précèdent les moves | à tester |
| V02 | Chockner ou Choppiness Index < 25 + breakout | filtre de compression | à tester |
| V03 | Expansion de range après CPI/FOMC, entrée après 15 min | la volatilité événementielle est tradeable sans trader le titre | à tester |

## 7. Cross-sectional momentum — classer, acheter fort, vendre faible

| id | idée (une ligne) | raison | statut |
|---|---|---|---|
| X01 | Rank 12h sur 10 actifs, long top 2 / short bottom 2 | le momentum relatif persiste | à tester |
| X02 | Momentum 7 jours avec filtre de volatilité | évite les actifs trop bruités | à tester |
| X03 | Rotation hebdo sectorielle (indices) | la rotation est un phénomène documenté | à tester |

## 8. Event and calendar — scheduled events, petites tailles

| id | idée (une ligne) | raison | statut |
|---|---|---|---|
| E01 | Aucune entrée ±30 min autour de CPI / FOMC / NFP (règle, pas un trade) | le slippage eventiel détruit les petits comptes | à appliquer |
| E02 | Halving BTC : même playbook « survive first » | les events crypto créent des gaps | à appliquer |
| E03 | Rééquilibrage mensuel d'indice, entrée après le flux | le flux forcé crée de la liquidité | à tester |

## 9. Micro-structure / sessions — le prix est un flux

| id | idée (une ligne) | raison | statut |
|---|---|---|---|
| S01 | Session Asie range, breakout à l'ouverture Londres | les sessions ont des profils différents | à tester |
| S02 | Balances de liquidité : balayage de plus haut puis retour | les stops alimentent le move | à tester |
| S03 | Spread / profondeur anormale sur un exchange | signal de micro-structure, coûts à mesurer | à tester |
| XAU01 | XAUUSD : EMA 20/50 sur 1h, filtre session Londres/New York | l'or tend en session fluide, stop ATR serré | à tester (proxy SIMXAU) |
| XAU02 | XAUUSD : retour à VWAP après excursion > 1,5 sigma | le gold intraday revient souvent au VWAP | à tester (proxy SIMXAU) |

## Procédure de validation (obligatoire avant paper)

1. `fast backtest` sur données synthétiques → vérifier que le code tourne (aucune preuve).
2. `full backtest` avec fees + slippage + funding sur 4+ ans de données réelles vérifiées.
3. Walk-forward 12 mois tune / 3 mois test ; ne rapporter que les fenêtres test combinées.
4. 50+ trades hors-échantillon, stress test avec slippage doublé.
5. Pass bar : profitable après coûts, drawdown dans la limite, meilleur que buy & hold risk-adjusted.
6. Créer une carte dans `strategies/` avec l'ID de chaque test.
