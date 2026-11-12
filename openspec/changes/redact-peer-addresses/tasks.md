## 1. Redaction

- [x] 1.1 Redact with
      `ethos lane redact private-addresses --apply --key-stdin --authorize --expect-head <head>`;
      done when a fresh preview reports no occurrence. The apply at `e3666dd` replaced both
      occurrences; the redaction is committed alone as `243533e`, and the preview of that head
      reports no occurrence.
- [x] 1.2 Verify with
      `ethos lane redact private-addresses --verify --key-stdin --base <base> --head <head>`; done
      when ETHOS records the `redaction:private-peer` Attestation for the head. The verification of
      `243533e` from `e3666dd` re-derived both occurrences and recorded Attestation `617169ad`.
