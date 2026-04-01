# OpenEnv Support Ticket Environment

A compact but realistic reinforcement-learning environment for customer-support workflow automation. The agent sees a stream of support tickets and must triage each one by predicting the right category, priority, routing destination, response style, and whether the ticket can be closed.

This is designed to feel like a real operations task rather than a toy game.

## Why this environment exists

Human support teams constantly make structured decisions under time pressure:

- classify the issue,
- assign urgency,
- route it to the right team,
- respond appropriately,
- avoid unsafe or premature closure.

That makes support triage a good fit for RL-style decision making with deterministic grading.

## Project structure

```text
openenv_support_env/
├── app.py
├── baseline/
│   ├── __init__.py
│   └── run_agent.py
├── openenv.yaml
├── requirements.txt
├── Dockerfile
├── README.md
└── support_env/
    ├── __init__.py
    ├── environment.py
    ├── graders.py
    ├── models.py
    └── scenarios.py
```

## OpenEnv interface

The environment follows the standard RL-style API:

- `reset()` returns the first `Observation`.
- `step(action)` returns `(observation, reward, done, info)`.
- `state()` returns the internal `EnvState` snapshot.

Typed Pydantic models are used for the main data contracts:

- `Observation`
- `Action`
- `Reward`
- `EnvState`

## Observation space

Each observation contains:

- task id
- ticket index and total ticket count
- ticket subject and body
- customer tier and sentiment
- prior interactions
- allowed categories, priorities, routes, and response types

## Action space

Each action contains:

- `category`
- `priority`
- `route_to`
- `response_type`
- `reply_text` (optional)
- `close_ticket` (boolean)

## Reward design

Reward is shaped across the full trajectory.

It gives partial credit for:

- matching the true category
- assigning the right priority
- routing to the right team
- selecting the right response type
- drafting a useful reply

It penalizes harmful behavior such as:

- closing a ticket that should remain open
- routing to archive when the issue needs attention
- skipping a reply when one is expected

## Tasks

### 1) `ticket_triage_easy`
Focus: obvious classification and priority decisions.

### 2) `ticket_triage_medium`
Focus: correct routing and action selection, with more policy awareness.

### 3) `ticket_triage_hard`
Focus: nuanced replies, safe closure decisions, and more context-sensitive handling.

## Baseline agent

`baseline/run_agent.py` supports two modes:

- `heuristic` — deterministic offline baseline
- `openai` — runs the OpenAI API client against the environment

The OpenAI SDK reads `OPENAI_API_KEY` from the environment, and the project uses the Responses API for model calls.

### Run the deterministic baseline

```bash
python baseline/run_agent.py --mode heuristic --task all
```

### Run the OpenAI-backed baseline

```bash
export OPENAI_API_KEY="your_key_here"
python baseline/run_agent.py --mode openai --task all
```

## Baseline scores

Measured with the deterministic heuristic baseline:

- easy: **1.000**
- medium: **0.925**
- hard: **0.710**
- average: **0.878**

## Setup

```bash
pip install -r requirements.txt
```

## Local usage

### 1. Run the environment demo API

```bash
uvicorn app:app --reload --port 7860
```

### 2. Inspect tasks

Open:

- `/api/tasks`

### 3. Run a demo rollout

Open:

- `/api/demo/ticket_triage_easy`
- `/api/demo/ticket_triage_medium`
- `/api/demo/ticket_triage_hard`

## Docker

Build and run locally:

```bash
docker build -t openenv-support .
docker run -p 7860:7860 openenv-support
```

## Hugging Face Spaces

This repository is container-friendly for a Hugging Face Docker Space.

Suggested Space settings:

- Space type: Docker
- Tag: `openenv`
- Port: `7860`

## Notes on originality

The scenarios, reward shaping, grader logic, and baseline policy in this repository were written specifically for this project and are not copied from any external template.
