# Publisher identity and signatures

The current release preparation does not create or assert a cryptographic signature. An archive checksum identifies bytes; it does not authenticate the author or publisher.

The final public records should identify the distribution version, exact archive, checksum and actual repository or deposit identifier. A signature may be supplied only if the authorised key holder actually signs the named bytes and provides enough information for recipients to verify that signature.

No institutional key, key ownership, signing approval or verification result is inferred from source metadata. Historical component signing instructions remain part of their earlier maintenance context and are not required for the browser-only publication route of this distribution.

See [distribution integrity](09-release-integrity.md) and [release preparation](08-release-process.md).
