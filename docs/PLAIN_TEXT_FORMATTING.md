# Plain Text Formatting Requirements

## Overview

The Question Answerer and Answer Checker agents have been updated to enforce plain text formatting in all generated answers. This ensures consistent, clean output without markdown or special formatting.

## Question Answerer Agent

The Question Answerer agent now generates answers that:

- **Use plain text only** - No markdown, bold, italics, or headers
- **Avoid special formatting** - No `**bold**`, `*italics*`, `` `code` ``, or `# headers`
- **No list formatting** - No bullet points (`-`), numbered lists (`1. 2. 3.`), or special characters
- **Write as natural prose** - Complete sentences in paragraph format
- **End with proper punctuation** - Answers end with a period before any URLs
- **No closing phrases** - Avoids "Learn more:", "References:", "For more information:", etc.
- **URLs at the end** - Documentation links appear at the end, separated by newlines

### Example Output

**Before (with markdown formatting):**
```
**Key Features:**
- **Custom Neural Voices:** Select from over 400 voices
- **Real-time & Batch Conversion:** Generate speech instantly
- **Voice Customization:** Personalize voice output

Learn more:
https://docs.microsoft.com/azure/ai
```

**After (plain text only):**
```
Yes, Microsoft Azure AI provides robust Text to Speech (TTS) capabilities through the Azure Speech service. Azure Text to Speech allows you to convert text input into natural human-like speech using neural voices, supporting multiple languages and voice styles. Key features include custom neural voices with selection from over 400 voices in 140+ languages and variants, real-time and batch conversion to generate speech instantly from text or process large volumes of text using batch synthesis, voice customization to personalize voice output with Speech Synthesis Markup Language (SSML) to adjust pitch, rate, pauses, and emphasis, and security and compliance to ensure data privacy and compliance with enterprise standards.

https://docs.microsoft.com/azure/ai
https://docs.microsoft.com/azure/cognitive-services/speech-service
```

## Answer Checker Agent

The Answer Checker agent validates that answers meet the plain text formatting requirements:

### Validation Criteria

The Answer Checker will **REJECT** answers that contain:

- Markdown bold syntax (`**text**`)
- Markdown italics syntax (`*text*`)
- Markdown code blocks (`` `text` ``)
- Markdown headers (`# Header`)
- Bullet points (`-` or `•`)
- Numbered lists (`1.`, `2.`, etc.)
- Closing call-to-action phrases like:
  - "Learn more:"
  - "References:"
  - "For more information, see:"
  - "For more details:"
  - "Additional resources:"

The Answer Checker will **APPROVE** answers that:

- Are written in natural prose with complete sentences
- Use plain text formatting only
- End with a period (after prose content)
- Place URLs at the end, separated by newlines
- Are accurate, complete, and relevant to the question

## Implementation Details

### Question Answerer Updates

**File:** `src/agents/question_answerer.py`

1. **Agent Instructions** - Updated to include explicit FORMATTING REQUIREMENTS section
2. **Question Prompt** - Added IMPORTANT - FORMATTING section to each query

### Answer Checker Updates

**File:** `src/agents/answer_checker.py`

1. **Agent Instructions** - Added FORMATTING VALIDATION criteria
2. **Validation Prompt** - Added FORMATTING CHECK section to validation queries

## Testing

To verify plain text formatting:

1. Generate an answer using the Question Answerer
2. Check that the output contains no markdown syntax
3. Verify the Answer Checker validates formatting correctly
4. Confirm answers are in natural prose format

## Benefits

- **Consistency** - All answers follow the same clean format
- **Readability** - Plain text is easier to read and process
- **Compatibility** - Works better with Excel, CSV, and other text formats
- **Professional** - Clean, professional appearance without visual clutter
- **Validation** - Automated checking ensures compliance

## Notes

- URLs are still included at the end of answers for reference
- Answers remain comprehensive and informative
- Natural prose format maintains readability
- The old `question_answerer_old.py` file already had similar requirements
