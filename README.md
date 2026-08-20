# CompilerMind

**Offline Goal-Driven AI Agent for Compiler Design**

CompilerMind is a completely offline, low-CPU AI agent designed to understand compiler-design goals, plan the required steps, execute compiler algorithms, verify the results, and continue working until the goal is achieved.

It is not limited to answering theoretical questions. CompilerMind is intended to actively build, analyse, test, debug, and improve compiler components.

## Example Goals

```text
Create a lexer for an arithmetic-expression language.

Convert this grammar into an LL(1) grammar and generate its parser.

Find and fix semantic errors in this source program.

Generate three-address code and optimize it.

Build a small compiler for the provided language specification.
```

## How It Works

```text
User Goal
   ↓
Goal Understanding
   ↓
Compiler Task Planning
   ↓
Algorithm and Tool Selection
   ↓
Execution
   ↓
Verification
   ↓
Error Correction and Iteration
   ↓
Completed Goal
```

## Core Capabilities

### Goal Understanding

* Interpret compiler-design requirements
* Identify expected input and output
* Break complex goals into smaller tasks
* Detect missing information and constraints

### Lexical Analysis

* Define tokens and lexical rules
* Build symbol tables
* Tokenize source code
* Detect lexical errors
* Construct and simulate finite automata

### Syntax Analysis

* Process context-free grammars
* Calculate FIRST and FOLLOW sets
* Remove left recursion
* Perform left factoring
* Build LL(1) parsing tables
* Implement recursive-descent parsers
* Support bottom-up parsing algorithms
* Generate parse trees
* Detect and report syntax errors

### Semantic Analysis

* Perform type checking
* Manage scopes
* Validate declarations and identifiers
* Detect semantic errors
* Maintain symbol-table information

### Intermediate Code Generation

* Generate three-address code
* Create quadruples and triples
* Build syntax trees
* Generate intermediate representations
* Represent control-flow operations

### Code Optimization

* Constant folding
* Constant propagation
* Dead-code elimination
* Common subexpression elimination
* Copy propagation
* Basic-block analysis
* Control-flow optimization
* Peephole optimization

### Code Generation

* Translate intermediate code into target instructions
* Manage registers and temporary values
* Generate code for expressions and control flow
* Support a lightweight virtual machine

### Verification

* Test every generated compiler component
* Compare expected and actual outputs
* Detect incomplete goals
* Trace errors back to their source
* Revise the plan and retry failed steps

### Explanation Engine

* Explain every operation in simple language
* Display intermediate steps
* Show why an algorithm was selected
* Produce debugging and verification reports

## Agent Architecture

CompilerMind contains one central autonomous agent supported by specialised internal engines:

* Goal Interpreter
* Task Planner
* Compiler Knowledge Engine
* Lexical Analysis Engine
* Parsing Engine
* Semantic Analysis Engine
* Intermediate Code Engine
* Optimization Engine
* Code Generation Engine
* Verification Engine
* Local Memory System

The central agent coordinates these engines and maintains progress until the requested compiler-design goal is completed.

## Offline and Low-CPU Design

CompilerMind is designed to:

* Work without an internet connection
* Avoid cloud APIs
* Avoid dependence on large language models
* Run on ordinary CPUs
* Use deterministic and symbolic algorithms
* Store knowledge and progress locally
* Load only the components required for the current goal
* Prefer Python standard-library implementations

## Planned Repository Structure

```text
CompilerMind/
├── compiler_mind/
│   ├── agent/
│   ├── planning/
│   ├── knowledge/
│   ├── lexical_analysis/
│   ├── syntax_analysis/
│   ├── semantic_analysis/
│   ├── intermediate_code/
│   ├── optimization/
│   ├── code_generation/
│   ├── verification/
│   ├── memory/
│   └── interface/
├── examples/
├── tests/
├── docs/
├── LICENSE
└── README.md
```

## Development Roadmap

### M1 — Agent Foundation

Goal representation, task planning, execution control and local memory.

### M2 — Lexical Analysis Engine

Token definitions, tokenizer, lexical errors and finite-automata support.

### M3 — Grammar Processing

Grammar representation, FIRST/FOLLOW sets, left-recursion removal and left factoring.

### M4 — Parser Generation

LL(1), recursive-descent and bottom-up parsing systems.

### M5 — Semantic Analysis

Symbol tables, scope handling, declaration validation and type checking.

### M6 — Intermediate Code Generation

Syntax trees, three-address code, quadruples and control-flow representation.

### M7 — Optimization Engine

Local and global optimization algorithms.

### M8 — Target Code Generation

Virtual-machine instructions, register management and executable output.

### M9 — Autonomous Verification

Testing, failure detection, replanning and automatic correction.

### M10 — Complete Compiler Goal Execution

End-to-end autonomous creation, analysis and improvement of small compilers.

## Project Status

Implemented on `main`:

* M2 lexical execution, verification and learning-by-doing loop
* M3 grammar representation, FIRST/FOLLOW, left-recursion removal and left factoring
* M4 LL(1) table generation, predictive parsing, recursive-descent parsing, parse trees, syntax-error reporting, SLR(1) bottom-up parsing, parser-conflict hypotheses and lexer-to-parser terminal adaptation
* M5 semantic AST, primitive type system, symbol tables, nested scopes, declaration/identifier validation, expression and assignment type checking, function signatures/calls, return checking and structured semantic diagnostics

The next implementation milestone is M6 intermediate code generation.

## Long-Term Vision

The long-term goal is to build an AI agent that can receive a language or compiler-related objective and independently:

1. Understand the language specification
2. Design the compiler architecture
3. Implement every compilation stage
4. Test and debug the compiler
5. Optimize the generated code
6. Verify that the original goal has been achieved

CompilerMind aims to make compiler construction understandable, automated, offline, and computationally efficient.
