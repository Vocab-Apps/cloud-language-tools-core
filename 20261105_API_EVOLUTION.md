# Overview
we want to enhance the `cloudlanguagetools` API while maintaining backward compatibility. 
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

# Encrypted service keys
For the backend deployment, we still want to use the mechanism in `cloudlanguagetools/encryption.py` with `CLOUDLANGUAGETOOLS_CORE_KEY`, but we want the configuration to be done using pydantic.
