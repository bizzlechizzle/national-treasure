# National Treasure Complete Work Checklist

> **Target**: Production-Ready v1.0.0
> **Standard**: A+ / 100 / 100
> **Created**: 2024-12-25

---

## Pre-Flight Checks

### Environment Setup
- [ ] Python 3.11+ available
- [ ] Virtual environment created: `python3.11 -m venv .venv`
- [ ] Package installed: `pip install -e ".[dev]"`
- [ ] Playwright installed: `playwright install chromium`
- [ ] Database initialized: `nt db init`

### Repository Status
- [ ] Clean git status (no uncommitted changes)
- [ ] On `main` branch
- [ ] All dependencies up to date

---

## Phase 1: Critical Fixes

### 1.1 Test Environment
- [ ] Update `pyproject.toml` with correct pytest-asyncio config
- [ ] Fix import errors in test files
- [ ] Verify `pytest tests/unit/ -v` runs without errors
- [ ] All 78 tests passing

### 1.2 Deprecated Code
- [ ] Replace `datetime.utcnow()` in `learning/domain.py`
- [ ] Replace `datetime.utcnow()` in `queue/service.py`
- [ ] Replace `datetime.utcnow()` in `core/models.py`
- [ ] Add `from datetime import UTC` imports

### 1.3 Job Queue Safety
- [ ] Add job lease timeout (30 min default)
- [ ] Add stale job recovery on startup
- [ ] Test orphaned job recovery

---

## Phase 2: Test Coverage

### 2.1 Fix Existing Tests
- [ ] `test_behaviors.py` - All passing
- [ ] `test_database.py` - All passing
- [ ] `test_learning.py` - All passing
- [ ] `test_models.py` - All passing
- [ ] `test_progress.py` - All passing
- [ ] `test_queue.py` - All passing
- [ ] `test_training.py` - All passing
- [ ] `test_validator.py` - All passing

### 2.2 Integration Tests
- [ ] Create `tests/integration/` directory
- [ ] `test_capture.py` - Basic capture workflow
- [ ] `test_capture.py` - Bot detection handling
- [ ] `test_capture.py` - Multiple formats
- [ ] `test_queue.py` - End-to-end job processing
- [ ] `test_learning.py` - Domain learning integration

### 2.3 CLI Tests
- [ ] Create `tests/integration/test_cli.py`
- [ ] Test `nt capture url` command
- [ ] Test `nt queue add` command
- [ ] Test `nt queue status` command
- [ ] Test `nt learning insights` command
- [ ] Test `nt db init` command

### 2.4 Coverage Target
- [ ] Run `pytest --cov=national_treasure`
- [ ] Achieve 70%+ coverage
- [ ] No untested critical paths

---

## Phase 3: Missing Features

### 3.1 WARC Generation
- [ ] Create `services/capture/warc.py`
- [ ] Implement wget-based capture
- [ ] Add CDP fallback method
- [ ] Add WARC to capture formats
- [ ] Test WARC generation
- [ ] Update CLI to support WARC

### 3.2 Image Discovery
- [ ] Create `services/image/discovery.py`
- [ ] Implement img tag extraction
- [ ] Implement srcset parsing
- [ ] Implement Open Graph extraction
- [ ] Implement Schema.org extraction
- [ ] Implement data-* attribute extraction
- [ ] Test image discovery

### 3.3 Image Enhancement
- [ ] Create `services/image/enhancement.py`
- [ ] Implement URL suffix stripping
- [ ] Implement CDN pattern recognition
- [ ] Implement quality comparison
- [ ] Test image enhancement

---

## Phase 4: Edge Case Handling

### 4.1 Error Handling
- [ ] Add timeout to page behaviors
- [ ] Fix worker exception swallowing
- [ ] Add proper error logging
- [ ] Add error classification

### 4.2 Resilience
- [ ] Implement circuit breaker for domains
- [ ] Add max queue depth limit
- [ ] Add domain blacklist support
- [ ] Implement graceful shutdown

### 4.3 Resource Management
- [ ] Remove global `_db` state
- [ ] Use dependency injection
- [ ] Add connection pooling if needed
- [ ] Add memory monitoring

---

## Phase 5: Code Quality

### 5.1 Linting
- [ ] Run `ruff check .`
- [ ] Fix all linting errors
- [ ] Run `ruff format .`
- [ ] No formatting issues

### 5.2 Type Checking
- [ ] Run `mypy src/`
- [ ] Fix all type errors
- [ ] Add missing type hints
- [ ] No mypy warnings

### 5.3 Code Review
- [ ] Review all services for patterns
- [ ] Verify consistent error handling
- [ ] Check for magic numbers
- [ ] Verify no hardcoded values

---

## Phase 6: Documentation

### 6.1 README.md Update
- [ ] Verify installation instructions
- [ ] Add troubleshooting section
- [ ] Verify all CLI commands documented
- [ ] Add quick start example

### 6.2 Developer Guide
- [ ] Verify DEVELOPER.md is current
- [ ] Add architecture diagram
- [ ] Document all services
- [ ] Add contribution guide

### 6.3 API Documentation
- [ ] Create `docs/api.md`
- [ ] Document public classes
- [ ] Document configuration
- [ ] Add usage examples

### 6.4 Examples
- [ ] Create `examples/basic_capture.py`
- [ ] Create `examples/batch_processing.py`
- [ ] Create `examples/learning_insights.py`
- [ ] Verify examples run correctly

---

## Phase 7: Security Audit

### 7.1 Input Validation
- [ ] Verify URL validation
- [ ] Verify file path validation
- [ ] Check for command injection
- [ ] Check for path traversal

### 7.2 Data Handling
- [ ] No secrets in logs
- [ ] No hardcoded credentials
- [ ] Proper cookie handling
- [ ] Secure file permissions

### 7.3 Dependencies
- [ ] Run `pip audit` or `safety check`
- [ ] Update vulnerable dependencies
- [ ] Lock dependency versions

---

## Phase 8: Performance

### 8.1 Benchmarking
- [ ] Measure single capture time
- [ ] Measure batch capture throughput
- [ ] Measure queue processing rate
- [ ] Document baseline metrics

### 8.2 Optimization
- [ ] Profile hot paths
- [ ] Optimize database queries
- [ ] Add caching where beneficial
- [ ] Test concurrent operations

---

## Phase 9: Final Verification

### 9.1 Full Test Suite
- [ ] `pytest tests/ -v` - All passing
- [ ] `pytest tests/ --cov` - 70%+ coverage
- [ ] No warnings in output

### 9.2 Lint and Type Check
- [ ] `ruff check .` - No errors
- [ ] `mypy src/` - No errors

### 9.3 Build Verification
- [ ] `pip install -e .` - Success
- [ ] `nt --version` - Correct version
- [ ] `nt capture url https://example.com` - Works

### 9.4 Documentation Review
- [ ] README.md accurate
- [ ] All commands documented
- [ ] Examples work

---

## Phase 10: Release

### 10.1 Version Bump
- [ ] Update VERSION to 1.0.0
- [ ] Update `__init__.py` version
- [ ] Update CHANGELOG.md

### 10.2 Git Operations
- [ ] All changes committed
- [ ] Meaningful commit messages
- [ ] No secrets in history
- [ ] Push to remote

### 10.3 Release Notes
- [ ] Document breaking changes
- [ ] List new features
- [ ] List bug fixes
- [ ] Thank contributors

---

## Acceptance Criteria

### Code Quality: A+
- [ ] All tests passing
- [ ] 70%+ coverage
- [ ] No linting errors
- [ ] No type errors
- [ ] Clean code patterns

### Functionality: 100%
- [ ] All CLI commands work
- [ ] All capture formats work
- [ ] Learning system works
- [ ] Queue system works
- [ ] All documented features implemented

### Documentation: 100%
- [ ] README complete
- [ ] Developer guide complete
- [ ] API documented
- [ ] Examples provided
- [ ] Troubleshooting documented

### Security: Pass
- [ ] No vulnerabilities
- [ ] Proper input validation
- [ ] No secrets exposed
- [ ] Dependencies audited

---

## Sign-Off

| Phase | Status | Reviewer | Date |
|-------|--------|----------|------|
| Critical Fixes | ⬜ | | |
| Test Coverage | ⬜ | | |
| Missing Features | ⬜ | | |
| Edge Cases | ⬜ | | |
| Code Quality | ⬜ | | |
| Documentation | ⬜ | | |
| Security | ⬜ | | |
| Performance | ⬜ | | |
| Final Verification | ⬜ | | |
| Release | ⬜ | | |

**Legend**: ⬜ Not Started | 🔄 In Progress | ✅ Complete | ❌ Blocked
