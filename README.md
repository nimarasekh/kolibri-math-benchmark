# Kolibri-1 (Higher) Category Theory Benchmark

> A benchmark testing the open-weight model **[Kolibri-1](https://aleph-alpha.com/kolibri/)** from **Aleph Alpha** on (higher) category theory.

## ⚙️ Setup

The setup is very direct:
- **40 questions**, grouped into four difficulty levels: *easy*, *medium*, *hard*, *very hard*.
- **5 independent runs** for each question.  
- **A single integer answer** for every problem, so grading is automatic and involves no subjective evaluation.

---

## 🎓 Difficulty scale

The difficulty levels were chosen in advance. The classifications are subjective and roughly correspond to the following background level:

| Level | Typical academic stage | Typical background |
|---|---|---|
| 🟢 Easy | Bachelor / early Master's | Basics of category theory and topology |
| 🟡 Medium | Master's | Graduate-level category theory and algebraic topology, some familiarity with higher categories |
| 🟠 Hard | Early PhD | Basics of higher-categorical notions: Kan extensions, colimits, ... |
| 🔴 Very hard | Early PhD / mid-PhD | Some familiarity with specialized theorems and techniques in higher category theory |

---

## 📊 Results

The following table summarizes the results.
- ✅ **Correct** means the model produced a number and it was correct.
- ❌ **Wrong** means the model produced a number and it was wrong.
- ⏳ **Length limit** means the model reached the maximum output length without producing an answer.
- 📊 **Accuracy** is the percentage of correct runs among all runs.

| Difficulty | Questions | Runs | Correct | Wrong | Length limit | Accuracy |
|---|---:|---:|---:|---:|---:|---:|
| 🟢 Easy | 10 | 50 | 40 | 6 | 4 | **80%** |
| 🟡 Medium | 10 | 50 | 15 | 8 | 27 | **30%** |
| 🟠 Hard | 10 | 50 | 18 | 4 | 28 | **36%** |
| 🔴 Very hard | 10 | 50 | 6 | 1 | 43 | **12%** |
| **Total** | **40** | **200** | **79** | **19** | **102** | **39.5%** |

If we remove all runs that hit the **length limit** we have the following adjusted table:

| Difficulty | Completed | Correct | Accuracy when completed |
|---|---:|---:|---:|
| 🟢 Easy | 46 | 40 | **87.0%** |
| 🟡 Medium | 23 | 15 | **65.2%** |
| 🟠 Hard | 22 | 18 | **81.8%** |
| 🔴 Very hard | 7 | 6 | **85.7%** |
| **Overall** | **98** | **79** | **80.6%** |

### Conclusion

> The overall benchmark score is **39.5%**, but among runs that produced an answer, **Kolibri-1** was correct **80.6%** of the time.  
> In this benchmark, a completed answer was therefore a strong indicator of correctness.

---

## 🔍 Some Observations

A few patterns were especially noticeable:
- The easy problems were solved very reliably, however, there some exceptions, notably *e6* and *e9*.
- Surprisingly, hard did slightly better than medium (*36%* vs. *30%*).
- The completion rates (correct or wrong) do decrease with increasing level of difficulty.
- Very hard questions hit the length limit, however, there is some success, in particular in *v3* and *v4*.
- In particular, among the 7 very-hard runs that finished, 6 were correct.

---


## 🔧 Technical Setup

```text
Model:              Aleph-Alpha/Kolibri-1
Reasoning effort:   high
Temperature:        1
Top-p:              0.97
Max output tokens:  32768
Runs per question:  5
```

---

## 📌 Disclaimer

This is a deliberately small, specialized benchmark focused on (higher) category theory and neighboring areas. It does not provide a universal benchmark, but only an analysis how the model performs with advanced mathematics.

## 🤝 Acknowledgements

Special thanks to [Niko Duerr](https://www.linkedin.com/in/nikoduerr/) from [Aleph Alpha](https://aleph-alpha.com/) and [Konark modi](https://www.linkedin.com/in/konarkmodi/) from [Tesseracted Labs](https://tesseracted.com/) for helping me get free API access to *Kolibri-1*.