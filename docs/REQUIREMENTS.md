# CropCover – Project Requirements

## 1. Functional Requirements

Functional requirements describe the main operations and features that the CropCover application must perform.

### FR-01: Crop Insurance Information

The system must provide information about PMFBY crop insurance coverage, eligibility, and applicable conditions.

**Acceptance Criteria:**
- Support at least 5 major crop categories.
- Provide information relevant to Tamil Nadu districts.
- Display the applicable season and notification.

### FR-02: Crop Damage Claim Guidance

The system must identify the potentially applicable claim category based on the farmer's crop damage situation.

**Acceptance Criteria:**
- Support at least 4 claim situations.
- Explain the applicable claim category.
- Provide the next steps for reporting damage.
- Include relevant official references.

### FR-03: Claim Deadline Information

The system must provide information about crop damage reporting deadlines.

**Acceptance Criteria:**
- Explain the applicable 72-hour intimation requirement where relevant.
- Display the deadline and applicable conditions.
- Provide the official source for verification.

### FR-04: Premium and Sum Insured Calculation

The system must retrieve and display crop insurance premium and sum insured values based on crop, district, and season.

**Acceptance Criteria:**
- Support at least 30 crop-district test cases.
- Achieve 100% accuracy against verified notification data.
- Display the premium amount and sum insured.
- Avoid displaying unverified financial values.

### FR-05: Official Source References

The system must provide references for important crop insurance information.

**Acceptance Criteria:**
- Provide at least one relevant official reference for each important insurance answer.
- Display the source document name.
- Include the relevant section, paragraph, or notification details wherever available.

---

## 2. Non-Functional Requirements

Non-functional requirements describe the quality, performance, security, and reliability of the application.

### NFR-01: Performance

The application should respond quickly to farmer queries.

**Acceptance Criteria:**
- API response time should be below 3 seconds for 95% of standard requests under the defined test load.
- Support at least 50 concurrent users during performance testing.

### NFR-02: Accuracy and Reliability

The application must provide accurate and trustworthy crop insurance information.

**Acceptance Criteria:**
- Achieve 100% accuracy for 30 verified premium and sum insured test cases.
- Achieve at least 90% accuracy for 30 claim classification scenarios.
- Avoid generating unsupported insurance information.

### NFR-03: Usability

The application should be simple and understandable for farmers.

**Acceptance Criteria:**
- Provide a simple and user-friendly interface.
- Keep important claim instructions within 5 steps wherever practical.
- Support mobile screen widths starting from 320 pixels.
- Use simple language for insurance explanations.

### NFR-04: Security

The application must protect user information and prevent unauthorized access.

**Acceptance Criteria:**
- Store sensitive configuration in environment variables.
- Never expose API keys or passwords in source code.
- Validate all user inputs.
- Use HTTPS when deployed publicly.

### NFR-05: Maintainability and Scalability

The application should be easy to maintain, test, and extend.

**Acceptance Criteria:**
- Maintain separate modules for API, business logic, and data processing.
- Use Pytest for automated testing.
- Use Ruff for code quality checks.
- Maintain at least 80% automated test coverage as a project target.

---

## 3. Requirement Summary

| Category | Requirement Count |
|---|---:|
| Functional Requirements | 5 |
| Non-Functional Requirements | 5 |
| Total Requirements | 10 |

## 4. Acceptance and Validation

The project will be considered ready for its initial evaluation when:

1. All 5 functional requirements have been implemented and tested.
2. All 5 non-functional requirements have measurable validation results.
3. All 30 crop-district test cases have verified premium and sum insured values.
4. Claim classification achieves at least 90% accuracy across 30 scenarios.
5. Important insurance answers contain official government references.

**Note:** These are project targets and acceptance criteria, not claims that the current application has already achieved them.
