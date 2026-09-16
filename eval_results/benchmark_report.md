# Antigravity `course-flake-generator` Evaluation Report

**Date:** 2026-09-16T00:41:55.360232  
**Status:** `COMPLETED`  
**Samples per Task ($n$):** 3  
**Completed Tasks:** 14  

## Overall Accuracy (pass@k)

| Metric | Score |
| :--- | :--- |
| **pass@1** | **92.86%** |
| **pass@3** | **100.00%** |

## Overall Performance Telemetry

| Metric | Mean per Trial |
| :--- | :--- |
| Duration (seconds) | 114.35s |
| Agent Turns | 1.0 |
| Total Tokens | 251,344 |
| Thinking Tokens | 3,486 |

## Task-Level Results

| Task # | Type | Task / Project Name | Successes ($c/n$) | 1 | 3 |
| :--- | :--- | :--- | :---: | :---: | :---: |
| 1 | greenfield | computer science | 3/3 | 100.0% | 100.0% |
| 2 | greenfield | computer science | 3/3 | 100.0% | 100.0% |
| 3 | greenfield | computer science | 3/3 | 100.0% | 100.0% |
| 4 | greenfield | computer science | 3/3 | 100.0% | 100.0% |
| 5 | greenfield | computer science | 2/3 | 66.7% | 100.0% |
| 6 | greenfield | computer science | 3/3 | 100.0% | 100.0% |
| 7 | greenfield | computer science | 3/3 | 100.0% | 100.0% |
| 8 | greenfield | computer science | 3/3 | 100.0% | 100.0% |
| 9 | greenfield | computer science | 3/3 | 100.0% | 100.0% |
| 10 | greenfield | computer science | 2/3 | 66.7% | 100.0% |
| 11 | greenfield | data science | 3/3 | 100.0% | 100.0% |
| 12 | greenfield | data science | 3/3 | 100.0% | 100.0% |
| 13 | greenfield | data science | 2/3 | 66.7% | 100.0% |
| 14 | greenfield | data science | 3/3 | 100.0% | 100.0% |

## Trial Details & Conversation Links

Use `agy --conversation <conversation_id>` to inspect or resume any trial.

| Task | Sample | Status | Duration | Turns | Tokens | Conversation ID | Notes |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| 1 | 1 | ✅ PASS | 100.2s | 1 | 264,128 | `5283d271-522c-4f6f-b1de-23efa27b63ed` | All checks passed |
| 1 | 2 | ✅ PASS | 86.6s | 1 | 232,958 | `e3f11fde-9054-41c1-8fba-dd5a9749bb7f` | All checks passed |
| 1 | 3 | ✅ PASS | 93.2s | 1 | 207,951 | `b7a70aed-4dbc-4c03-b2e2-bd0c3d4138bd` | All checks passed |
| 2 | 1 | ✅ PASS | 94.0s | 1 | 219,476 | `9d95cddc-9fcb-4144-9fc1-62f02724ac4f` | All checks passed |
| 2 | 2 | ✅ PASS | 131.9s | 1 | 253,664 | `1eb63276-a888-4809-bd2f-d279e3f3f9f8` | All checks passed |
| 2 | 3 | ✅ PASS | 1299.1s | 1 | 287,096 | `e238a68d-c411-44df-a490-f9a7db31d5fa` | All checks passed |
| 3 | 1 | ✅ PASS | 5.0s | 1 | 40,868 | `92e6f325-13b3-4f98-adf6-9c4115cf11dd` | All checks passed |
| 3 | 2 | ✅ PASS | 101.6s | 1 | 341,876 | `d15417ac-afff-46c2-bc6a-48f0290a0716` | All checks passed |
| 3 | 3 | ✅ PASS | 133.7s | 1 | 444,106 | `6ba4565a-50bb-44fc-9ee3-d76368d73be9` | All checks passed |
| 4 | 1 | ✅ PASS | 113.3s | 1 | 455,431 | `dc131233-a529-4a3e-b2ab-4eab93a91a66` | All checks passed |
| 4 | 2 | ✅ PASS | 2.8s | 1 | 13,278 | `7252c692-9727-41b3-949c-942632b5817f` | All checks passed |
| 4 | 3 | ✅ PASS | 26.4s | 1 | 162,958 | `0210c722-1529-499a-9abb-b8f7d438cc4d` | All checks passed |
| 5 | 1 | ✅ PASS | 47.0s | 1 | 244,732 | `7c4f454b-582d-4437-841b-8c340759c0a0` | All checks passed |
| 5 | 2 | ❌ FAIL | 32.4s | 1 | 150,533 | `63f0dd8c-fd10-4246-b182-c441a2702e7e` | No flake.nix was generated |
| 5 | 3 | ✅ PASS | 65.4s | 1 | 193,409 | `62bcae85-32b3-45b5-b74d-3534659e5e3f` | All checks passed |
| 6 | 1 | ✅ PASS | 1.2s | 1 | 13,251 | `88f32990-854d-4ea6-8c04-81ab306a7187` | All checks passed |
| 6 | 2 | ✅ PASS | 83.6s | 1 | 202,614 | `1be07b81-4c4c-4270-8d6a-0926e22ec1eb` | All checks passed |
| 6 | 3 | ✅ PASS | 164.0s | 1 | 349,768 | `4a5c31db-e81c-4053-a16f-0f0d8664054d` | All checks passed |
| 7 | 1 | ✅ PASS | 171.4s | 1 | 350,528 | `01e2886d-0e5d-452f-8146-dd6f8679d4b0` | All checks passed |
| 7 | 2 | ✅ PASS | 1.7s | 1 | 13,286 | `72a428e1-56f2-4517-be6c-17c30054087d` | All checks passed |
| 7 | 3 | ✅ PASS | 97.1s | 1 | 324,165 | `732097e2-8430-44c9-a168-50cb58688b82` | All checks passed |
| 8 | 1 | ✅ PASS | 103.2s | 1 | 216,260 | `a387d9e2-faab-4a5b-acfa-850214b4c7c8` | All checks passed |
| 8 | 2 | ✅ PASS | 90.6s | 1 | 218,416 | `8da3b1ae-7f5f-40dd-b800-f778b22cc02a` | All checks passed |
| 8 | 3 | ✅ PASS | 68.3s | 1 | 205,583 | `61f7e559-443e-49ec-b850-8a785a634d20` | All checks passed |
| 9 | 1 | ✅ PASS | 152.9s | 1 | 389,629 | `adc69e5b-0e8e-4398-a09a-d7d0639a3c95` | All checks passed |
| 9 | 2 | ✅ PASS | 119.6s | 1 | 314,729 | `154bbe18-51ba-49fd-bec5-09dfafa6fea8` | All checks passed |
| 9 | 3 | ✅ PASS | 27.3s | 1 | 110,957 | `57c7e487-898f-4f7a-897a-77f922cb8256` | All checks passed |
| 10 | 1 | ❌ FAIL | 112.6s | 1 | 301,724 | `0f4539b7-8d8e-4bea-9b6c-401682a396a2` | No flake.nix was generated |
| 10 | 2 | ✅ PASS | 48.9s | 1 | 217,135 | `e5324f2c-8aea-44d6-9423-cee6a204878b` | All checks passed |
| 10 | 3 | ✅ PASS | 81.5s | 1 | 241,051 | `3d802609-f3e9-4ed6-b3d6-0932e983d444` | All checks passed |
| 11 | 1 | ✅ PASS | 40.7s | 1 | 169,992 | `dc47a219-31d7-4809-8e43-694476037e36` | All checks passed |
| 11 | 2 | ✅ PASS | 35.3s | 1 | 125,197 | `85121186-6e80-46d5-ba41-75577f9e8247` | All checks passed |
| 11 | 3 | ✅ PASS | 35.7s | 1 | 166,695 | `78ffe947-7b8a-4bac-94fe-3518027d2290` | All checks passed |
| 12 | 1 | ✅ PASS | 106.4s | 1 | 387,313 | `ace558f6-0c59-4190-94af-08e02f5d9ea2` | All checks passed |
| 12 | 2 | ✅ PASS | 119.8s | 1 | 424,081 | `c368c743-7197-4d25-862f-b3ba1606b7d9` | All checks passed |
| 12 | 3 | ✅ PASS | 121.8s | 1 | 410,125 | `e64d2c83-51e7-43af-9ae5-ea9cfe4190a5` | All checks passed |
| 13 | 1 | ✅ PASS | 189.0s | 1 | 349,584 | `a11075e7-c70b-483b-a0d2-637d37c2a579` | All checks passed |
| 13 | 2 | ❌ FAIL | 46.3s | 1 | 179,073 | `2010c73a-88ec-4d0c-a77b-7dc4aee8e725` | No flake.nix was generated |
| 13 | 3 | ✅ PASS | 116.0s | 1 | 405,512 | `353aef2b-2357-4b36-9aa2-877fbba3f62d` | All checks passed |
| 14 | 1 | ✅ PASS | 157.3s | 1 | 445,111 | `9f072ccd-e04c-4593-a533-5bb192f3cc01` | All checks passed |
| 14 | 2 | ✅ PASS | 96.0s | 1 | 276,703 | `36155cde-94ee-4ad4-ae19-5a686905a6ec` | All checks passed |
| 14 | 3 | ✅ PASS | 81.7s | 1 | 235,488 | `10a60a32-8760-4fbe-9b6a-42bb1688dc26` | All checks passed |
