---
applyTo: "**/*.py"
---

# QA Check Instructions for Python Files

When editing Python files in this project:

## Pre-Edit Considerations
- Review the plan.md file to understand the intended functionality
- Ensure changes align with the project specifications

## During Editing
- Write code that matches the plan.md requirements
- Consider edge cases and error handling as specified

## Post-Edit Validation
- Run the QA/Tester agent to validate changes against plan.md
- Execute unit tests to ensure functionality works as expected
- Check for any breaking changes or regressions

## Automated Checks
Use the following agents for comprehensive validation:
- QA/Tester Agent: Validates implementation against plan.md and runs tests
- Python Code Review Agent: Checks for performance and code quality
- Python Linter Agent: Runs automated code quality checks

Always run QA validation before committing changes to critical files.