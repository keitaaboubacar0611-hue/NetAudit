# NetAudit — Outil d'audit de conformité réseau

Automatisation de la vérification des règles de sécurité sur équipements Cisco IOS via Python et SSH.

---

## Problème résolu

Dans un parc réseau, vérifier manuellement que chaque routeur respecte les règles de sécurité (HTTP désactivé, Telnet banni, sessions avec timeout...) est long et source d'erreurs. NetAudit automatise cette vérification et produit un rapport de conformité avec un score global en quelques secondes.

---

## Fonctionnement

```
Inventaire  -->  Connexion SSH (netmiko)  -->  show running-config
                                                       |
                                          Vérification des règles
                                                       |
                                          Rapport Rich (tableau + score)
```

### Deux modes d'exécution

| Mode | Utilisation | Paramètre |
|------|------------|-----------|
| Dry Run (simulation) | Test sans réseau, configs fictives intégrées | `dry_run=True` |
| SSH réel | Connexion aux vrais équipements | `dry_run=False` |

---

## Règles de sécurité vérifiées

| Règle | Criticité | Pattern recherché |
|-------|-----------|-------------------|
| Serveur HTTP désactivé | CRITIQUE | `no ip http server` |
| Serveur HTTPS désactivé | CRITIQUE | `no ip http secure-server` |
| Telnet interdit (SSH uniquement) | CRITIQUE | `transport input ssh` |
| Timeout de session défini | MOYEN | `exec-timeout` |
| Banner de connexion présente | FAIBLE | `banner motd` |

Ajouter une règle = ajouter une ligne dans le dictionnaire `REGLES_SECURITE`, sans toucher au reste du programme.

---

## Installation

```bash
pip install netmiko pyyaml rich
```

```bash
git clone https://github.com/keitaaboubacar0611-hue/NetAudit.git
cd NetAudit
python main.py
```

---

## Exemple de sortie

```
=======================================
   NetAudit -- Demarrage de l'audit
=======================================
Mode : Simulation (Dry Run)

> Audit de Router-Paris (192.168.1.1)
  -> Analyse terminee (5 regles verifiees)
> Audit de Router-Lyon (192.168.1.2)
  -> Analyse terminee (5 regles verifiees)

+------------------+------+------------------------------+-----------+--------------+
| Equipement       | Site | Regle verifiee               | Criticite |    Statut    |
+------------------+------+------------------------------+-----------+--------------+
| Router-Paris     | Paris| Serveur HTTP desactive       | CRITIQUE  |     OK       |
| Router-Lyon      | Lyon | Serveur HTTP desactive       | CRITIQUE  |  VULNERABLE  |

Score global de conformite : 53% (8/15 regles respectees)
```

---

## Stratégie de test

Le mode Dry Run intègre trois profils de routeurs simulés :

- Router-Paris : bien configuré, score élevé
- Router-Lyon : HTTP actif, Telnet autorisé, vulnérabilités détectées
- Router-Lille : configuration permissive, score bas

Cela permet de valider l'algorithme sans aucun équipement réseau. Pour un test SSH réel, passer `dry_run=False` et renseigner les équipements dans `INVENTAIRE`. Compatible Cisco Packet Tracer et GNS3.

---

## Structure du projet

```
NetAudit/
├── main.py          # Script principal (audit + rapport)
├── README.md        # Documentation
└── inventory.yaml   # (optionnel) liste des équipements en production
```

---

## Evolutions possibles

- Lecture de l'inventaire depuis un fichier YAML externe
- Export du rapport en PDF ou CSV
- Alerte par e-mail si le score descend sous un seuil
- Interface web (Flask/FastAPI)
- Support multi-constructeurs (Juniper, HP)

---

## Stack technique

- Python 3.10+
- Netmiko : abstraction SSH multi-constructeurs
- Rich : rendu terminal (tableaux, couleurs)
- PyYAML : gestion de l'inventaire

---

## Auteur

Keita Aboubacar — Etudiant ingénieur ENIB, Brest  
github.com/keitaaboubacar0611-hue
