# CognOS Planning Mode — Vibecoding (Lovable.dev)

**Can be used on Lovable:** https://lovable.dev/

Syfte: använd CognOS som planeringslager före implementation, så att vibecoding ger exakt bygginstruktion istället för vag idé.

## Kärnprincip

Innan kodning ska varje idé konverteras till en **byggspec** med:
- exakt mål
- tydlig scope (vad ingår / inte ingår)
- konkreta leverabler
- mätbara acceptanskriterier
- copy/paste-prompt till byggagent (t.ex. Lovable)

## Minimal workflow (10–15 min)

1. Definiera input (idé + målgrupp + utfall).
2. Kör Planning Prompt (nedan).
3. Granska output mot checklistan.
4. Skicka endast "Build Prompt" till Lovable.
5. Validera leverans mot acceptanskriterier.

## Input-mall (fyll i)

- Produkt/feature:
- Målgrupp:
- Primärt mål (1 mening):
- Problem som löses:
- Tekniska constraints:
- Måste finnas:
- Får inte finnas:
- Deadline:

## Planning Prompt (copy/paste)

```text
Du är CognOS Planning Engine.

Uppgift:
Omvandla min idé till en exakt byggspec för vibecoding i Lovable.dev.

Regler:
- Skriv konkret och beslutsbart.
- Inga fluff-ord.
- Inga antaganden utan att märka dem som antaganden.
- Scope ska vara minimalt men komplett för MVP.
- Om något är oklart: välj enklaste tolkning och skriv den explicit.

Input:
[KLISTRA IN DIN INPUT-MALL HÄR]

Returnera EXAKT i detta format:

1) Problem Statement (max 5 rader)
2) Objective (max 3 mätbara mål)
3) User Stories (3–7 st)
4) Scope In (punktlista)
5) Scope Out (punktlista)
6) Functional Requirements (numrerad lista)
7) Non-Functional Requirements (prestanda, säkerhet, UX)
8) Data Model (om relevant)
9) API/Integration Requirements (om relevant)
10) UI Requirements (om relevant)
11) Acceptance Criteria (Given/When/Then)
12) Definition of Done (checklista)
13) Build Prompt for Lovable (copy/paste-klar)
14) Test Prompt for QA Agent (copy/paste-klar)

Extra krav för Build Prompt:
- Måste innehålla exakt vilka filer/komponenter som ska skapas.
- Måste innehålla vad som INTE ska byggas.
- Måste innehålla valideringssteg efter implementation.
```

## Lovable Build Prompt — mall

```text
Build this exactly as specified.

Project goal:
[1 mening]

Implement:
- [lista exakt vad som ska byggas]

Do NOT implement:
- [lista vad som inte ska byggas]

Technical constraints:
- [ramverk, språk, versionskrav]

Deliverables:
- [filer/komponenter]

Acceptance criteria:
- [kriterier]

Validation:
1) Run [kommando]
2) Verify [utfall]
3) Report changed files and test result
```

## Snabb kvalitetssäkring (före du kör Lovable)

Kör endast om alla är "JA":
- Är målet mätbart?
- Är scope in/out tydligt?
- Finns explicit "Do NOT implement"?
- Finns acceptanskriterier?
- Finns valideringssteg?
- Är leverabler specificerade fil-för-fil?

## Exempel: landing page-uppdrag

Bra mål:
"Bygg en statisk landing page för base76.se som positionerar CognOS som Trust Infrastructure for AI och länkar till GitHub + onboarding."

Dålig målbild:
"Bygg något snyggt för CognOS."

## När detta läge ska användas

Använd Planning Mode när:
- uppgiften känns bred eller vag
- flera agenter ska samarbeta
- du vill minska rework
- du vill kunna visa beslutslogik för team/partners

Undvik Planning Mode när:
- uppgiften är en liten bugfix med tydlig root cause

## Outcome

Rätt använt ger detta:
- mindre scope creep
- snabbare leverans
- högre träffsäkerhet i vibecoding
- tydlig handoff mellan planering och bygg

## Brand note

- Referera till Lovable med text+länk i första hand.
- Ladda inte upp tredje parts logotyper i detta repo utan uttryckligt tillstånd eller officiella brand-riktlinjer.
