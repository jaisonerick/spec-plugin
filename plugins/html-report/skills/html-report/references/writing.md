# Writing: what the report says and in what order

The reader opens the link, reads for forty seconds, and either acts or closes it. Everything here serves that.

## Section order

1. **The answer.** Stat tiles, then two or three paragraphs that state the finding and its scope. Someone who reads only this section must be able to repeat the conclusion correctly.
2. **The mechanism.** The chart that shows *why* the headline is what it is.
3. **The other cuts.** Composition, detail, the per-entity view. One section per question the reader will actually ask.
4. **How the number is built.** Source, grain, definitions, what was checked.
5. **Where it can still lie.** What was left out and what would change the reading.

The last two are not appendices to skip. They are what makes the report survive the first sceptical question, and writing them is where you discover the number you cannot defend.

## The headline

Lead with the number, then the scope, then the meaning. Never the reverse.

> **Nenhuma safra se sustenta sozinha.** O NDR não passa de 100% em nenhum ponto depois da entrada: 86% no MOB 3, 76% no MOB 6, 54% no MOB 12.

Not "we analysed retention across cohorts and found interesting patterns". Say the thing.

**Four stat tiles, maximum.** Each is one number and one line saying what it is. A fifth tile means you have not decided what the report is about.

## Every section states its scope

"45%" is not a finding. "45% do volume, nas safras de 2025 em diante, no 12º mês depois da entrada" is. The scope goes in the section's `.sub` line, so it is present without being repeated in every sentence.

The three dates are different and the reader needs all of them: when the report was generated, what the data's own as-of date is, and what period the analysis covers. The header carries the first two; the title carries the third.

## Gloss every term at first use

Any acronym, internal label or coined name gets a short explanation in place, in parentheses or as an appositive:

> O NDR (net dollar retention, o quanto uma safra ainda desembolsa contra o que desembolsava ao entrar) não passa de 100%…

A glossary at the top is not a substitute — nobody reads up. If a term appears once, replace it with plain words instead of glossing it.

## Numbers in prose

- **Compute every number in prose from the same data the charts read.** A typed number rots on the next run and nothing warns you. This is the most common way a report ends up contradicting its own chart.
- pt-BR formatting: `R$ 8.886.382`, `53,7%`. Thousands with a period, decimals with a comma.
- One decimal for percentages, none for currency in prose. Two decimals reads as false precision on a number that has a confidence interval nobody computed.
- Round in prose, exact in tooltips and tables. "cerca de 90%" in the paragraph, `89,6%` in the tile, the raw value on hover.

## The honesty rules

These are what make a report trustworthy rather than merely handsome.

- **Say what the number is not.** If it is volume and not revenue, say so where the number appears, not only in the method section.
- **Mark thin bases.** A cell built on three merchants gets faded and asterisked, and the note says why. Someone will quote it otherwise.
- **A visible cap is honest, a silent one is not.** "200 de 1.482 linhas" in the table counter; "a série para no MOB 12 porque adiante restam 4 safras" in a note.
- **When two readings disagree, reconcile them in the report.** Measure what each difference contributes and say which one is the reading and why. Publishing both without a verdict pushes your work onto the reader.
- **Correct openly.** If this report supersedes an earlier number, say so in the note where it matters, with the reason. A quiet correction is discovered later and costs more.

## Tone

Impersonal and factual. No "we are excited to share", no "as we can clearly see", no adjectives doing work the number should do. If the finding is dramatic, the number carries it.

Portuguese specifics: do not conjugate English verbs, do not invent nominalizations, and never use an em dash to break mid-sentence — a comma, a colon, parentheses or two sentences.

## Before you call it done

Read it once as a person who was not in the analysis. Every term explained, every number scoped, every chart legible without the paragraph next to it, and the first section enough to act on. Then open the actual file, look at it, and check the console.
