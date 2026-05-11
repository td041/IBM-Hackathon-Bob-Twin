# Bob's Twin — Audit Report

**Run ID:** `3d46f87a`  
**Generated:** 2026-05-11T13:04:29Z  
**Equivalence Score:** 1.0  

---

## Executive Summary

Migration PASSED. 34 of 34 interactions matched. Equivalence score: 1.0.

---

## Capture Phase

- **Cassette:** `golden_cassettes\run_3d46f87a.yaml`
- **Cassette SHA-256:** `sha256:5596bb4cf47c5c4a46f30833108e4aebfeaabd9503428c8129c5b1302409db91`
- **Interactions:** 34
- **Captured at:** 2026-05-11T13:03:46.911Z

**Endpoints covered:**

- `POST /admin/reset`
- `GET /health`
- `GET /users`
- `POST /users`
- `PUT /users/1`
- `PUT /users/2`
- `PUT /users/3`
- `GET /users/1/orders`
- `GET /users/2/orders`
- `DELETE /users/7`
- `DELETE /users/8`
- `DELETE /users/9`
- `GET /users/1`
- `GET /users/2`
- `GET /users/3`
- `POST /orders/calculate`
- `POST /products/tags`
- `POST /reviews/bulk`

---

## Replay Phase

| Metric | Value |
|--------|-------|
| Equivalence score | 1.0 |
| Passed | 34 |
| Failed | 0 |
| Total | 34 |
| Tolerance rules applied | 0 |

---

## Hash Chain

| Index | Phase | Timestamp | This Hash |
|-------|-------|-----------|-----------|
| 0 | capture | 2026-05-11T13:03:46.911Z | `sha256:3aff7d59d3871...` |
| 1 | replay | 2026-05-11T13:04:04.576Z | `sha256:02861dfe4d8e6...` |
| 2 | replay | 2026-05-11T13:04:14.335Z | `sha256:ae6c67e43a92a...` |
| 3 | replay | 2026-05-11T13:04:24.083Z | `sha256:11f23b9ba08fd...` |

---

## Footer

Licensed under Apache 2.0. Tool: Bob's Twin v0.1.0. Generated: 2026-05-11T13:04:29Z.
