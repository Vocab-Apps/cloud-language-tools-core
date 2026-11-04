# Overview
we want to enhance the `cloudlanguagetools` API with respect to configuring services. 
Overall the changes are destined to make the module distributable to end-users, letting them configure their own API keys.
We want to be able to selectively enable services, and their configuration / API keys.

# Use Cases
Currently we use `cloudlanguagetools` deployed in a backend service exposed over a REST API. But we also want to start deploying
it inside an Anki addon which will be run by individual users. And those users may not have the API key for all services, they 
may only want to configure one or two services.

# Implementation Details
We want one pydantic model which will enabled services and configure them in one go. The configuration data will be validated by pydantic.
this will replace the existing `configure_services` / `configure_default`.
If a service is not enabled, it should not be consulted to get a list of transformations / audio / other.
The reason for not enabling a services is in case the user doesn't have an API key for it, we then cannot use that service.

When a service is directly called when not enabled, it should raise an appropriate exception.

# Configuration Pydantic Model
One model with an optional sub-model per service.
We don't need to keep the shape of the existing `services_configuration.json`. Normalize the existing configuration in services to make sure things look more consistent. 
Pydantic validation is only structural, no need to check the API key with the service. Something like non-empty is sufficient.
The pydantic model should be versioned.

# Encrypted service keys
For the backend deployment, we still want to use the mechanism in `cloudlanguagetools/encryption.py` with `CLOUDLANGUAGETOOLS_CORE_KEY`, but we want the configuration to be done using pydantic.
the CLOUDLANGUAGETOOLS_CORE_KEY / encryption settings themselves become a pydantic model.

# Per-service notes
## Google Config
the temp file used when configuring google is not ideal for this use case, find out whether there is a way to configure google that is more aligned with this change.

## Gemini
we want to decouple gemini from google, see if that is possible.

## keyless services
Epitran, Spacy, PyThaiNLP, MandarinCantonese, Wenlin
those can be enabled without an API key

