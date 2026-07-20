# Public datasets (brief §9)

Real, working samples of the datasets the brief references, plus a reproducible
downloader. Run `python3 datasets/download_datasets.py` to (re)fetch everything.

| Dataset | Here | What's included | Used for |
|---|---|---|---|
| **A. CFPB Consumer Complaints** | `cfpb/complaints_sample.json` | 250 real complaints (product, issue, company, state, date, narrative) | Realistic text for the **Complaint agent**; routing/escalation eval |
| **B. Banking77** | `banking77/train.csv`, `test.csv`, `categories.json` | 10,003 train + 3,080 test utterances across **77 intents** | Benchmarking the **Intent-detection / router** |
| **C. DailyDialog** | `dailydialog/dialogues_sample.txt` | 3 sample multi-turn dialogues (`__eou__` = end of utterance) | Multi-turn **conversation-memory** testing |
| **D. SQuAD v2.0** | `squad/dev-v2.0.json` | Full dev set (35 topics, ~1,200 paragraphs, ~12k Q/A) | Evaluating **RAG retrieval + answer** quality |
| **E. MS MARCO** | `ms_marco/validation_sample.json` | 100 validation rows (query + passages + answers) | Semantic-retrieval sanity checks |

## Notes on the big ones
Two sources are far too large to vendor into the repo, so we ship a **sample** and
link the full download:

- **CFPB** updates daily and holds millions of complaints. The full database:
  https://www.consumerfinance.gov/data-research/consumer-complaints/
  (the downloader pulls a live sample via the search API).
- **MS MARCO** is tens of GB. Full set:
  https://github.com/microsoft/MSMARCO-Question-Answering
- **SQuAD** train (`train-v2.0.json`, ~40 MB) isn't vendored; grab it from
  https://raw.githubusercontent.com/rajpurkar/SQuAD-explorer/master/dataset/train-v2.0.json

## DailyDialog
The original host (`yanran.li`) is unreliable and the Hugging Face copies are now
**gated** (need `huggingface-cli login`). We ship a small format sample so the
pipeline has data. Full dataset:
- HF (gated): https://huggingface.co/datasets/daily_dialog
- XDailyDialog (multilingual): https://github.com/liuzeming01/XDailyDialog

## How these feed the project
The **live product** answers from the company knowledge base (`../knowledge_base/`).
These public datasets are for **evaluation and enrichment** — e.g. measuring intent
accuracy against Banking77, or stress-testing the complaint agent with real CFPB
narratives — which is exactly what the brief's §7 (Testing & Evaluation) rewards.
