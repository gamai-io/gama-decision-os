# GAMA Decision OS — Enterprise License Agreement (template v1.0)

**IMPORTANT:** This is a commercial licence template, not legal advice. Both parties must have counsel review the executed agreement. The binding terms are those in the signed order form + this document.

**Licensor:** GAMA, Sarajevo, Bosnia and Herzegovina ("GAMA")
**Licensee:** the legal entity named in the order form ("Customer")
**Effective date:** the date of the order form or the licence key issuance, whichever is later.

---

## 1. Definitions

1.1 **"Software"** means the GAMA Decision OS Enterprise edition, including the enterprise-only modules, container images, licence validator, documentation and updates supplied by GAMA under this agreement.

1.2 **"Core"** means the Apache-2.0 licensed components published at the public repository. Core is governed solely by Apache-2.0, not by this agreement.

1.3 **"Node"** means one physical or virtual machine running the Software in a production environment. Development, test and staging environments do not count.

1.4 **"Licence Key"** means the signed, machine-readable token issued by GAMA that enables the Software for a defined tier, node count and term.

1.5 **"Order Form"** means the GAMA document specifying tier, node count, term, fees and add-ons.

---

## 2. Licence grant

2.1 Subject to payment and compliance with this agreement, GAMA grants Customer a **non-exclusive, non-transferable, non-sublicensable, time-limited** right to install and use the Software on the licensed number of Nodes, for Customer's internal business purposes, during the term.

2.2 Customer may make a reasonable number of backup copies and run the Software in a disaster-recovery site, provided the total concurrent production Nodes do not exceed the licensed count.

2.3 Affiliates controlled by Customer (≥50% ownership) may use the Software under this agreement if listed in the Order Form. Customer remains liable for their compliance.

2.4 **No rights are granted by implication.** All rights not expressly granted are reserved by GAMA.

---

## 3. Restrictions

Customer shall not, and shall not permit any third party to:

(a) copy, modify, translate or create derivative works of the enterprise-only Software, except as expressly permitted in writing by GAMA;
(b) reverse engineer, decompile or disassemble the enterprise-only Software, except to the extent permitted by mandatory applicable law (and then only after written notice to GAMA);
(c) remove, obscure or circumvent any licence key, feature flag, copyright or proprietary notice;
(d) rent, lease, lend, sell, resell, sublicense, distribute or provide the enterprise-only Software as a service to third parties, unless a separate OEM/partner agreement is signed;
(e) use the Software to build a competing agent control plane, or to train a competing model on GAMA's proprietary outputs, without written permission;
(f) publish benchmarks of the enterprise-only Software without GAMA's prior written consent, except that Customer may share results internally and with its auditors;
(g) use the Software in violation of applicable law, including sanctions and export-control law.

**Clarification:** Restrictions (a)–(f) apply only to enterprise-only components. Customer's rights to the Apache-2.0 Core are not restricted by this agreement.

---

## 4. Licence keys, delivery and verification

4.1 GAMA issues Licence Keys bound to Customer, tier, node count and expiry. Keys are validated offline by the Software using GAMA's public key.

4.2 Customer shall keep keys confidential and shall not publish them. Customer is responsible for use of keys issued to it.

4.3 The Software may produce a local, aggregated usage record (node count, version, dates) to support compliance. It does **not** transmit customer data, prompts, evidence content or telemetry to GAMA. If Customer enables optional telemetry, it is documented and can be disabled.

4.4 On expiry, the Software enters a 30-day read-only grace period. GAMA will not remotely disable the Software or delete Customer data.

---

## 5. Support, SLA and updates

5.1 Support and SLA are as stated in the Order Form. If no SLA is stated, Enterprise support is business-hours e-mail with a 1-business-day response target, and no availability guarantee applies.

5.2 GAMA provides updates and security patches for the supported major version for 12 months after the next major release. Customer may decline updates; GAMA is not liable for issues fixed in a declined update.

5.3 Onboarding, custom connectors and training are separate deliverables and are only included if listed in the Order Form.

---

## 6. Fees, taxes and payment

6.1 Fees are stated in the Order Form and exclude VAT and other applicable taxes, which Customer pays (excluding taxes on GAMA's income).

6.2 Unless stated otherwise: annual fees are invoiced in advance; monthly fees are invoiced monthly in advance. Payment is due within 15 days.

6.3 Late amounts accrue interest at 1% per month or the maximum permitted by law, whichever is lower. GAMA may suspend the licence after 15 days' written notice of non-payment. Suspension does not relieve Customer of accrued fees.

6.4 Fees are non-refundable except as expressly stated in Section 10 (warranty) or required by law.

---

## 7. Confidentiality

7.1 Each party protects the other's confidential information with at least reasonable care and uses it only to perform this agreement, for the term and 3 years after.

7.2 Confidential information does not include information that is public without breach, independently developed, or lawfully received from a third party without duty of confidence.

7.3 Disclosure required by law is permitted after prompt notice, limited to what is legally required.

---

## 8. Intellectual property

8.1 GAMA and its licensors own all rights in the Software, including enterprise-only modules, documentation and trademarks. Customer owns its data, prompts, configurations and evidence content.

8.2 Customer grants GAMA a limited licence to use Customer's feedback to improve the Software, without identifying Customer.

8.3 If Customer provides a custom connector or patch, Customer grants GAMA a perpetual, irrevocable, royalty-free licence to use it in the Software, unless the Order Form states otherwise.

---

## 9. Data protection

9.1 Each party complies with applicable data protection law, including GDPR where applicable.

9.2 The Software is self-hosted. Customer is the controller of data processed through the Software. GAMA acts as processor only if it accesses Customer systems for support, and then only under the DPA referenced in the Order Form.

9.3 GAMA will not access Customer production data without a written support request or an executed DPA.

---

## 10. Warranty and remedies

10.1 GAMA warrants that, for 30 days after delivery, the Software will materially conform to its documentation when used as intended.

10.2 Customer's exclusive remedy for breach of 10.1 is repair, replacement or, if neither is commercially reasonable, a refund of fees paid for the affected term.

10.3 **Except as stated in 10.1, the Software is provided "AS IS".** GAMA disclaims all other warranties, express or implied, including merchantability, fitness for a particular purpose, title and non-infringement, to the maximum extent permitted by law.

10.4 GAMA does not warrant that the Software will detect every unsafe agent action. The Software is a control layer, not a guarantee of correctness or legal compliance. Customer remains responsible for its agents, decisions and regulatory obligations.

---

## 11. Limitation of liability

11.1 Neither party is liable for indirect, incidental, special, consequential or punitive damages, or for lost profits, revenue, data or goodwill, even if advised of the possibility.

11.2 Each party's total aggregate liability under this agreement is limited to the fees paid or payable by Customer in the **12 months** preceding the event giving rise to the claim.

11.3 The cap in 11.2 does not apply to: (a) Customer's payment obligations; (b) breach of Section 3 (Restrictions) or Section 7 (Confidentiality); (c) either party's fraud or wilful misconduct; or (d) liability that cannot be limited by law.

11.4 This allocation of risk is an essential basis of the bargain and applies even if a remedy fails of its essential purpose.

---

## 12. Indemnification

12.1 GAMA will defend Customer against a third-party claim that the enterprise-only Software infringes a patent, copyright or trade secret, and pay resulting damages finally awarded, provided Customer promptly notifies GAMA, gives control of the defence, and cooperates.

12.2 GAMA has no obligation for claims arising from: modifications not made by GAMA, combination with non-GAMA products, use contrary to documentation, or the Apache-2.0 Core.

12.3 If an injunction is likely, GAMA may procure the right, replace or modify the Software, or terminate and refund prepaid unused fees.

---

## 13. Term and termination

13.1 The term is stated in the Order Form and renews for equal periods unless either party gives 30 days' written notice before renewal.

13.2 Either party may terminate for material breach not cured within 30 days of written notice, or immediately on insolvency.

13.3 On termination, Customer must stop using enterprise-only components and destroy or return Licence Keys. Customer may retain and export its own data and evidence. Core may continue under Apache-2.0.

13.4 Sections 3, 6, 7, 8, 10.3–10.4, 11, 12 and 14 survive termination.

---

## 14. Governing law and disputes

14.1 This agreement is governed by the laws of Bosnia and Herzegovina, excluding its conflict-of-law rules and the CISG.

14.2 The courts of Sarajevo have exclusive jurisdiction, unless the Order Form specifies arbitration (then ICC rules, seat Sarajevo, language English).

14.3 Before litigation, the parties will attempt good-faith resolution for 30 days through senior representatives.

---

## 15. General

15.1 **Entire agreement.** This agreement + Order Form + DPA (if any) is the entire agreement and supersedes prior discussions.

15.2 **Order of precedence:** Order Form → DPA → this agreement.

15.3 **Assignment.** Customer may not assign without GAMA's written consent, except to a successor in a merger or sale of substantially all assets, provided the successor assumes all obligations.

15.4 **Severability.** If a provision is unenforceable, it is modified to the minimum extent necessary; the rest remains in effect.

15.5 **No waiver.** Failure to enforce is not a waiver.

15.6 **Force majeure.** Neither party is liable for delay caused by events beyond reasonable control, except payment obligations.

15.7 **Notices** must be in writing to the addresses in the Order Form and are effective on delivery (e-mail with confirmation).

15.8 **Publicity.** GAMA may name Customer as a customer only with prior written consent.

---

**Contact:** legal@gamai.io · GAMA, Sarajevo, Bosnia and Herzegovina
