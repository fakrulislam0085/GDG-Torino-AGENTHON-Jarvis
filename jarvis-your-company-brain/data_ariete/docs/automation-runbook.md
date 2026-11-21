---
id: doc-002
title: Automation runbook
acl: [tech]
updated: 2026-11-18
---
> Fictional scenario built on Ariete Tech Solutions' public services. Not Ariete's data.

# Automation runbook

- The document-intake pipeline reads PEC and email attachments, runs OCR and files each document in the right client pratica. If many files fail at once, check the OCR step first.
- Pipeline 2.4 drops scanned PDFs over 20 pages at the OCR step. Fixed in 2.5.
- Updates to a client's automation only in planned windows, with an engineer on site or on call and a rollback plan.
- Sensitive client files: open-weight model on the client's own server; everything else in an EU data centre (GDPR).
