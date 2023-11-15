from pathlib import Path
from typing import Dict, Iterable, Union

from typeguard import check_argument_types

from espnet2.text.abs_tokenizer import AbsTokenizer
from espnet2.text.char_phoneme_tokenizer import CharPhonemeTokenizer


def build_tokenizer(
    token_type: str,
    char_non_linguistic_symbols: Union[Path, str, Iterable[str]] = None,
    phone_non_linguistic_symbols: Union[Path, str, Iterable[str]] = None,
    remove_non_linguistic_symbols: bool = False,
    space_symbol: str = "<space>",
    joint_symbol: str = "@",
    nonsplit_symbol: Iterable[str] = None,
) -> CharPhonemeTokenizer:
    """A helper function to instantiate Tokenizer"""
    assert check_argument_types()

    if token_type == "char_phone" or token_type == "aux_phone":
        return CharPhonemeTokenizer(
            char_non_linguistic_symbols=char_non_linguistic_symbols,
            phone_non_linguistic_symbols=phone_non_linguistic_symbols,
            space_symbol=space_symbol,
            remove_non_linguistic_symbols=remove_non_linguistic_symbols,
            nonsplit_symbols=nonsplit_symbol,
            joint_symbol=joint_symbol,
        )
    else:
        raise ValueError(
            f"token_mode must be one of bpe, word, char or phn: " f"{token_type}"
        )
