from pathlib import Path
from typing import Iterable, List, Union, Dict

from packaging.version import parse as V
from typeguard import check_argument_types

from espnet2.text.abs_tokenizer import AbsTokenizer

from espnet2.text.word_tokenizer import WordTokenizer
from espnet2.text.char_tokenizer import CharTokenizer


class CharPhonemeTokenizer(AbsTokenizer):
    def __init__(
        self,
        char_non_linguistic_symbols: Union[Path, str, Iterable[str]] = None,
        phone_non_linguistic_symbols: Union[Path, str, Iterable[str]] = None,
        space_symbol: str = "<space>",
        remove_non_linguistic_symbols: bool = False,
        nonsplit_symbols: Iterable[str] = None,
        joint_symbol: str = "@",
    ):
        assert check_argument_types()
        self.space_symbol = space_symbol
        self.char_non_linguistic_symbols = char_non_linguistic_symbols
        self.phone_non_linguistic_symbols = phone_non_linguistic_symbols
        self.nonsplit_symbols = nonsplit_symbols
        self.joint_symbol = joint_symbol

        # prepare char tokenizer
        self.char_tokenizer = CharTokenizer(
            non_linguistic_symbols=char_non_linguistic_symbols,
            space_symbol=space_symbol,
            remove_non_linguistic_symbols=remove_non_linguistic_symbols,
            nonsplit_symbols=nonsplit_symbols,
        )

        # prepare phone tokenizer
        self.phone_tokenizer = WordTokenizer(
            delimiter=" ",
            non_linguistic_symbols=phone_non_linguistic_symbols,
            remove_non_linguistic_symbols=remove_non_linguistic_symbols,
        )

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f'space_symbol="{self.space_symbol}"'
            f'char_non_linguistic_symbols="{self.char_non_linguistic_symbols}"'
            f'phone_non_linguistic_symbols="{self.phone_non_linguistic_symbols}"'
            f'nonsplit_symbols="{self.nonsplit_symbols}"'
            f")"
        )

    def text2tokens(self, line: str) -> Dict[str, List[str]]:
        text_line, phone_line = line.split(self.joint_symbol)
        text_tokens = self.char_tokenizer.text2tokens(text_line)
        phone_tokens = self.phone_tokenizer.text2tokens(phone_line)

        return {"char": text_tokens, "phone": phone_tokens}

    def char_text2tokens(self, line: str) -> List[str]:
        return self.char_tokenizer.text2tokens(line)

    def phone_text2tokens(self, line: str) -> List[str]:
        return self.phone_tokenizer.text2tokens(line)

    def tokens2text(self, tokens: Iterable[str]) -> str:
        raise NotImplementedError("Cannot use this method for CharPhonemeTokenizer")

    def char_tokens2text(self, tokens: Iterable[str]) -> str:
        return self.char_tokenizer.tokens2text(tokens)

    def phone_tokens2text(self, tokens: Iterable[str]) -> str:
        return self.phone_tokenizer.tokens2text(tokens)

    def phone_text2tokens_svs(self, syllable: str) -> List[str]:
        return self.phone_tokenizer.text2tokens_svs(syllable)
