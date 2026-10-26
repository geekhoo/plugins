Semantic mutations of compact-report.md; expected decisions are walkthroughs, not an executable report parser or paid judge output.

| Variant | Concrete mutation / retained source evidence | Expected criteria and decision |
|---|---|---|
| R1 omitted numeric tests | Replace final-tests sentence with “Tests pass; see docs/example/test-output.txt.” | C2 fails (no final numbers); reject even if all other criteria hold. |
| R2 omitted commits | Remove the “Commits made” and “Final revision” sentence and the two IDs in the preceding hash-support sentence. | C3 fails (neither commit IDs nor subjects); reject. |
| R3 unsupported PASS | Replace impl-review evidence cell with “See review-impl.md.” | C5 fails: linked artifact alone supplies no basis in the output text for PASS; reject. |
| R4 unreached stage hidden | Source fixture state says impl-review was never dispatched; report still claims impl-review PASS. | C1/C5 fail: the stage was not reached and cannot have current supporting reviewer evidence; reject. An honest unreached row with overall incomplete is the valid disclosure. |
| R5 links alone | Retain stage names and artifact paths; replace each outcome/support with “See artifact”; remove numeric tests, commit and disclosure paragraphs. | C1–C5 fail; reject. |
| R6 unaddressed required warning | Source domain data-E labels a violated mandatory AC as “warning”; report still says Overall PASS. | C5 fails; requirement remains unproved regardless of label. Consolidation must be NEEDS FIXES. |

R4's contradiction is assessed against its declared synthetic source state. Text alone cannot prove a fabricated reviewer claim false; this walkthrough does not claim automated detection or calibrated judge accuracy.
