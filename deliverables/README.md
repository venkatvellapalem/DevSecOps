# Deliverables

Presentation and teaching materials for Project 15.

| File | What it is |
|---|---|
| `DevSecOps_Secure_Pipeline.pptx` | 22-slide deck, 16:9, with speaker notes on every slide |
| `project_build_guide.docx` | Step-by-step build guide, phase by phase |
| `project_student_guide.docx` | Every concept and term in plain language |
| `project_student_worksheet.docx` | 100-mark assessment, five sections |
| `project_student_worksheet_solutions.docx` | Model answers, question for question |
| `diagrams/` | The six diagrams, as PNGs you can reuse |
| `build/` | The scripts that generate all of the above |

Everything here is generated, not hand-assembled, so it is reproducible and stays
in sync if the project changes:

```bash
python deliverables/build/make_diagrams.py   # the six PNGs
python deliverables/build/make_deck.py       # the pptx
python deliverables/build/make_docs.py       # build guide + student guide
python deliverables/build/make_worksheet.py  # worksheet + solutions
```

Requires `python-pptx` and `python-docx`. The diagrams use Pillow only.
