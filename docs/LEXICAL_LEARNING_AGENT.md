# Learning-by-Doing Lexical Agent

## Purpose

CompilerMind should not perform lexical analysis by asking an AI model to reason over every character. The actual scan must stay deterministic, fast, offline, and low-CPU.

The AI capability is used where reasoning is valuable: understanding a language specification, proposing lexical rules, designing experiments, diagnosing failures, improving rules, and deciding what verified knowledge should be retained.

This gives CompilerMind a **learning-by-doing lexical-analysis capability**.

---

## Core Idea

The lexical subsystem follows this loop:

```text
Observe
  ↓
Hypothesize
  ↓
Experiment
  ↓
Execute
  ↓
Compare
  ↓
Correct
  ↓
Verify
  ↓
Remember
```

The agent is therefore not just a tokenizer. It can actively discover and improve lexical rules through controlled experiments.

---

## Separation of Responsibilities

### AI Reasoning Layer

The reasoning layer can:

- understand the user's language goal
- identify required token categories
- infer candidate lexical rules from examples
- detect ambiguity in a language specification
- generate useful test cases
- diagnose why a rule failed
- propose corrected rules
- decide whether a discovery has enough evidence to be stored

### Deterministic Lexical Engine

The deterministic engine performs the actual lexical work:

- read source text character by character
- apply lexical rules
- execute DFA/state-machine transitions
- emit tokens
- track line and column positions
- skip or preserve whitespace as specified
- identify invalid characters and malformed lexemes
- update symbol-table information when required

The deterministic engine does not need open-ended reasoning for normal scanning.

---

## Main Components

### 1. Goal Interpreter

Converts a user goal into a lexical-analysis task.

Example:

```text
User:
Build lexical rules for a language containing let, fn, identifiers,
integers, arithmetic operators and comments.
```

Possible structured goal:

```text
keywords       = [let, fn]
identifiers    = required
integers       = required
operators      = [+, -, *, /, =]
comments       = required
error_tracking = line + column
```

---

### 2. Rule Hypothesis Generator

Produces candidate lexical rules from specifications, examples, or previous verified knowledge.

Example observations:

```text
abc     -> IDENTIFIER
abc12   -> IDENTIFIER
_a      -> IDENTIFIER
12abc   -> INVALID
```

Candidate hypothesis:

```text
IDENTIFIER:
first character     = letter or _
remaining characters = letter, digit or _
```

A hypothesis is not treated as knowledge yet.

---

### 3. Experimenter

The Experimenter creates cases that can prove or break the current hypothesis.

For the identifier rule it may generate:

```text
a
_a
a1
abc_25
__
1a
25abc
a-b
```

Good experiments should include:

- normal cases
- boundary cases
- invalid cases
- ambiguous cases
- previously failing cases

---

### 4. Deterministic Executor

Runs the candidate rule using a lexer, DFA, or another deterministic mechanism.

Example:

```text
input: let count = value25 + 10;
```

Output:

```text
KEYWORD      let
IDENTIFIER   count
ASSIGN       =
IDENTIFIER   value25
PLUS         +
NUMBER       10
SEMICOLON    ;
```

This execution path should be cheap enough to run repeatedly during experiments.

---

### 5. Critic

The Critic searches for contradictions and weaknesses.

Example:

```text
Candidate rule:
NUMBER = one or more digits

Input:
25abc
```

The Critic asks whether the language intends this to be:

```text
NUMBER(25) + IDENTIFIER(abc)
```

or:

```text
LEXICAL_ERROR(25abc)
```

If the specification does not determine the answer, the system marks the point as unresolved instead of inventing a rule.

---

### 6. Verifier

The Verifier decides whether a rule is trustworthy enough to use.

A candidate rule should pass:

1. known examples
2. generated edge cases
3. negative examples
4. regression cases
5. consistency checks with neighboring lexical rules

Only verified rules may become stable lexical knowledge.

---

### 7. Experience Memory

CompilerMind stores useful outcomes from completed experiments.

Memory should distinguish:

```text
hypothesis
verified_rule
rejected_rule
unresolved_case
regression_case
```

A stored rule should contain provenance such as:

```text
rule_id
language/profile
rule definition
supporting examples
counterexamples checked
verification result
version
source task
```

The system must never silently convert an unverified hypothesis into a verified rule.

---

## Learning Loop

```text
Lexical Goal
    ↓
Load relevant verified knowledge
    ↓
Create / select candidate rule
    ↓
Generate experiments
    ↓
Run deterministic lexer
    ↓
Expected vs actual comparison
    ↓
Pass? ─────────────── No
  │                    ↓
 Yes             Diagnose failure
  │                    ↓
  │              Revise hypothesis
  │                    ↓
  └────────────── Run again
    ↓
Independent verification
    ↓
Store verified result
```

---

## Example: Learning an Identifier Rule

### Observations

```text
name    -> IDENTIFIER
x2      -> IDENTIFIER
_temp   -> IDENTIFIER
2temp   -> ERROR
```

### Hypothesis H1

```text
identifier = letters followed by letters or digits
```

### Experiment

```text
_temp
```

H1 fails because `_temp` is expected to be valid.

### Revised Hypothesis H2

```text
first     = letter | _
remaining = letter | digit | _
```

### Generated verification cases

```text
a
_a
x2
abc_25
__
2a
@name
```

### Result

If all expected cases pass, H2 can be stored as a verified rule for that language profile.

The important learning event is not merely that the lexer produced tokens. CompilerMind performed an experiment, detected a failed hypothesis, revised it, and verified the replacement.

---

## When AI Thinking Should Be Used

Reasoning should activate for tasks such as:

- incomplete language specifications
- ambiguous token boundaries
- competing lexical rules
- rule induction from examples
- failure diagnosis
- test generation
- choosing an experiment that distinguishes two hypotheses
- deciding whether evidence is sufficient for verification

Reasoning should not be used for routine character-by-character scanning when a verified deterministic rule already exists.

---

## When Deterministic Execution Should Be Used

Use the lexical engine directly when:

- lexical rules are already known
- a DFA/state machine has already been constructed
- source code only needs tokenization
- regression tests are being executed
- known errors need exact line/column reporting

This keeps CompilerMind predictable and low-CPU.

---

## Safety Against False Learning

The learning system must follow these rules:

### Evidence before memory

Do not store a rule merely because one example matched.

### Preserve counterexamples

A failed case is valuable evidence and should remain available for regression testing.

### No silent specification invention

If two interpretations are both valid and the task does not specify which one is intended, record an unresolved case.

### Separate language profiles

A rule learned for one language must not automatically become a universal compiler rule.

### Revalidation after rule changes

When a lexical rule changes, rerun affected regression tests.

### Deterministic final execution

Once rules are verified, normal tokenization should not depend on nondeterministic reasoning.

---

## Proposed Internal Architecture

```text
compiler_mind/
└── lexical_analysis/
    ├── engine.py
    ├── rules.py
    ├── automata.py
    ├── token.py
    ├── errors.py
    └── learning/
        ├── hypothesis.py
        ├── experimenter.py
        ├── critic.py
        ├── verifier.py
        ├── experience.py
        └── regression.py
```

Responsibilities:

```text
hypothesis.py   candidate rule representation
experimenter.py generate discriminating test cases
critic.py       detect contradictions and weak rules
verifier.py     verification gates
experience.py   verified/rejected/unresolved knowledge
regression.py   preserve and rerun important cases
```

This structure is conceptual. Implementation should stay as small as possible and files should only be separated when the separation reduces complexity.

---

## Capability Levels

### L0 — Execute

Use predefined lexical rules and tokenize source code.

### L1 — Diagnose

Explain why tokenization or a lexical rule failed.

### L2 — Experiment

Generate edge cases and run controlled tests.

### L3 — Infer

Propose candidate lexical rules from specifications and observations.

### L4 — Verify

Attempt to falsify candidate rules and promote only sufficiently tested rules.

### L5 — Learn by Doing

Reuse verified discoveries, preserve failures as regression knowledge, and autonomously improve lexical behavior through future tasks.

---

## Definition of Learned

CompilerMind may say that it has learned a lexical rule only when:

```text
candidate created
      +
relevant experiments executed
      +
known counterexamples checked
      +
verification passed
      +
provenance recorded
      +
verified memory updated
```

Therefore:

> Learning = verified behavioral improvement produced through experience, not simply generated text or stored conversation history.

---

## Design Principle

CompilerMind should **think where uncertainty exists and execute deterministically where the rule is known**.

For lexical analysis, intelligence belongs primarily in rule discovery, experimentation, diagnosis, verification, and adaptation. The final scanner remains a lightweight deterministic compiler component.
