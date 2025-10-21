# Formatting Comparison: Before and After

This document shows the difference between the old markdown-formatted answers and the new plain text answers.

## Issue Screenshot Reference

The original issue showed an answer with markdown formatting like this:

```
Yes, Microsoft Azure AI provides robust Text to Speech (TTS) capabilities...

**Key Features:**
- **Custom Neural Voices:** Select from over 400 voices in 140+ languages...
- **Real-time & Batch Conversion:** Generate speech instantly...
- **Voice Customization:** Personalize voice output with SSML...
- **Security and Compliance:** Ensures data privacy...

**Example: Using Text to Speech with Azure SDK (Python)**
```python
import azure.cognitiveservices.speech as speechsdk
...
```
```

## After: Plain Text Only

With the changes implemented, the same answer would be generated as:

```
Yes, Microsoft Azure AI provides robust Text to Speech (TTS) capabilities through the Azure Speech service. Azure Text to Speech allows you to convert text input into natural human-like speech using neural voices, supporting multiple languages and voice styles. Key features include custom neural voices with selection from over 400 voices in 140+ languages and variants, real-time and batch conversion to generate speech instantly from text or process large volumes of text using batch synthesis, voice customization to personalize voice output with Speech Synthesis Markup Language (SSML) to adjust pitch, rate, pauses, and emphasis, and security and compliance to ensure data privacy and compliance with enterprise standards. Using Text to Speech with Azure SDK requires Python and involves importing the azure.cognitiveservices.speech module, creating a speech configuration with your subscription key and service region, setting the speech synthesis voice name, creating a synthesizer, and using the speak_text_async method to generate speech from text input.

https://docs.microsoft.com/azure/cognitive-services/speech-service/
https://docs.microsoft.com/azure/cognitive-services/speech-service/get-started-text-to-speech
```

## Key Differences

| Aspect | Before (Markdown) | After (Plain Text) |
|--------|-------------------|-------------------|
| Bold text | `**text**` | Plain text |
| Headers | `**Key Features:**` | Integrated into prose |
| Lists | `- **Item:** Description` | Complete sentences |
| Code blocks | Python code in ``` blocks | Description in prose |
| Formatting | Visual hierarchy | Natural prose flow |
| Closing phrases | "Learn more:", "References:" | URLs only |

## Benefits of Plain Text

1. **Better Excel/CSV compatibility** - No special characters to escape
2. **Cleaner copy/paste** - Works seamlessly in any text field
3. **More professional** - Reads like formal documentation
4. **Consistent output** - Every answer follows the same format
5. **Easier validation** - Clear rules for acceptance

## Implementation

Both the Question Answerer and Answer Checker have been updated to enforce this format:

- Question Answerer generates only plain text
- Answer Checker validates and rejects markdown formatting
- Clear instructions prevent markdown in responses
- Validation ensures compliance before accepting answers
