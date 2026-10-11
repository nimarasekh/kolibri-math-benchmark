# 🧠 Kolibri-1 Category Theory Benchmark

> **How far can a reasoning model get on category theory and higher category theory when every problem has one exact numerical answer?**

This repository benchmarks **Aleph Alpha's Kolibri-1** on a collection of problems in category theory, homotopy theory, higher category theory, and neighboring areas.

The benchmark is deliberately simple to score:

- every question has a **single integer answer**;
- there are **no multiple-choice options**;
- each question is run **5 times**;
- the model is allowed a large reasoning budget;
- a run counts as correct only if it terminates and returns the correct integer.

The interesting part is not just *whether* Kolibri gets the answer right, but **how its behavior changes as the mathematics becomes more advanced**.

---

## 🚀 Headline result

### 40 questions · 200 runs · 4 difficulty levels

| Difficulty | Questions | Runs | Correct | Wrong | Hit length limit | Raw accuracy |
|---|---:|---:|---:|---:|---:|---:|
| 🟢 Easy | 10 | 50 | 40 | 6 | 4 | **80%** |
| 🟡 Medium | 10 | 50 | 15 | 8 | 27 | **30%** |
| 🟠 Hard | 10 | 50 | 18 | 4 | 28 | **36%** |
| 🔴 Very hard | 10 | 50 | 6 | 1 | 43 | **12%** |
| **Total** | **40** | **200** | **79** | **19** | **102** | **39.5%** |

At first glance, **39.5%** looks rough.

But that hides the most interesting feature of the benchmark:

> **Kolibri is often accurate when it actually finishes.**

Among completed runs:

| Difficulty | Completed runs | Correct among completed | Conditional accuracy |
|---|---:|---:|---:|
| 🟢 Easy | 46 / 50 | 40 / 46 | **87.0%** |
| 🟡 Medium | 23 / 50 | 15 / 23 | **65.2%** |
| 🟠 Hard | 22 / 50 | 18 / 22 | **81.8%** |
| 🔴 Very hard | 7 / 50 | 6 / 7 | **85.7%** |
| **Overall** | **98 / 200** | **79 / 98** | **80.6%** |

So the dominant failure mode on difficult problems is not necessarily:

> *“Kolibri confidently gives the wrong answer.”*

It is increasingly:

> *“Kolibri keeps reasoning until it exhausts the output budget.”*

That distinction is one of the main takeaways of the benchmark.

---

## 📈 Completion collapses before accuracy does

The completion rate drops sharply with difficulty:

```text
Easy       ██████████████████░░   92%
Medium     █████████░░░░░░░░░░░   46%
Hard       █████████░░░░░░░░░░░   44%
Very hard  ███░░░░░░░░░░░░░░░░░   14%
```

But conditional accuracy among completed answers remains surprisingly high.

This suggests a useful separation between two capabilities:

1. **Finding a mathematically viable route**
2. **Bringing that route to completion within a finite reasoning budget**

Kolibri sometimes appears to have enough mathematical knowledge to solve a difficult problem, but struggles to terminate its reasoning efficiently.

> ⚠️ Conditional accuracy is selection-biased: the runs that finish are likely the runs where the model found a good route early. So **85.7% on completed very-hard runs does *not* mean 85.7% very-hard accuracy**.

---

## 🎓 What do the difficulty levels mean?

The labels describe the **mathematical level of the problem**, not empirical difficulty for Kolibri.

| Tier | Rough human study level | Typical flavor |
|---|---|---|
| 🟢 **Easy** | Advanced Bachelor / early Master's | Basic category theory, finite constructions, simple nerves and functor counting |
| 🟡 **Medium** | Master's / beginning PhD | Kan extensions, adjunctions, homotopy pullbacks, groupoid completion |
| 🟠 **Hard** | Early PhD / advanced graduate coursework | Presheaves, twisted arrow categories, stable/homotopical constructions |
| 🔴 **Very hard** | Mid-PhD / specialist coursework | Recognizing and applying substantial theorems from higher algebra, topology, or representation theory |

The **very hard** questions were designed with a particular philosophy:

> A strong solution should require recognizing an abstract theorem or conceptual machine, and then using it to reduce the problem to a finite exact calculation.

Examples include:

- Barratt–Priddy–Quillen
- Solomon–Tits
- homotopy fixed points and group cohomology
- twisted-arrow/end formulas
- sheaf cohomology of local systems
- stable mapping calculations

These are not research problems. They are better thought of as **research-level background turned into exercise-shaped questions**.

---

## 🧪 Benchmark design

Each question is run **five independent times**.

### Model configuration

```text
Model:              Aleph-Alpha/Kolibri-1
Reasoning effort:   high
Temperature:        1
Top-p:              0.97
Max output tokens:  32768
Runs per question:  5
```

Each problem ends with:

> **Give your final answer as a single integer. Your response must contain nothing else; any additional text will be counted as incorrect.**

The grader records:

- expected answer;
- suggested answer;
- exact match;
- finish reason;
- runtime;
- token usage.

If the model reaches the maximum output length before producing a final answer, the run is graded as a **length failure**.

---

## 🧩 Some interesting cases

### `m10`: consistently wrong

`m10` is a finite-poset adjunction/counting problem.

Correct answer:

```text
35
```

Kolibri completed **all five runs** — and returned:

```text
10
10
10
10
10
```

This is a clean example of a **stable conceptual mistake** rather than a timeout.

---

### `h3`: strict colimit vs. ∞-categorical colimit

This question asks for the first homology of a left Kan extension in the **∞-category of spaces**.

The correct calculation uses

\[
\operatorname*{colim}_C \operatorname{const}(X)
\simeq
X \times |NC|.
\]

In this case,

\[
|NC| \simeq S^1,
\qquad
X=S^1,
\]

so the result is a torus and the answer is:

```text
2
```

An earlier version of the question was slightly ambiguous about whether the colimit was strict or homotopy-coherent, so the prompt was revised to explicitly say that the left Kan extension is computed in the **∞-category of spaces**.

After clarification:

- 4 / 5 runs hit the length limit;
- the one completed run still answered `1`.

So this became a useful diagnostic example: the ambiguity was removed, but the conceptual error remained.

---

### `h4` and `h9`: hard but reliable

Some genuinely advanced questions were solved consistently:

```text
h4: 5 / 5 correct
h9: 5 / 5 correct
```

This is a reminder that **human mathematical difficulty and LLM difficulty are not monotone**.

A theorem-heavy problem may be easy for a model if it recognizes the pattern immediately, while a simpler bespoke combinatorial argument may be much harder.

---

### `v9`: Solomon–Tits

One of the very-hard problems asks about the spherical building of \(GL_4(\mathbf F_3)\).

The key input is the **Solomon–Tits theorem**, after which the computation is short:

\[
\operatorname{rank}\widetilde H_2
=
3^{\binom 42}
=
3^6
=
729.
\]

Kolibri solved this correctly in **1 out of 5 runs**.

The other four never reached a final answer.

---

## 🤖 What does the benchmark seem to measure?

Not just factual recall.

A typical difficult question requires several stages:

```text
recognize structure
      ↓
identify theorem
      ↓
translate theorem into concrete algebra
      ↓
perform exact finite computation
      ↓
stop reasoning
      ↓
output one integer
```

Kolibri often succeeds at the first few stages but appears to have trouble with the penultimate one:

> **knowing when it has enough information to stop.**

That is especially visible in the very-hard tier, where **43 of 50 runs** hit the output-length limit.

---

## 🗂 Repository structure

A typical layout is:

```text
.
├── prompts/
│   ├── e1.txt
│   ├── ...
│   ├── m1.txt
│   ├── ...
│   ├── h1.txt
│   ├── ...
│   └── v10.txt
│
├── solutions/
│   ├── e1s.txt
│   ├── ...
│   └── v10s.txt
│
├── results/
│   ├── grading.csv
│   ├── usage.csv
│   └── ...
│
└── test_kolibri.py
```

Question prefixes indicate difficulty:

```text
e = easy
m = medium
h = hard
v = very hard
```

---

## 📊 Result files

### `results/grading.csv`

Contains one row per benchmark run:

```text
question
run
difficulty
correct_answer
suggested_answer
match
finish_reason
time_seconds
grading_reason
```

### `results/usage.csv`

Tracks token and runtime information:

```text
question
run
input_tokens
output_tokens
total_tokens
reasoning_characters
answer_characters
finish_reason
time_seconds
attempts
request_id
```

---

## 🔍 A few numbers worth remembering

```text
200 total runs
79 correct
19 completed but wrong
102 hit the length limit
```

Among all completed runs:

```text
79 / 98 = 80.6% correct
```

Among all runs:

```text
79 / 200 = 39.5% correct
```

And on the very-hard tier:

```text
6 correct
1 completed but wrong
43 length failures
```

That is probably the single best summary of the benchmark.

---

## 🧠 Interpretation

A compact way to describe the result is:

> **Kolibri-1 shows substantial competence on advanced category-theoretic mathematics when it reaches a final answer, but its completion rate deteriorates dramatically as problems become more difficult.**

Or, less formally:

> **The model often knows enough mathematics — it just doesn't always know when to stop thinking.**

---

## ⚠️ Limitations

This is a small benchmark, and it should be interpreted accordingly.

- Only **40 questions** are included.
- Each question is sampled only **5 times**.
- Difficulty labels are human judgments.
- Conditional accuracy is heavily affected by selection bias.
- All answers are integers, so the benchmark does not evaluate exposition or proof quality directly.
- A 32,768-token reasoning budget is generous, but still finite.
- The questions are concentrated in category theory, homotopy theory, and adjacent subjects rather than mathematics broadly.

The goal is therefore not to produce a universal model ranking.

The goal is to probe a narrower question:

> **What happens when a modern reasoning model is pushed from elementary category theory into genuinely specialized higher mathematics?**

---

## 🔮 Possible next steps

Natural extensions would include:

- comparing multiple models on the exact same prompt set;
- varying the reasoning budget;
- measuring *time-to-correct-answer* rather than only final correctness;
- manually classifying failure modes;
- testing whether explicit theorem hints rescue length failures;
- separating theorem-recognition questions from calculation-heavy questions;
- adding proof-based grading alongside exact-answer grading.

---

## 🏁 Bottom line

```text
Easy       → usually solves it
Medium     → mixed
Hard       → surprisingly strong when it finishes
Very hard  → rarely finishes, but usually correct when it does
```

And that is exactly what made this benchmark interesting.
