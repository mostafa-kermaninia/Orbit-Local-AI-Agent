# Contributing to ORBIT

Contributions that improve reliability, documentation, tests, accessibility, or the teaching value of the project are welcome.

## Development setup

```powershell
git clone https://github.com/mostafa-kermaninia/Orbit-Local-AI-Agent.git
cd Orbit-Local-AI-Agent

py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

## Before opening a pull request

Run:

```powershell
python -m compileall -q assistant tools ui scripts main.py
python -m pytest -q
```

Keep changes focused. Avoid unrelated formatting churn in the same pull request.

## Contribution rules

By submitting a contribution, you confirm that you have the right to license the contributed code under the repository's MIT License.

Do not submit:

- copied code with unknown or incompatible licensing;
- secrets or personal data;
- model weights;
- proprietary assets;
- changes that silently add arbitrary shell execution;
- web tooling intended to bypass login/paywall/CAPTCHA protections.

## Pull request checklist

- [ ] The change has a clear purpose.
- [ ] Existing behavior is preserved unless the PR explicitly changes it.
- [ ] Relevant tests were added or updated.
- [ ] `pytest` passes locally.
- [ ] Documentation/config examples were updated if behavior changed.
- [ ] No credentials or personal data are included.
- [ ] Third-party dependencies/assets have compatible licensing.

For large architecture changes, open a discussion first.
