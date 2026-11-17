# Prior Art and Opportunity for Verity: Documentation and Instruction Drift Verification

## Executive summary: the core opportunity is automatic inference, not another claim language

Verity is best understood as a **claim-extraction and evidence-correlation layer**, not as a sixth link checker or a generic documentation linter. Its credible differentiator is the ability to inspect a repository, infer candidate claims from Markdown, CI configuration, Dockerfiles, Makefiles, configuration files and shell scripts, and then resolve each candidate against the actual repository. This is broader than the tools developers already use, but it is not an unoccupied space. An npm package named `@pietro-falco/verity` already provides deterministic, offline verification of explicitly declared `file_exists`, `file_matches`, `git_committed` and `command` claims, with pass/fail output and optional JSON reporting [1]. The proposed product would therefore not be novel merely because it verifies claims without a network connection. Its novelty must come from zero-config inference, cross-artifact correlation and evidence provenance.

Existing tools solve pieces of the problem. Lychee checks URLs and mail addresses, including in offline mode, but treats a valid local relative link as the end of its investigation rather than asking whether the referenced path, build command or configuration key still means what the documentation claims [2]. mdBook, pytest and rustdoc execute examples rather than validating identifiers, paths and configuration references found in prose [3]. actionlint validates GitHub Actions syntax and expressions, while check-jsonschema validates files against schemas; neither connects a `README` instruction to the workflow, Dockerfile or Makefile that supposedly implements it [4][5]. Architecture tools such as dependency-cruiser, ArchUnit and import-linter similarly impose user-authored rules rather than discovering undocumented drift between instructions and implementation [6][7].

The strongest conclusion is therefore conditional. **No surveyed single tool delivers the full integrated scope**, particularly zero-config, offline, language-agnostic extraction of paths, commands, flags, environment variables, configuration keys, ports, code symbols and version pins followed by evidence-backed drift reporting. At the same time, several tools already occupy substantial parts of that surface area, and at least one direct namesake already occupies the conceptual center. Verity should not be marketed as a replacement for these tools. It should be positioned as a correlation tool that fails only when it has sufficient evidence, delegates structured validation to specialists and presents a structured explanation of what it checked.

The greatest risks are not technical novelty but usability: unqualified extraction will create far more noise than signal. A repository contains countless strings that resemble commands, ports, environment variables and symbols, while documentation frequently uses placeholders, optional instructions and alternative commands. A useful Verity must therefore begin with safe, high-confidence detectors and make ignore rules, evidence provenance, confidence calibration and continuous validation part of the product from the first release.

## Prior-art categories already solve adjacent problems; none surveyed here provides the full integration

**Verity competes less with one obvious同类 product than with a portfolio of mature, narrowly scoped tools.** The market already offers link checking, documentation-example execution, embedded-code synchronization, workflow and container validation, schema validation, architecture enforcement, code analysis, repository packing and agent-context tooling. A credible evaluation must compare the proposed scope with each of these categories rather than treat them as interchangeable.

| Category and representative tools | Repository and approximate popularity | Verified checks | Important non-goals or limitations |
|---|---:|---|---|
| Link checking: lychee | [lycheeverse/lychee](https://github.com/lycheeverse/lychee) — 4.1k stars | URLs and mail addresses in Markdown, HTML, reStructuredText and other text; supports offline checking and JSON/CI usage [2] | Does not verify repository paths, CLI commands, environment variables, configuration keys, ports, symbols, version pins, Docker instructions or workflow semantics. A live URL does not show that the URL documents the current system. |
| Link checking: markdown-link-check | [tcort/markdown-link-check](https://github.com/tcort/markdown-link-check) — about 712–723 stars in secondary trackers | Liveness of Markdown hyperlinks, with timeouts, retries and ignore rules [8] | Effectively an HTTP/URL checker for Markdown; does not check local build commands, files, environment variables or configuration truth. |
| Markdown/testable examples: mdBook | [rust-lang/mdBook](https://github.com/rust-lang/mdBook) — 19.2k stars | Builds books and runs supported inline code examples, currently presented as rustdoc tests [3] | Does not verify arbitrary prose claims. Example execution is not claim resolution for a repository. |
| Markdown/testable examples: rustdoc | Part of the Rust toolchain | Compiles and runs Rust documentation examples; a test passes when it compiles and runs without panicking [9] | `no_run` and `ignore` intentionally do not prove that a snippet works in the current repository. It is Rust-specific and checks executable code rather than documentation claims. |
| Documentation examples: pytest --doctest-modules | Part of the pytest ecosystem | Runs Python doctrings as tests | Verifies executable Python examples; it does not resolve prose commands, configuration references or cross-artifact drift. |
| Sphinx doctest | [sphinx-toolbox doctest extension](https://sphinx-toolbox.readthedocs.io/en/stable/extensions/doctest.html) | Runs selected documentation examples | Focused on examples, not on verifying that written instructions reflect a repository’s current state. |
| Embedded code: embedme | [carlsberg/embedme](https://github.com/carlsberg/embedme) — 424 stars | Pulls code from source files into Markdown, or writes edited blocks back, to keep examples synchronized | Synchronizes example content with files; it does not decide whether the embedded command is the correct command, whether a referenced configuration key exists or whether the documentation is truthful. |
| GitHub Actions linting: actionlint | [rhysd/actionlint](https://github.com/rhysd/actionlint) — 4.4k stars | Workflow syntax, expression typing, `needs` dependencies, runner labels, cron syntax, embedded script checks and other workflow rules [5] | Does not validate that a `README` accurately describes those workflows or that the workflow’s commands, images and environment variables still work in the repository. |
| JSON and workflow/config schema: check-jsonschema | [python-jsonschema/check-jsonschema](https://github.com/python-jsonschema/check-jsonschema) — 351 stars | Validates a JSON or YAML file against a supplied or built-in schema, including GitHub Workflows, Renovate and Azure Pipelines [4] | Confirms that a document conforms to a schema. It does not extract claims from prose, verify that a referenced command exists or determine whether the schema describes the actual system. |
| TOML validation: Taplo | [tamasfe/taplo](https://github.com/tamasfe/taplo) — approximately 2.2k stars | Parsing, formatting, analysis and schema-aware tooling for TOML | Validates TOML form and optionally schema. It does not prove that another document’s description of the configuration is accurate. |
| JavaScript dependency architecture: dependency-cruiser | [sverweij/dependency-cruiser](https://github.com/sverweij/dependency-cruiser) | Forbidden dependencies, custom rules, graphs and dependency-graph validation | Enforces dependency policy that a team defines. It does not extract or test natural-language documentation claims. |
| JVM architecture: ArchUnit | [TNG/ArchUnit](https://github.com/TNG/ArchUnit) — 3.1k stars | Package, class, layer and slice dependencies; cycles and architecture rules over Java bytecode [6] | A unit-test library for architecture. It cannot read “run this command” from a README or verify an environment variable. |
| Python architecture: import-linter | [seddonym/import-linter](https://github.com/seddonym/import-linter) — 948 stars | Imports and contracts between Python packages | Checks a configured architecture rather than documentation claims or repository truth. |
| Semantic code analysis: Semgrep | Commercial platform; public rule repositories | Pattern- and semantic-based detection across many languages | Finds code patterns and security issues. It does not prove that a document’s claim about the code is correct, nor is it a zero-config prose-to-repository verifier. |
| Semantic code analysis: CodeQL | GitHub’s CodeQL | Code querying and vulnerability analysis | Requires building or acquiring a database and writing queries. It does not verify documentation prose, nor does its core model match the requested language-agnostic zero-config claim extraction. |
| Repository packing: Repomix | [yamadashy/repomix](https://github.com/yamadashy/repomix) — 17.5k stars | Packs a repository into XML, Markdown or plain output with summaries, trees, line numbers and compression [10] | Supplies context to agents; it does not verify the context. |
| Repository packing: Gitingest | [cyclotruc/gitingest](https://github.com/cyclotruc/gitingest) — 11.7k stars | Produces a prompt-friendly summary, directory tree and repository content dump | Provides ingestion context rather than factual verification. |
| Documentation generation and drift: Sintesi | [doctypedev/sintesi](https://github.com/doctypedev/sintesi) — 71 stars | Generates READMEs and documentation and runs a drift check, with an AI/RAG pipeline [11] | Online, model-dependent generation is not equivalent to deterministic, offline claim verification. |
| Documentation generation: SnakeMD | [mrdimosthenis/SnakeMD](https://github.com/mrdimosthenis/SnakeMD) | Programmatic Markdown generation | Generates Markdown output; it does not verify that existing Markdown is true. |

Star counts should be treated as approximate popularity indicators rather than measures of product quality. The figures above come from repository pages, official distribution pages and secondary trackers captured during research; some values are rounded and may have changed since capture. Stars do not reveal adoption inside private enterprises, CI usage, accuracy or maintenance burden.

## Existing checkers validate documents or code in isolation, leaving the repository-correlation gap open

**The central unresolved problem is not the absence of linters but the absence of correlation between what a document says and what the repository actually contains.** Each existing tool tends to answer one bounded question. Lychee asks whether a URL is reachable. actionlint asks whether a workflow is internally well formed. check-jsonschema asks whether a configuration document conforms to a schema. dependency-cruiser asks whether the code violates an explicitly defined architectural rule. None of these questions is identical to asking whether the `README`’s setup instruction, the CI workflow and the Makefile still describe the same build.

### Link checkers prove reachability, not documentation truth

Lychee is a fast, asynchronous Rust link checker that inspects Markdown, HTML, reStructuredText and other text for broken URLs and mail addresses. It can run recursively over a repository, operate offline and emit machine-readable results [2]. markdown-link-check occupies a similar niche at the Markdown-and-HTTP layer [8]. Both are necessary for documentation hygiene, but neither resolves the failure mode Verity targets. A local relative link may resolve while pointing to the wrong version, deprecated script or obsolete configuration key. Conversely, a perfectly valid external URL may document behavior that the local repository no longer implements.

The distinction becomes clearer when documentation contains a command such as `make build` followed by `docker run -p 8080:8080 app`. A link checker can verify that a surrounding URL is reachable, but it cannot establish whether `make build` exists, whether the `Makefile` still defines that target, whether `app` is the current image name, whether port 8080 is still the intended port or whether the surrounding sentence remains accurate. Verity’s value therefore begins where link checking ends.

### Doctest tools execute examples but do not audit prose claims

rustdoc executes documentation examples by compiling them and wrapping them in `main`. A test passes if it compiles and runs without panicking; attributes such as `no_run`, `ignore`, `should_panic` and `compile_fail` alter execution [9]. mdBook can run available tests in a book and currently supports rustdoc tests [3]. pytest and Sphinx-style tools similarly execute selected examples.

These systems are strong evidence that developers already accept executable documentation. Their limitation is scope. They validate code that has been deliberately isolated as an example, not the phrase “run `cargo build --release`”, the environment variable mentioned two paragraphs later, or the claim that a service exposes port 5432. The execution environment can also diverge from the repository: an example may run in a documentation harness while the command shown to developers is never invoked.

### Synchronization and static validation cannot establish semantic agreement

embedme provides a useful counterexample to the claim that no tool touches documentation and code at all. It synchronizes embedded code blocks with real source files so that examples do not silently drift [12]. Its operation is nonetheless content synchronization rather than factual verification. Copying a real command into a document does not show that the command belongs in that section, that the surrounding explanation is correct or that the document’s promise matches the current implementation.

actionlint applies deeper validation to GitHub Actions. It checks workflow syntax, expression typing, `needs` dependencies, runner labels, cron syntax and embedded scripts [5]. check-jsonschema similarly validates JSON and YAML documents against schemas and ships built-in support for GitHub Workflows, Renovate and Azure Pipelines [4]. These tools can reject malformed keys, incorrect expression properties or schema violations, but they cannot answer whether the workflow implements what the `README` claims. A workflow may be internally valid and still contradict the documented setup path.

### Architecture and security tools enforce explicit policies, not inferred documentation facts

Architecture enforcement tools solve a related but materially different problem. dependency-cruiser validates dependency graphs against rules. ArchUnit inspects Java bytecode to test package, class, layer and slice relationships [6]. import-linter checks Python import contracts defined in configuration [7]. Their strength is precision: a team writes a rule, and the tool enforces it.

That strength is also the reason they do not cover Verity’s proposed scope. They do not infer claims from prose, do not determine whether a documentation instruction is still true and generally require the user to specify the policy up front. Verity inverts that model by proposing to discover candidate claims automatically. Its challenge is therefore the reverse: it must infer useful claims without creating an unmanageable volume of false ones.

### Repository packers increase context but do not verify it

Repomix packages repository contents into AI-friendly XML, Markdown or plain-text output, with optional summaries, directory trees, line numbers and tree-sitter-based compression [10]. Gitingest similarly converts a Git repository into a summary, tree and text dump for an LLM [13]. Both are highly relevant to the stated AI-agent use case because agents often operate on packed or partial repository context.

Neither tool determines whether that context is true. In fact, providing more context can amplify the harm from stale instructions if the consuming agent treats the additional text as authoritative. This creates an opportunity for a verifier, but it also establishes a high evidence standard: a drift checker must be substantially more reliable than a tool that merely assembles content.

## The integrated scope remains uncovered, but a direct namesake already claims the conceptual center

**No single surveyed tool delivers the proposed combination of automatic claim extraction, offline verification and repository-wide evidence reporting.** The conclusion is narrower and more defensible than claiming that Verity has no competition. It occupies a gap between link checkers, example runners, synchronization tools, linters, schema validators, architecture enforcers and repository packers. At the same time, the proposal is not as conceptually original as “the first tool to verify claims,” because an existing npm package already uses the same name and the same core metaphor.

### The proposed scope is distributed across many specialized tools

The proposed claim taxonomy spans files and directories, CLI commands and flags, environment-variable names, configuration keys, ports, code symbols and version pins. It also spans Markdown instruction files, CI YAML, Dockerfiles, Makefiles, configuration files and shell scripts. None of the surveyed tools covers that entire graph.

Lychee covers URLs but not commands or symbols. mdBook and rustdoc execute examples but do not perform cross-artifact correlation. actionlint understands GitHub Actions semantics but not README claims. Taplo and check-jsonschema understand configuration form and schema but not whether prose describes the configuration accurately. dependency-cruiser, ArchUnit and import-linter enforce rules authored by developers rather than extracting claims from documentation. Semgrep and CodeQL analyze source code, but their core use is pattern detection or vulnerability analysis, not the proposed language-agnostic, zero-config verification of documentation and operational instructions.

The strongest integrated claim should therefore remain limited to the specific feature combination. It is fair to say that no single tool covers **automatic, zero-config, offline, language-agnostic extraction and cross-artifact verification for the stated claim types**. It would be inaccurate to say that each individual capability is new.

### `@pietro-falco/verity` already occupies deterministic offline claim verification

The most important counterexample is not a generic adjacent tool but a directly named one. `@pietro-falco/verity`, described as alpha software, presents itself as “a notary for your coding agent’s ‘done’—it checks a written claim against reality and stamps it true or false.” It runs a manifest of claims, reports pass or fail and emits a JSON report. Its documentation states that the same claims manifest against the same repository state always produces the same verdict, with no LLM and no network call in the loop. The supported claim types are `file_exists`, `file_matches`, `git_committed` and `command` [1].

This tool does not claim to perform zero-config extraction from Markdown, CI YAML, Dockerfiles, Makefiles, configuration files or shell scripts. It requires an explicit `.verity/claims.json` manifest and therefore does not cover the full proposed scope. Its existence nevertheless changes the product positioning. Verity cannot credibly be introduced as the first tool to verify declared claims against repository reality. The defensible positioning is that it automates claim discovery, expands the taxonomy, correlates heterogeneous artifacts and explains its evidence—all capabilities that the manifest-based namesake leaves to the user.

### Two broader AI-documentation tools occupy nearby semantic space

Sintesi further narrows the apparent white space. It generates documentation, analyzes code, plans documentation structure and runs drift checks through an AI and RAG pipeline, including a `sintesi check` workflow [11]. Its approach is closer to documentation management than to deterministic verification, and its reliance on models and embeddings is a different operating model from offline claim checking. Even so, it shows that the phrase “documentation drift” already has competing meanings.

A separate IC CL / Enforce project also named Verity is an MCP-oriented LLM hallucination checker that challenges model outputs using multiple models, natural-language inference, arithmetic checks, resampling and log-probability analysis [14]. It targets fabricated model output rather than repository facts. The coexistence of these unrelated projects illustrates the practical difficulty: “Verity” is not a distinctive name in this semantic neighborhood, and the term “claims” is used differently by almost every adjacent tool.

## High-confidence, evidence-first extraction is the only credible route past false positives and low adoption

**The most serious threat to Verity is not lack of features but failure to separate facts from suspicious patterns.** Documentation and operational files contain many strings that resemble claims without being actionable facts. A weak extractor will report that `localhost`, `8080`, `NODE_ENV`, `main`, `v1` or `app` are missing, while missing the one instruction that costs a developer an afternoon. If the first-run experience is noisy, users will not tune the tool; they will disable it.

### False positives will dominate any naive extractor

A command such as `docker run --rm -p 5432:5432 myapp` contains at least five candidate entities: a command, flags, a port mapping, an image reference and potentially a version. Only some of those entities may be meaningful claims in context. Documentation may also show mutually exclusive alternatives, illustrative values, deprecated commands retained for migration guidance, example environment names or fictional configuration keys. A grep-like detector cannot distinguish these cases reliably.

Path checking creates a similar problem. Markdown often uses relative links that resolve through the documentation renderer rather than the filesystem, and repository layouts vary between source, build output and packaged distributions. Checking only source paths may miss generated artifacts; checking build artifacts may be impossible in CI; treating every token that looks like a path as a real path will produce continuous false positives.

### Claims without executable semantics are often unverifiable

Many of the requested claim types are structurally difficult. A configuration key may be constructed dynamically, namespaced, loaded from multiple files, optional or defined in code rather than a configuration document. A port may be allocated by the orchestrator, overridden by an environment variable, documented as a default rather than a guarantee or bound only at runtime. A version pin may be legitimate in one artifact and stale in another. A symbol may be generated, conditionally compiled, minified, macro-produced or defined in a language that the tool does not parse.

A design that treats all such cases as equivalent failures will conflate ambiguity with drift. The tool must instead express what evidence would be required to make a claim true and stop short when that evidence is unavailable. Confidence must reflect the strength and completeness of the evidence, not the superficial plausibility of the match.

### Repository churn will increase the cost of maintaining generic detectors

A repository-aware verifier is tightly coupled to the formats it parses. GitHub Actions keys and Dockerfile directives are stable enough to support specialized parsing, but prose is not. Changes in documentation style, templating, shell dialects, build wrappers and language-specific build systems will require continuous detector maintenance.

The first version should therefore avoid attempting universal language support. A broader initial taxonomy may appear more capable while actually being less trustworthy. High-value, parseable artifacts should come first, followed by narrowly scoped claim families with conservative matching rules.

### Offline execution has a sharp boundary

Offline verification is useful for CI reproducibility and supply-chain risk, but it cannot validate externally documented behavior or third-party endpoints. A promise such as “the API conforms to this OpenAPI document” cannot be confirmed by inspecting repository files alone. Similarly, a live URL is not evidence that an external service still implements the behavior the documentation describes.

The product should therefore distinguish three states: **verified against repository evidence**, **not applicable in offline mode** and **ambiguous or insufficient evidence**. Treating the second state as a failure would force users to choose between disabling the check and maintaining a growing allowlist.

### Without CI integration and a clear human workflow, adoption will remain marginal

Repository maintainers already have link checkers, schema validators, linters and test suites. A new tool must justify its place in a workflow by being fast, predictable and easy to interpret. A binary pass/fail is useful for CI, but it is insufficient during development. Contributors need to know which claim failed, where it was extracted, what evidence was examined, why the match was rejected and whether a documented alternative is equally valid.

Output aimed only at machines will not help a human decide whether to update the documentation, fix the implementation or suppress a false positive. Conversely, verbose output without stable machine identifiers makes automation difficult. Verity needs both a compact developer explanation and a stable machine schema from the outset.

## Verity should rank evidence quality above claim quantity and specialize before generalizing

**The ordering of requirements determines whether Verity becomes infrastructure or remains a toy.** A useful first release should prove that it can resolve a small set of high-value claims accurately, explain its reasoning and fail safely. Additional claim types, language support and repository formats should follow only after the evidence model is stable.

### 1. Evidence-first confidence must take precedence over broad claim coverage

The first requirement is a verifier model that separates observed facts, resolvers, candidate claims and verdicts. Every finding should identify:

- the source file, line and column;
- the extracted claim text;
- the claim family;
- the resolver used;
- the positive and negative evidence considered;
- the reason a match was accepted or rejected;
- an explicit confidence and uncertainty status.

Confidence should be calibrated on annotated repositories and measured by precision, recall and abstention rather than by the raw number of findings. A tool that finds every stale instruction but also fabricates hundreds of claims is not useful. One that silently ignores ambiguous cases is not a verifier. The target state must be **high precision with explicit abstention**, not maximum coverage.

### 2. Offline operation must be enforced, bounded and auditable

Offline execution should mean no network calls, package installation, remote schema downloads or model inference during verification. Local execution should be allowed only when explicitly classified as an opt-in runtime test.

The tool should record which checks were performed offline, whether the repository state was dirty and whether a required artifact was unavailable. If a claim cannot be resolved without network access, the report should state that constraint rather than guessing. This makes the offline promise auditable and prevents the checker from drifting into the behavior of generic web validators.

### 3. Claim extraction must begin with a small, parseable, high-value artifact set

The initial scope should prioritize files with explicit semantics:

- GitHub Actions YAML;
- Dockerfiles;
- Makefiles;
- shell scripts;
- a limited set of configuration formats;
- README, AGENTS, CLAUDE and CONTRIBUTING documentation.

Free prose should follow only after structured extraction has demonstrated acceptable precision. This sequence avoids the trap of extracting every token that looks like a command while delivering immediate value in CI, Docker and build configuration.

### 4. Extractors must encode semantic identity and origin

A usable extractor needs to preserve enough structure to distinguish real claims from examples. A `README` code block should be parsed as a different evidence source from a `RUN` instruction in a Dockerfile, and an instruction should be distinguished from an alternative, comment or variable interpolation.

For each claim type, the tool should record the source range and semantic identity. “Runs `pytest`” should not automatically be merged with an image tag, an environment variable or a port mapping. Without this provenance, suppressions become difficult to maintain and findings cannot be reviewed reliably.

### 5. Correlated, contradictory claims should take priority over isolated tokens

The most valuable findings will come from comparing artifacts rather than inspecting them individually. Examples include:

- a README command not present in the Makefile or workflow;
- a Dockerfile `EXPOSE` port that conflicts with the documented port;
- a workflow environment variable absent from the documented setup;
- documentation referencing a configuration key that the validator accepts but the code no longer reads.

These cross-artifact contradictions are more actionable than isolated tokens because they reveal disagreements about the same operational fact. Correlation should therefore be the headline capability, while single-artifact extraction remains the foundation.

### 6. Machine and human output must be separate but connected

The tool should support JSON and SARIF for automation, together with a compact developer summary. Every machine finding needs a stable rule identifier and a canonical evidence pointer. The human output should explain what was checked and why the result is uncertain.

This separation avoids a common failure mode in analysis tools: machine output becomes unreadable, while human output cannot be automated. Verity should emit both from one execution, with the human explanation linked to the stable machine identifiers.

### 7. CI behavior must be conservative and configurable

Exit codes should distinguish at least three outcomes: verified failure, error and uncertainty. A team should be able to choose whether uncertainty fails CI, creates a warning or remains informational.

Configurable severity is necessary because a false instruction and an unresolvable environment variable are not equivalent risks. The default should be conservative: fail when there is strong evidence of drift, report ambiguity separately and avoid allowing a single ambiguous token to block a merge.

### 8. Specialist tools must be delegated rather than duplicated

Verity should invoke lychee, actionlint, check-jsonschema, language-specific tests or architecture tools where appropriate, then correlate their results with documentation claims. This reduces the burden of maintaining parsers for every format and focuses Verity on its distinctive contribution.

The product should not attempt to replace mature specialists. It should consume their findings, identify contradictions across tools and explain what remains unresolved.

### 9. Tuning must be repository-aware but require explicit approval

Autodiscovered files should be checked by default, while exclusions, aliases, allowlists and claim transformations should be committed to the repository. Onboarding should produce a proposed configuration and a reviewable report of initially ambiguous claims.

This requirement addresses both automation and governance. Repositories with monorepos, generated documentation, examples and public documentation need different rules. Those rules should be inspectable and version-controlled rather than hidden in personal editor settings or inferred implicitly.

### 10. Determinism and performance must be visible in the report

The same commit, same extractor configuration and same verified evidence should produce the same result. Relevant metadata should include:

- input digest;
- scanned files;
- enabled extractors;
- execution duration;
- warnings;
- unresolved external claims.

Incremental checking may improve performance, but it must never weaken the definition of a completed run. Without these guarantees, users cannot tell whether a different result reflects a repository change, a changed tool version or an unreliable detector.

## Verity’s defensible niche is cross-artifact evidence correlation, not another repository scanner

**Verity has a genuine opportunity only if it sells evidence correlation rather than claim quantity.** The adjacent landscape is mature: lychee, markdown-link-check, rustdoc, mdBook, pytest, embedme, actionlint, check-jsonschema, Taplo, dependency-cruiser, ArchUnit, import-linter, Semgrep, CodeQL, Repomix and Gitingest all solve real problems. Their proliferation shows that developers value automated verification, but it also means that a new generic scanner will not succeed merely by adding another claim type.

The distinctive, evidence-backed opportunity is to infer a bounded set of high-value claims from structured repository artifacts, resolve them against local evidence and report cross-artifact drift with confidence and provenance. This is not a replacement for specialized tools. It is a coordinator and correlation layer positioned above them.

Success depends on three conditions. First, Verity must resist the temptation to claim that every command-like token is a command. Second, it must abstain when evidence is insufficient rather than turning ambiguity into failure. Third, it must prove accuracy on real repositories before expanding the taxonomy. If it cannot achieve high precision with explicit uncertainty, users will treat it as noise. If it can, it could become the missing verification layer between documentation, agent context and operational configuration.

## Data sources

[1] https://www.npmjs.com/package/@pietro-falco/verity
> “The same claims manifest against the same repository state always produces the same verdict — no LLM, no network call, in the loop.”

[2] https://github.com/lycheeverse/lychee
> “Finds broken hyperlinks and mail addresses inside Markdown, HTML, reStructuredText, or any other text file or website!”

[3] https://github.com/rust-lang/mdBook/blob/master/guide/src/cli/test.md
> “mdBook supports a test command that will run all available tests in a book. At the moment, only rustdoc tests are supported.”

[4] https://github.com/python-jsonschema/check-jsonschema
> “A CLI and set of pre-commit hooks for jsonschema validation with built-in support for GitHub Workflows, Renovate, Azure Pipelines, and more!”

[5] https://github.com/rhysd/actionlint/blob/main/README.md
> “actionlint is a static checker for GitHub Actions workflow files.”

[6] https://github.com/TNG/ArchUnit
> “A Java architecture test library, to specify and assert architecture rules in plain Java.”

[7] https://github.com/seddonym/import-linter
> “Import Linter is a command line tool to check that you are following a self-imposed architecture within your Python project.”

[8] https://github.com/tcort/markdown-link-check
> “checks all of the hyperlinks in a markdown text to determine if they are alive or dead”

[9] https://doc.rust-lang.org/rustdoc/write-documentation/documentation-tests.html
> “rustdoc supports executing your documentation examples as tests.”

[10] https://github.com/yamadashy/repomix
> “Pack your codebase into AI-friendly formats.”

[11] https://github.com/doctypedev/sintesi
> “Sintesi is a self-maintaining documentation engine that keeps your documentation in sync with your codebase.”

[12] https://github.com/carlsberg/embedme
> “embedme lets you embed code into your markdown files.”

[13] https://github.com/cyclotruc/gitingest
> “Turn any Git repository into a prompt-friendly text ingest for LLMs.”

[14] https://www.computing.co.uk/news/2026/ai/iccl-launches-open-source-tool-to-reduce-llm-hallucinations
> “ICCL has released an open source tool designed to reduce LLM hallucinations.”

[15] https://github.com/tamasfe/taplo
> “A TOML toolkit written in Rust.”

[16] https://github.com/sverweij/dependency-cruiser
> “dependency-cruiser is a tool for validating dependency graphs.”
