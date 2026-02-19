<a id="fr">

<div align=center>
    <a href="#en">EN</a> . 
    <a href="#fr">FR</a>

# Agentception

*Un agent IA en ligne de commande en Python - créé par un agent !*

---
</div>

Dans ce **projet éducatif**, nous avons été mis au défi de créer un **orchestrateur IA autonome** en une seule journée grâce à la collaboration avec des agents IA (vibe coding).

Les agents IA sont des outils logiciels autonomes qui effectuent des tâches, prennent des décisions et interagissent intelligemment avec leur environnement. Ils utilisent l'intelligence artificielle pour apprendre, s'adapter et agir en fonction des retours d'information en temps réel et des conditions changeantes. Les agents IA peuvent travailler seuls ou dans le cadre d'un système plus large, apprenant et changeant en fonction des données qu'ils traitent. [Source : GitHub](https://github.com/resources/articles/what-are-ai-agents)

Notre implémentation d'**agentception** est un orchestrateur IA auto-hébergé, hors ligne, conçu pour fonctionner localement en utilisant des modèles FOSS via Ollama. L'agent peut lire/écrire des fichiers, exécuter des commandes shell et effectuer des tâches d'assistance (comme la recherche sur le web et la prise de notes) dans un environnement Docker en bac à sable.

Ce projet montre comment collaborer efficacement avec des agents de codage IA pour construire un agent de codage IA lui-même ! Sous des contraintes de temps strictes.

C'était le défi du **jour 4** de MiniVibes - un projet éducatif créé par notre école d'informatique. *Pour plus de détails, voir le brief complet du projet (FR & EN) [MiniVibesConsigne.md](./docs/MiniVibesConsigne.md)*

## Qu'est-ce que le vibe coding? Pourquoi?

Le « vibe coding » fait référence à la compétence émergente de travailler efficacement avec des agents de codage IA. À mesure que les agents IA deviennent plus performants, savoir comment les prompter, les guider et collaborer avec eux devient sans doute une compétence importante. Une compétence qui s'ajoute aux compétences traditionnelles de codage.

## Contraintes du projet

Le défi MiniVibes a fonctionné sous des contraintes strictes :
- **temps limité** : un jour par projet
- **jetons limités** : utilisation de modèles « mini » (multiplicateur 0,33x) la plupart du temps
- **budget limité** : une requête premium par projet/jour

Malgré ces limitations, l'objectif est de créer des projets riches en fonctionnalités et de qualité production qui démontrent les compétences en ingénierie des invites et en communication avec les agents.

## Autres exigences du projet

- **spécifications complètes du projet avant le développement** - nous en avons généré une partie avec un LLM (Gemini)
- **contrôle de version basé sur Git avec commits intelligents** - nous fournissons des instructions à Copilot dans [`COPILOT.md`](./COPILOT.md)
- **prompting transparent** - tous les prompts documentés dans [`SESSION.md`](./SESSION.md) avec horodatages
- **code initial généré entièrement par des agents IA** - nous n'avons écrit ou modifié que la documentation, sinon nous avons simplement fourni des invites !

## Résultat final

À venir. Nous documenterons notre résultat ici.

## Structure du projet

À venir. Nous la documenterons ici après la fin du projet.

```
agentception/
├── README.md                # ce fichier
├── LICENSE                  # licence du projet
├── COPILOT.md               # instructions pour l'agent
├── SESSION.md               # journal de session
├── docs/
│   ├── Specification.md     # spécification technique du projet
│   └── MiniVibesConsigne.md # vue d'ensemble du projet plus large
│   └── *.png                # images
└── .gitignore               # fichiers ignorés
```

### Caractéristiques techniques

À venir. Nous la documenterons ici après la fin du projet.

## Problèmes, débogage, optimisation, tests, etc

À venir. Nous documenterons tout autre élément pertinent ici après la fin du projet.

## Compétences

Ce projet démontre :
- **compétences de collaboration avec l'IA** - de plus en plus valorisées dans les entretiens d'embauche et les rôles technologiques
- **développement rapide** - création de fonctionnalités complètes sous contraintes
- **pratiques de codage propre** - flux de travail Git approprié et organisation du code
- **ingénierie des invites** - une compétence technique pratique et émergente
- **gestion du temps** - livrer du travail de qualité dans des délais stricts

## Références

Certaines inspirations pour l'écriture de la spécification ont été tirées de l'article [How to Build an Agent](https://ampcode.com/how-to-build-an-agent) écrit par Thorsten Ball, 15 avril 2025

---

<a id="en">

<div align=center>
    <a href="#en">EN</a> . 
    <a href="#fr">FR</a>

# Agentception

*A command-line AI agent in python - made by a agent!*
---
</div>

In this **educational project** we were challenged to create a **a command-line AI agent** in a single day through AI agent collaboration (vibe coding). 

AI agents are autonomous software tools that perform tasks, make decisions, and interact with their environment intelligently and rationally. They use artificial intelligence to learn, adapt, and take action based on real-time feedback and changing conditions. AI agents can work on their own or as part of a bigger system, learning and changing based on the data they process. [Source: GitHub](https://github.com/resources/articles/what-are-ai-agents)

Our implementation of **agentception** is a self-hosted, offline AI orchestrator designed to run locally using FOSS models via Ollama. The agent can read/write files, execute shell commands, and perform assistant tasks (like web searching and note-taking) within a sandboxed Docker environment.

This project showcases how to collaborate effectively with AI coding agents to build an AI coding agent itself! Under strict time constraints. 

It was the **day 4** challenge of MiniVibes - an educational project set by our training school. *For more details, see complete project brief (French & English) [MiniVibesConsigne.md](./docs/MiniVibesConsigne.md)*

## What is vibe coding? Why? 

Vibe coding refers to the emerging skill of effectively working with AI coding agents. As AI agents are becoming more capable, knowing how to prompt, guide, and collaborate with AI coding agents is perhaps becoming an important skill. One that sits alongside traditional coding skills.

## Project constraints

The MiniVibes challenge operated under strict constraints:
- **limited time**: one day per project
- **limited tokens**: using "mini" models (0.33x multiplier) most of the time  
- **limited budget**: one premium request per project/day

Despite these limitations, the idea is to create feature-rich, production-quality projects that demonstrate prompt engineering and agent communication skills. 

## Other project requirements

- **complete project specifications before development** - we generated some of this with an LLM (Gemini)
- **git-based version control with intelligent commits** - we provide instructions to Copilot in [`COPILOT.md`](./COPILOT.md)
- **transparent prompting** - all prompts documented in [`SESSION.md`](./SESSION.md) with timestamps
- **initial code generated entirely by AI agents** - we only wrote or edited the documentation, otherwise we just prompted!

## Final result

To come. We will document our result here. 

## Project structure

To come. We will document it here after the project is complete. 

```
agentception/
├── README.md                # this file
├── LICENSE                  # project license
├── COPILOT.md               # agent instructions
├── SESSION.md               # session log
├── docs/
│   ├── Specification.md     # technical project specification
│   └── MiniVibesConsigne.md # larger project overview
│   └── *.png                # images
└── .gitignore               # ignored files
```

### Technical features

To come. We will document it here after the project is complete. 

## Issues, debugging, optimizing, testing etc

To come. We will document all other relevant stuff here after the project is complete. 

## Skills

This project demonstrates:
- **AI collaboration skills** - increasingly valued in tech interviews and roles
- **rapid development** - building complete features under constraints
- **clean coding practices** - proper Git workflow and code organization
- **prompt engineering** - a practical, emerging technical skill
- **time management** - delivering quality work within strict timeframes

## References

Some inspiration for writing the specification was taken from the article [How to Build an Agent](https://ampcode.com/how-to-build-an-agent) written by Thorsten Ball, April 15, 2025

---

