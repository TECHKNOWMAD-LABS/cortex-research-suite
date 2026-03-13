# AI Writing Anti-Patterns Reference

A catalog of detectable patterns in AI-generated content, with examples and preferred alternatives. This guide serves the de-slop skill for identifying and rewriting AI-heavy markdown.

---

## Category 1: Structural Tells (Weight: 3)

Detection focuses on layout choices that reflect training data rather than human document design.

### Pattern 1.1: Emoji in Headers

**Regex hint:** `^#+\s*.*[\p{Emoji}]`

**Bad example:**
```
## 🚀 Getting Started with the Platform
## 💡 Key Features Overview
## 🎯 Our Mission Statement
```

**Good rewrite:**
```
## Getting Started with the Platform
## Key Features Overview
## Our Mission Statement
```

**Why it matters:** Emoji in headers signals template-driven content generation; professional documentation reserves emoji for specific callout blocks or intentional UI elements, not for header decoration.

---

### Pattern 1.2: Excessive Bold Formatting in Lists

**Regex hint:** `^[\s]*[\*\-]\s*\*\*.*?\*\*:\s`

**Bad example:**
```
- **Scalability**: The system can handle growth.
- **Security**: All data is encrypted.
- **Performance**: Response times stay under 100ms.
- **Reliability**: 99.99% uptime guaranteed.
```

**Good rewrite:**
```
- Scalability: The system can handle growth.
- Security: All data is encrypted.
- Performance: Response times stay under 100ms.
- Reliability: 99.99% uptime guaranteed.
```

**Why it matters:** Consistent bolding of list labels is a stylistic signature of batch text generation; selective emphasis (reserved for critical terms) reflects human editorial judgment.

---

### Pattern 1.3: Headers as Full Sentences

**Regex hint:** `^#+\s+.*[\.!?]$`

**Bad example:**
```
## Why Your Business Needs This Solution Today
## How We're Revolutionizing the Industry
## What Sets Us Apart from the Competition
```

**Good rewrite:**
```
## Business Requirements
## Industry Position
## Competitive Advantages
```

**Why it matters:** Sentence-form headers create narrative friction; noun-based headers improve scannability and signal content designed for readers, not algorithmic generation.

---

### Pattern 1.4: Numbered Lists Where Bullets Suffice

**Regex hint:** `^\d+\.\s+[A-Za-z].*(?:\n\d+\.\s+[A-Za-z].*){3,}` (when order is not sequential/causal)

**Bad example:**
```
## Benefits
1. Improved team collaboration
2. Faster deployment cycles
3. Reduced operational costs
4. Enhanced user satisfaction
```

**Good rewrite:**
```
## Benefits
- Improved team collaboration
- Faster deployment cycles
- Reduced operational costs
- Enhanced user satisfaction
```

**Why it matters:** Numbering implies sequence or priority; unordered lists signal that items are equivalent in weight, a distinction humans make deliberately but generative models often ignore.

---

### Pattern 1.5: Section Headers with Marketing Language

**Regex hint:** `^#+\s+(Why|How to|Everything You Need|The Ultimate Guide|The Complete|Best Practices for)`

**Bad example:**
```
## Why You Can't Afford to Ignore This
## How to Unlock Your Full Potential
## Everything You Need to Know About Automation
## The Ultimate Guide to Cloud Migration
```

**Good rewrite:**
```
## Cost-Benefit Analysis
## Getting Started with Automation
## Cloud Migration Overview
## Best Practices
```

**Why it matters:** Sensationalized headers with "you" and superlatives are signatures of content designed to drive engagement rather than inform; technical documentation uses descriptive, neutral headers.

---

## Category 2: Hyperbolic Language (Weight: 2)

Exaggeration and unsupported claims reflect training data skewed toward marketing and promotional material.

### Pattern 2.1: Power Words Without Support

**Regex hint:** `\b(revolutionary|game-changing|cutting-edge|unleash|supercharge|groundbreaking|paradigm-shifting|disrupted?|transform(?:ative)?|unleash|breakthrough)\b`

**Bad example:**
```
Our revolutionary platform unleashes cutting-edge automation that will transform your workflow. 
This groundbreaking technology supercharges productivity by allowing teams to unleash their full potential.
The paradigm-shifting approach disrupts traditional processes.
```

**Good rewrite:**
```
Our platform automates routine tasks, reducing manual work by approximately 40%.
This feature allows teams to focus on higher-value work while reducing turnaround time.
The approach replaces multi-step manual processes with a single configuration step.
```

**Why it matters:** Power words create urgency without specificity; concrete metrics and outcomes demonstrate actual value and build reader trust.

---

### Pattern 2.2: Unsupported Superlatives

**Regex hint:** `\b(the most|the best|the only|unparalleled|unmatched|unprecedented|industry-leading|market-leading)\b.*(?:solution|platform|tool|approach)`

**Bad example:**
```
The most advanced analytics engine on the market.
Our unparalleled customer support is the best in the industry.
The only solution you'll ever need for data management.
Unprecedented speed improvements across all operations.
```

**Good rewrite:**
```
Analytics engine with 200+ visualization types and real-time query processing.
Customer support with 2-hour average response time and 95% first-contact resolution.
Handles datasets up to 50TB with built-in versioning and access controls.
Processes queries 5x faster than the previous generation through parallel indexing.
```

**Why it matters:** Superlatives invite skepticism; specific metrics provide measurable claims that readers can verify or compare.

---

### Pattern 2.3: Marketing Language in Technical Docs

**Regex hint:** `(don't|didn't|won't|would|could|can) (you|your|teams?|organizations?|businesses?)\s+(finally|now|at last).*\b(achieve|unlock|discover|realize|gain)\b`

**Bad example:**
```
Finally achieve the reliability you deserve.
Now unlock the performance your business deserves.
Discover the efficiency gains your team has been waiting for.
Realize your vision of seamless integration.
```

**Good rewrite:**
```
Achieve 99.95% uptime through automated failover and load balancing.
Reduce latency to under 50ms using edge caching and CDN integration.
Deploy new features in under 30 minutes with our CI/CD pipeline.
Integrate with 150+ third-party tools via webhook or REST API.
```

**Why it matters:** "Deserves" and "finally" appeal to emotion; technical documentation appeals to problem-solving needs with concrete capabilities.

---

### Pattern 2.4: Exaggerated Capability Claims

**Regex hint:** `\b(automatically|instantly|seamlessly|effortlessly|zero-config|no-setup|magic)\b` without qualifiers

**Bad example:**
```
Automatically scales your infrastructure based on demand.
Instantly migrate all your data with zero downtime.
Seamlessly integrate with your existing systems.
Effortlessly achieve enterprise-grade reliability.
Zero-setup deployment across all regions.
```

**Good rewrite:**
```
Scales automatically when CPU utilization exceeds 70% (configurable threshold).
Migrates data with a configurable cutover window; typical downtime is 15 minutes for databases under 1TB.
Integrates via REST API, GraphQL, or webhook (configuration required for custom scenarios).
Achieves 99.95% uptime through automated health checks and failover (requires multi-region setup).
Standard deployment takes 20 minutes; additional regions add 5 minutes each.
```

**Why it matters:** Absolute claims collapse under scrutiny; qualified claims acknowledge real-world constraints and build credibility.

---

## Category 3: Defensive/Compensatory Framing (Weight: 2)

Anticipatory language revealing authorial self-consciousness rather than confident communication.

### Pattern 3.1: "This is Not a..." Defensive Openings

**Regex hint:** `^(This is not|We're not|Unlike|Rather than|It's not just another|This isn't simply)\b`

**Bad example:**
```
This is not just another monitoring tool—it's a complete observability platform.
We're not claiming to be a silver bullet, but our approach is fundamentally different.
Unlike other solutions that promise everything, we focus on what matters.
This isn't simply data storage; it's intelligent data management.
```

**Good rewrite:**
```
The platform provides application performance monitoring, infrastructure monitoring, and log analysis in a single interface.
Our approach focuses on three core capabilities: distributed tracing, metric aggregation, and anomaly detection.
We differ from competitors by offering vendor-agnostic instrumentation and no forced upgrades.
The system performs automatic data tiering, compression, and retention optimization.
```

**Why it matters:** Defensive framing wastes space and reveals insecurity; direct statements of what something *is* communicate with authority.

---

### Pattern 3.2: Unprompted Comparisons

**Regex hint:** `\b(Unlike (most|other|traditional)|Compared to|In contrast to|Whereas other)\b`

**Bad example:**
```
Unlike traditional approaches, we prioritize user experience.
Compared to legacy systems, our solution is infinitely more flexible.
In contrast to competitors, we never lock you in.
Whereas other tools require weeks of setup, ours takes days.
```

**Good rewrite:**
```
The interface prioritizes common workflows, requiring no configuration for standard deployments.
Configuration changes take effect immediately without restarting services.
Customers can export their data in standard formats and migrate at any time.
Standard setup completes in 1-2 days; complex deployments may require 1-2 weeks of planning.
```

**Why it matters:** Comparative framing shifts focus away from actual product benefits; direct capability statements keep attention on functionality.

---

### Pattern 3.3: Self-Promotional Framing

**Regex hint:** `\b(What sets|What makes|Our secret|Our unique|What distinguishes|Where we excel)\b`

**Bad example:**
```
What sets our platform apart is our obsession with user experience.
What makes us different is our commitment to transparency.
Our secret sauce is our proprietary algorithm.
Our unique value proposition centers on developer-first design.
Where we excel is in reliability and performance.
```

**Good rewrite:**
```
The platform includes real-time collaboration, version control, and audit logging.
All pricing is public; no custom quotes, no surprise fees.
The algorithm uses ensemble methods combining neural networks and symbolic reasoning for improved accuracy.
APIs prioritize simplicity: 30 endpoints instead of 200, average integration time 2 hours.
The system maintains 99.95% uptime and serves responses within 100ms at p95.
```

**Why it matters:** Claims of differentiation unsubstantiated by specifics feel hollow; concrete features speak for themselves.

---

### Pattern 3.4: Anticipating Skepticism

**Regex hint:** `\b(Not just|Not only|More than|Goes beyond|Takes it further)\b`

**Bad example:**
```
Not just a tool—it's a complete ecosystem.
More than mere automation—it's intelligent process management.
It goes beyond simple monitoring.
Not only do we provide the software, we offer strategic consulting.
```

**Good rewrite:**
```
Includes workflow engine, analytics dashboard, and API gateway.
Provides rule-based automation plus machine learning classification of process anomalies.
Monitoring includes infrastructure metrics, application traces, and custom event ingestion.
Software license includes quarterly architecture reviews and capacity planning assistance.
```

**Why it matters:** Hyperbolic framing invites doubt rather than confidence; feature enumeration lets capabilities stand on their own merit.

---

## Category 4: Buzzword Patterns (Weight: 2)

Clustering of abstract modifier chains that obscure rather than clarify.

### Pattern 4.1: Adjective Stacking

**Regex hint:** `\b(?:enterprise-grade|production-ready|battle-tested|world-class|best-in-class|proven|robust|scalable|reliable)\s+(?:enterprise-grade|production-ready|battle-tested|world-class|best-in-class|proven|robust|scalable|reliable)\b`

**Bad example:**
```
Enterprise-grade, production-ready, battle-tested solution.
World-class, best-in-class platform.
A proven, robust, and scalable infrastructure.
```

**Good rewrite:**
```
Used in production by 500+ customers with 99.95% uptime SLA.
Handles 1M+ requests per second with sub-100ms latency at p99.
Supports horizontal scaling to 100+ nodes without performance degradation.
```

**Why it matters:** Stacked adjectives replace quantification; specific metrics prove capability better than abstract modifiers.

---

### Pattern 4.2: Redundant Phrases

**Regex hint:** `\b(fully autonomous|zero-human-intervention|completely automated|entirely self-service|fully managed|completely serverless)\b`

**Bad example:**
```
Fully autonomous zero-human-intervention pipeline.
Completely automated and entirely self-service deployment.
Fully managed and completely serverless infrastructure.
```

**Good rewrite:**
```
Pipeline runs on schedule; no manual steps required.
Deployment is self-service; no approval or handoff steps needed.
No servers to provision, patch, or maintain.
```

**Why it matters:** Redundancy signals filler; single, concrete verbs communicate more efficiently.

---

### Pattern 4.3: Empty Modifiers Without Specifics

**Regex hint:** `\b(robust|seamless|elegant|intuitive|powerful|efficient|intelligent|smart)\b` (standalone, without follow-up explanation)

**Bad example:**
```
Our robust architecture ensures reliability.
The seamless integration simplifies workflows.
An elegant solution to complex problems.
The intuitive interface reduces training time.
```

**Good rewrite:**
```
The architecture uses automated failover, distributed consensus, and persistent logging to maintain consistency across node failures.
Integration via REST API, GraphQL, or native SDK; typical setup time is 2 hours.
The solution reduces configuration lines from 500+ to 50 through smart defaults and templates.
The interface requires zero training for standard workflows; advanced features are documented with inline help.
```

**Why it matters:** Abstract praise provides no information; mechanisms and outcomes demonstrate value.

---

### Pattern 4.4: Compound Buzzwords

**Regex hint:** `(AI|ML|machine learning|intelligent|smart|advanced|next-gen|cutting-edge)[\-\s]+(powered|automation|insights|optimization|analytics|orchestration)`

**Bad example:**
```
AI-powered intelligent automation engine.
Machine learning-driven smart optimization.
Next-generation intelligent analytics platform.
Advanced automated workflow orchestration.
```

**Good rewrite:**
```
Automation engine that learns from execution patterns to optimize routing decisions.
Identifies anomalies in performance metrics using statistical baselines and isolation forests.
Provides root cause analysis through correlation of events across 50+ data sources.
Routes tasks based on resource availability and historical completion times per task type.
```

**Why it matters:** Buzzword compounds obscure mechanism; specific technical choices (algorithms, approaches) prove substance.

---

## Category 5: Motivational/Inspirational Tone (Weight: 1)

Aspirational language in contexts requiring neutrality.

### Pattern 5.1: Inspirational Appeals in Technical Context

**Regex hint:** `\b(refuse to be|dare to|demand|excellence|potential|passion|vision|journey|transform|empower|breakthrough|reimagine)\b` in headers or opening paragraphs

**Bad example:**
```
## Dare to Dream Bigger with Our Platform
For teams that refuse to be average and demand excellence.
Unleash your potential and reimagine what's possible.
Join the revolution in application development.
Transforming visions into reality, one deployment at a time.
```

**Good rewrite:**
```
## Scaling Application Architecture
Teams managing 100+ deployments daily can reduce release cycle time using this approach.
The system supports blue-green deployments and automatic rollback on health check failure.
Version control integrates directly with CI/CD; typical pipeline execution time is 8 minutes.
```

**Why it matters:** Inspirational tone is off-key in technical documentation; professional tone maintains reader trust and clarity.

---

## Category 6: Filler Patterns (Weight: 1)

Conversational padding that inflates word count without adding substance.

### Pattern 6.1: Context Padding

**Regex hint:** `^(In today's|As we navigate|With the rise of|In an increasingly|In this (day and age|modern era|digital landscape)|As organizations grapple with)\b`

**Bad example:**
```
In today's rapidly evolving digital landscape, organizations need...
As we navigate the complexities of modern cloud infrastructure...
With the rise of artificial intelligence, companies are...
In this era of rapid technological change, solutions must...
```

**Good rewrite:**
```
Organizations managing multi-cloud infrastructure need...
Cloud deployments introduce complexity in resource allocation and cost tracking...
Machine learning models in production require monitoring for data drift and performance degradation...
Modern deployments require solutions that adapt to changing resource constraints...
```

**Why it matters:** Padding dilutes signal; direct problem statements engage readers immediately.

---

### Pattern 6.2: Obligatory Interjections

**Regex hint:** `^(It's worth noting|It's important to note|Interestingly|Notably|Significantly|Importantly|By the way)\b`

**Bad example:**
```
It's worth noting that performance varies by region.
Interestingly, most users prefer the command-line interface.
Notably, the system scales horizontally.
By the way, you can customize the dashboard.
```

**Good rewrite:**
```
Performance varies by region; Asia-Pacific averages 150ms latency versus 40ms in US-East.
Most users (68%) prefer the command-line interface; the web dashboard is used mainly for monitoring.
The system scales horizontally across regions; add nodes to increase capacity.
Dashboard customization is available via config file or API.
```

**Why it matters:** Interjections slow reading; direct statements with evidence move communication forward.

---

### Pattern 6.3: Exploratory Openings

**Regex hint:** `^(Let's|Let me|Let's dive|Let's explore|Here we (go|explore)|Without further ado)\b`

**Bad example:**
```
Let's dive into the architecture overview.
Let's explore how authentication works.
Here we go with the deployment guide.
Without further ado, let's examine the configuration.
```

**Good rewrite:**
```
## Architecture Overview
## Authentication
## Deployment Guide
## Configuration
```

**Why it matters:** "Let's" addresses readers as peers in a conversation; headers establish scope and allow readers to choose their path.

---

### Pattern 6.4: Paragraph Starters with Empty Transitionals

**Regex hint:** `^(So,|Now,|Well,|Basically,|Essentially,|In short,)\s+` (when not following a complex statement)

**Bad example:**
```
So, the platform provides several core features.
Now, we'll examine the deployment process.
Well, configuration requires a YAML file.
Basically, the system is built on Kubernetes.
```

**Good rewrite:**
```
The platform provides several core features: authentication, data persistence, and caching.
The deployment process involves three steps: image building, registry push, and manifest application.
Configuration uses YAML; templates are provided for common scenarios.
The system is built on Kubernetes 1.25+, which provides container orchestration and resource management.
```

**Why it matters:** Empty transitionals add no semantic content; direct statements respect reader time.

---

## Category 7: Repetitive Structure (Weight: 1)

Templated patterns that signal batch generation rather than individual thought.

### Pattern 7.1: Identical List Item Openings

**Regex hint:** `^[\s]*[\*\-]\s+(Never|Always|Ensure|Avoid|Use|Don't)\s+` (same verb across 4+ consecutive items)

**Bad example:**
```
- Always validate input parameters
- Always check for null values
- Always log errors appropriately
- Always implement timeout handlers
- Always document API changes

- Avoid using global variables
- Avoid hardcoding credentials
- Avoid synchronous blocking calls
- Avoid catching generic exceptions
- Avoid committing secrets to version control
```

**Good rewrite:**
```
- Validate input parameters and check for null values
- Log errors at appropriate severity levels
- Implement timeout handlers and circuit breakers
- Document API changes in version notes
- Monitor for performance regressions in production

Input validation:
- Reject requests with missing required fields
- Type-check all parameters
- Enforce length limits on string inputs

Common mistakes:
- Global variables create hard-to-trace dependencies
- Hardcoded credentials leak in version control
- Synchronous calls block event loops and increase latency
- Generic exception handlers mask root causes
```

**Why it matters:** Repetitive structure is a signature of template-generated content; natural writing varies sentence structure based on semantic content.

---

### Pattern 7.2: Parallel Phrasing Across Paragraphs

**Regex hint:** Multiple paragraphs with identical sentence structures (SVO order, length, punctuation patterns)

**Bad example:**
```
The platform provides authentication. Users can configure it quickly. Teams appreciate its simplicity.

The system offers caching. Developers can enable it easily. Customers see performance improvements.

The tool delivers monitoring. Operations can set it up fast. Organizations value the visibility.
```

**Good rewrite:**
```
Authentication is built-in and configurable without code changes.

Caching is optional; enable it per endpoint or globally. Performance benchmarks show 5-10x improvement for read-heavy workloads.

Monitoring provides infrastructure metrics, application traces, and custom event ingestion. Most teams configure standard dashboards in under 1 hour.
```

**Why it matters:** Parallel structure in this context signals mechanical generation; varied structure reflects considered, contextual writing.

---

### Pattern 7.3: Cookie-Cutter Section Headings

**Regex hint:** Chapters/sections following predictable "Overview → Features → Benefits → Best Practices → Troubleshooting" across multiple topics

**Bad example:**
```
### Authentication Overview
### Authentication Features
### Authentication Benefits
### Authentication Best Practices
### Authentication Troubleshooting

### Caching Overview
### Caching Features
### Caching Benefits
### Caching Best Practices
### Caching Troubleshooting
```

**Good rewrite:**
```
### Authentication
- Single sign-on via OpenID Connect or SAML
- Role-based access control with custom attributes
- Time-limited tokens with refresh rotation
- Audit logging of all authentication events

Recommended approach: Use OpenID Connect for user-facing apps, SAML for enterprise SSO.

### Caching
Caching is optional and improves performance for read-heavy workloads.

Enable globally:
[code example]

Or per-endpoint:
[code example]

Invalidation strategies: TTL-based (default), event-based, or manual. Cache hit rates typically reach 80-95% for standard workloads.

Common issues and fixes:
- Stale data: Reduce TTL or enable event-based invalidation
- Memory exhaustion: Set max cache size; LRU eviction is automatic
```

**Why it matters:** Template-driven headings create false consistency across unrelated topics; structure should follow semantic hierarchy and need, not formula.

---

## Using This Reference

Each pattern includes:

1. **Pattern Name**: Descriptive label
2. **Regex Hint**: Simplified pattern for scanner implementation (not exhaustive)
3. **Bad Example**: AI-generated or AI-influenced text
4. **Good Rewrite**: Professional, human-written alternative
5. **Why It Matters**: One-sentence principle

Weight values (1-3) indicate prevalence and severity in AI output. Higher-weight categories should be prioritized in scanning and remediation.

Weights:
- **3 (Structural Tells)**: Most common and most reliably detectable
- **2 (Hyperbolic, Defensive, Buzzwords)**: Frequent and moderately reliable
- **1 (Motivational, Filler, Repetitive)**: More subtle; context-dependent

Use this catalog to train scanning logic, establish scoring thresholds, and guide rewriting workflows.
