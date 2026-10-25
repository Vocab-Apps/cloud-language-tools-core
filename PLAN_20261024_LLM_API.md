# Overview
we want to transform the cloudlanguagetools API to allow use by LLM including through AI code generation. Let's call this the CLT-AI API.
The user will ask for a transformation to be done on some text input, and the goal will be to generate python code which can accomplish this using the CLT-AI API.

# API specifications
the API should have some well defined distinct entrypoint which correspond to existing operations in `cloudlanguagetools/servicemanager.py`. We can treat those as verbs / function names.
- `sound`: when the user wants to create audio
- `translate`: when the user wants to translate from one language to another
- `transliterate`: when the user wants to for example convert from Chinese characters to Pinyin, or generate IPA text
- `transcribe`: convert audio into text
- `llm`: when the user wants to answer a generic question or generate some text, which cannot be done with other functions.

These functions will be used in two ways:
- when generating python code, they will be the entry point or the public API into the CLT-AI API. This is the more likely mode when working as an Anki addon or in the online spreadsheet.
- when using them directly, they will be tools that the LLM has access to. This mode is more likely in Chatbot mode.

The parameters to those functions should be Pydantic models. This will allow us to do strict validation, including on the parameters that may be specific to one service (for example voice parameters). The input parameters will clearly specify the language, and parameters to use that correspond to what the services expect.

The API should be versioned, it will evolve over time, and we should keep backward compatibility when we add a new version.

# Discovery of parameters
The exact parameters expected by services are opaque, so we will need a discovery method for them (for all the verbs). Implement something that makes sense here. We should also be able to validate that parameters are correct for example when we call `sound` before making the actual call.

Each service will implement a Pydantic model which can verify its inputs.

# Default selection
when the user doesn't specify defaults, for example if they say "generate audio for this text", we will have a set of text rules that help the LLM decide the voice. For example "If the user doesn't specify which service to use for audio, choose Azure".

# Python orientation
we want to use generated python code because of its power and flexbility. We will worry about safety of executing code at another step.

# Use cases
This API will be used inside different products:
- in an Anki addon, where the user will ask to create repeatable transformations, such as "generate japanese audio using Azure female voice"
- in an online spreadsheet, where the user can create transformations such as "translate from Chinese to English"
- in an online chatbot, where the user will be able to submit standing instructions, such as "if I type text in chinese, give me the translation, pinyin and audio"

When the user asks for that type of "transformation", an LLM call will generate python code which can accomplish this using the CLT-AI API. That python code can now be looped over input to generate the same type of transformation over many rows. 

This is particularly relevant for the Anki addon and the online spreadsheet, where running transformations over rows of input will be a very typical use case.

# Use case details
## Anki addon
When used from an Anki addon, in most cases, the user will ask to create repeatable instructions. Using the python format allows us to store these repeatable instructions and reliably re-run them.
Example may include:
- "generate Japanese audio with female voice for the Kanji field, output to the sound field"
- 

# Other Notes
`cloudlanguagetools/chatapi.py` does something similar, but we want to design a new API from scratch which will replace `cloudlanguagetools/chatapi.py`. Remove `cloudlanguagetools/chatapi.py` and its tests.