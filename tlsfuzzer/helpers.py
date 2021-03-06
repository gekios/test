# Author: Hubert Kario, (c) Red Hat 2018
# Released under Gnu GPL v2.0, see LICENSE file for details
"""Helper functions for test scripts."""

from functools import partial
from tlslite.constants import HashAlgorithm, SignatureAlgorithm, \
        SignatureScheme

from tlslite.extensions import KeyShareEntry, PreSharedKeyExtension, \
        PskIdentity
from tlslite.handshakehelpers import HandshakeHelpers
from .handshake_helpers import kex_for_group

__all__ = ['sig_algs_to_ids', 'key_share_gen', 'psk_ext_gen',
           'psk_ext_updater']


def _hash_name_to_id(h_alg):
    """Try to convert hash algorithm name to HashAlgorithm TLS ID.

    accepts also a string with a single number in it
    """
    try:
        return int(h_alg)
    except ValueError:
        return getattr(HashAlgorithm, h_alg)


def _sign_alg_name_to_id(s_alg):
    """Try to convert signature algorithm name to SignatureAlgorithm TLS ID.

    accepts also a string with a single number in it
    """
    try:
        return int(s_alg)
    except ValueError:
        return getattr(SignatureAlgorithm, s_alg)


def sig_algs_to_ids(names):
    """Convert a string with signature algorithm names to list of IDs.

    :param str names: whitespace separated list of names of hash algorithm
        names. Names can be specified as the legacy (TLS1.2) hash algorithm
        and hash type pairs (e.g. sha256+rsa), as a pair of numbers (e.g 4+1)
        or as the new TLS 1.3 signature scheme (e.g. rsa_pkcs1_sha256).
        Full string then could look like "sha256+rsa 5+rsa rsa_pss_pss_sha256"
    :raises AttributeError: when the specified identifier is not defined in
        HashAlgorithm, SignatureAlgorithm or SignatureScheme
    :return: list of tuples
    """
    ids = []

    for name in names.split():
        if '+' in name:
            h_alg, s_alg = name.split('+')

            hash_id = _hash_name_to_id(h_alg)
            sign_id = _sign_alg_name_to_id(s_alg)

            ids.append((hash_id, sign_id))
        else:
            ids.append(getattr(SignatureScheme, name))

    return ids


def key_share_gen(group, version=(3, 4)):
    """
    Create a random key share for a group of a given id.

    :param int group: TLS numerical ID from GroupName identifying the group
    :param tuple version: TLS protocol version as a tuple, as encoded on the
        wire
    :return: KeyShareEntry
    """
    kex = kex_for_group(group, version)
    private = kex.get_random_private_key()
    share = kex.calc_public_value(private)
    return KeyShareEntry().create(group, share, private)


def _get_psk_config_hash(psk_settings):
    sett_len = len(psk_settings)

    if sett_len == 2:
        psk_hash = "sha256"
    elif sett_len == 3:
        psk_hash = psk_settings[2]
    else:
        raise ValueError("Invalid number of options in PSK config")

    if psk_hash not in ("sha256", "sha384"):
        raise ValueError("Supported hashes are 'sha256' and 'sha384' only")

    return psk_hash


def psk_ext_gen(psk_settings):
    """
    Create a PreSharedKeyExtension from given settings.

    Takes a list of 2 or 3-element tuples, where the first element is an
    identity name, the second is the shared secret and the third is the name
    of the associated hash ("sha256" or "sha384", with "sha256" being the
    default).

    :param list psk_settings: list of tuples
    :return: extension generator
    """
    identities = []
    binders = []

    for config in psk_settings:
        if not config[0]:
            raise ValueError("identity can't be an empty string")

        identities.append(PskIdentity().create(config[0], 0))

        psk_hash = _get_psk_config_hash(config)

        binders.append(bytearray(32 if psk_hash == 'sha256' else 48))

    return PreSharedKeyExtension().create(identities, binders)


def _psk_ext_updater(state, client_hello, psk_settings):
    h_hash = state.handshake_hashes
    HandshakeHelpers.update_binders(client_hello,
                                    h_hash,
                                    psk_settings)


def psk_ext_updater(psk_settings):
    """
    Uses the provided settings to update the PSK binders in CH PSK extension.

    Generator that can be used to generate the callback for the
    ClientHelloGenerator.modifiers setting.

    See psk_ext_gen for a specification of psk_settings.

    This updater requires that the PSK extension be the last one in
    ClientHello.

    Please note that if the ClientHello is subsequently modified (either by
    modifiers placed after this one or generic message fuzzers) after this
    updater was run, the binders it has created will likely become invalid.
    This is because the binders sign (using an HMAC) the whole ClientHello
    message, including the handshake protocol header (the one byte handshake
    type and the 3-byte length), but excluding other binders.
    """
    return partial(_psk_ext_updater, psk_settings=psk_settings)
