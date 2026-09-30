# Antigravity `course-flake-generator` Evaluation Report

**Date:** 2026-09-29T00:18:40.454322  
**Status:** `COMPLETED`  
**Execution Command:** `python3 evaluate_pass_at_k.py`  
**Samples per Task ($n$):** 3  
**Completed Tasks:** 14  

### Execution Arguments & Configuration

| Parameter | Value |
| :--- | :--- |
| **Inputs** | `input/nl_instruction_inputs.jsonl` |
| **Samples ($n$)** | `3` |
| **$k$ Values** | `[1, 3]` |
| **Output Directory** | `/Users/luis/Code/Thesis_Implementation/eval_results` |
| **Run Directory** | `/Users/luis/Code/Thesis_Implementation/eval_results/20260929_001840` |
| **Task Filter** | `task_index=None, num_tasks=None, start_index=0` |
| **Model Override** | `None (default)` |
| **Print Timeout** | `15m0s` |
| **Keep Scratch** | `False` |

## Overall Accuracy (pass@k)

| Metric | Score |
| :--- | :--- |
| **pass@1** | **97.62%** |
| **pass@3** | **100.00%** |

## Overall Performance Telemetry

| Metric | Mean per Trial |
| :--- | :--- |
| Duration (seconds) | 324.61s |
| Agent Turns | 1.0 |
| Total Tokens | 228,882 |
| Thinking Tokens | 5,271 |

## Task-Level Results

| Task # | Type | Task / Project Name | Successes ($c/n$) | 1 | 3 |
| :--- | :--- | :--- | :---: | :---: | :---: |
| 1 | greenfield | computer science | 3/3 | 100.0% | 100.0% |
| 2 | greenfield | computer science | 3/3 | 100.0% | 100.0% |
| 3 | greenfield | computer science | 3/3 | 100.0% | 100.0% |
| 4 | greenfield | computer science | 3/3 | 100.0% | 100.0% |
| 5 | greenfield | computer science | 3/3 | 100.0% | 100.0% |
| 6 | greenfield | computer science | 3/3 | 100.0% | 100.0% |
| 7 | greenfield | computer science | 3/3 | 100.0% | 100.0% |
| 8 | greenfield | computer science | 3/3 | 100.0% | 100.0% |
| 9 | greenfield | computer science | 3/3 | 100.0% | 100.0% |
| 10 | greenfield | computer science | 3/3 | 100.0% | 100.0% |
| 11 | greenfield | data science | 3/3 | 100.0% | 100.0% |
| 12 | greenfield | data science | 3/3 | 100.0% | 100.0% |
| 13 | greenfield | data science | 3/3 | 100.0% | 100.0% |
| 14 | greenfield | data science | 2/3 | 66.7% | 100.0% |

## Trial Details & Conversation Links

Use `agy --conversation <conversation_id>` to inspect or resume any trial.

| Task | Sample | Status | Duration | Turns | Tokens | Conversation ID | Notes |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| 1 | 1 | ✅ PASS | 136.7s | 1 | 170,549 | `d2eba945-eac3-40e5-b0b5-ca4b3f9035f5` | All checks passed |
| 1 | 2 | ✅ PASS | 98.6s | 1 | 192,874 | `963b2ac4-c0f8-4d2c-87e8-88ab8ee6954a` | All checks passed |
| 1 | 3 | ✅ PASS | 112.3s | 1 | 253,139 | `0c34da39-d713-4205-97f1-c08b43867577` | All checks passed |
| 2 | 1 | ✅ PASS | 357.7s | 1 | 286,896 | `8ee4908b-5451-4827-9443-d21b73f6f4a2` | All checks passed |
| 2 | 2 | ✅ PASS | 232.7s | 1 | 329,350 | `85f88955-4082-4229-83d8-8b0320d37a49` | All checks passed |
| 2 | 3 | ✅ PASS | 116.8s | 1 | 167,573 | `4a7d6c6f-57f8-477f-995a-94d2c0d9d8a7` | All checks passed |
| 3 | 1 | ✅ PASS | 126.3s | 1 | 164,220 | `26e71631-51a4-4025-a92b-5d88a52a847c` | All checks passed |
| 3 | 2 | ✅ PASS | 141.9s | 1 | 190,693 | `a982d248-04ab-41fe-86a7-0da42a110559` | All checks passed |
| 3 | 3 | ✅ PASS | 133.8s | 1 | 216,493 | `d30bce88-6374-4c9f-8d87-ca1124eda9ad` | All checks passed |
| 4 | 1 | ✅ PASS | 146.7s | 1 | 190,143 | `10bfa0d2-abb7-4289-8c21-2af39496a927` | All checks passed |
| 4 | 2 | ✅ PASS | 135.6s | 1 | 180,786 | `2ac6c7a7-f4cf-4e2e-bddb-583810fbfc4b` | All checks passed |
| 4 | 3 | ✅ PASS | 71.5s | 1 | 125,481 | `71464dd2-0ebd-40f3-84ae-58bdb03771ab` | All checks passed |
| 5 | 1 | ✅ PASS | 98.1s | 1 | 164,533 | `b3f31dce-9a60-4a1a-937f-2501a35de4fb` | All checks passed |
| 5 | 2 | ✅ PASS | 93.6s | 1 | 148,483 | `fce36c22-af5d-45e2-b310-7ccecbc3ab6f` | All checks passed |
| 5 | 3 | ✅ PASS | 75.9s | 1 | 147,705 | `46baca55-c97b-432d-be13-6b6dc14adaaf` | All checks passed |
| 6 | 1 | ✅ PASS | 256.6s | 1 | 320,887 | `20f507fa-ef5f-489a-9cc1-35af10ac2f30` | All checks passed |
| 6 | 2 | ✅ PASS | 211.4s | 1 | 223,164 | `bd5281ae-37aa-40e5-8c2b-8848692b84d8` | All checks passed |
| 6 | 3 | ✅ PASS | 263.5s | 1 | 293,610 | `012e3de6-3f81-4228-af1c-a4d04e5e071a` | All checks passed |
| 7 | 1 | ✅ PASS | 183.1s | 1 | 241,089 | `c133fb32-7064-41cb-9ace-3594a3c06472` | All checks passed |
| 7 | 2 | ✅ PASS | 175.4s | 1 | 253,489 | `4274e691-5790-40b8-97a3-e9e1f3aab6e3` | All checks passed |
| 7 | 3 | ✅ PASS | 200.4s | 1 | 215,357 | `de8eddf9-3264-4c33-9e6a-b281fe3c54e6` | All checks passed |
| 8 | 1 | ✅ PASS | 149.8s | 1 | 244,011 | `c1cbfb74-2644-47c5-b826-07143e71a0d4` | All checks passed |
| 8 | 2 | ✅ PASS | 210.4s | 1 | 228,006 | `92a06ea3-3c76-426d-8d49-c71ba1ddba81` | All checks passed |
| 8 | 3 | ✅ PASS | 129.9s | 1 | 200,797 | `cc23633f-ceef-4437-986b-1b5def761900` | All checks passed |
| 9 | 1 | ✅ PASS | 179.2s | 1 | 254,743 | `7556c90b-193b-4f5f-8406-fe80f0bff7ad` | All checks passed |
| 9 | 2 | ✅ PASS | 239.5s | 1 | 235,779 | `6e2aadbd-6777-4b76-8355-84dd9fe14f10` | All checks passed |
| 9 | 3 | ✅ PASS | 100.4s | 1 | 171,111 | `b8cfa4d4-5983-4cb4-bd6f-4c6abb69b998` | All checks passed |
| 10 | 1 | ✅ PASS | 183.0s | 1 | 234,736 | `39cf20c6-4b27-4a9f-ace8-0fa744ca3476` | All checks passed |
| 10 | 2 | ✅ PASS | 120.8s | 1 | 143,172 | `cd0e7332-00b2-423d-a25d-ebb92dedf647` | All checks passed |
| 10 | 3 | ✅ PASS | 93.9s | 1 | 160,708 | `e8d037c0-1a93-4efb-a45a-81b72a04f40e` | All checks passed |
| 11 | 1 | ✅ PASS | 106.7s | 1 | 137,330 | `8632504c-a2e2-49e2-aa5d-497f5b479f07` | All checks passed |
| 11 | 2 | ✅ PASS | 74.7s | 1 | 136,476 | `b665597e-42cc-4378-a755-7d2eee9bf99c` | All checks passed |
| 11 | 3 | ✅ PASS | 62.6s | 1 | 133,605 | `653205e1-ea93-4e1f-9c7e-2d3e2e927091` | All checks passed |
| 12 | 1 | ✅ PASS | 399.1s | 1 | 443,255 | `c5160a11-b84b-436a-a0d7-eb58832e559e` | All checks passed |
| 12 | 2 | ✅ PASS | 1190.0s | 1 | 574,941 | `8e05bcad-db67-4918-a4c7-76f6790fc98a` | All checks passed |
| 12 | 3 | ✅ PASS | 3244.4s | 1 | 465,145 | `eb35c6a1-0add-4dbe-988e-5f78f90c54e9` | All checks passed |
| 13 | 1 | ✅ PASS | 1750.4s | 1 | 264,573 | `52753766-2cc7-44c4-86cc-659f6819398e` | All checks passed |
| 13 | 2 | ✅ PASS | 794.2s | 1 | 215,237 | `9a7ab34d-a301-4068-97b8-4bbdf79670ed` | All checks passed |
| 13 | 3 | ✅ PASS | 606.5s | 1 | 214,356 | `f909bb91-8ee7-4593-8be1-386f4a9ff074` | All checks passed |
| 14 | 1 | ✅ PASS | 265.0s | 1 | 279,287 | `bb1f264e-32ec-4b12-aa9c-4aa22db7b85a` | All checks passed |
| 14 | 2 | ❌ FAIL | 233.9s | 1 | 227,325 | `3949f631-77c9-4094-bc96-4851c411bbff` | sample_01: Missing tools in devShell: mysql-workbench |
| 14 | 3 | ✅ PASS | 130.7s | 1 | 171,954 | `33eccdda-e9e2-41cc-a6ff-46ea0185d02c` | All checks passed |
