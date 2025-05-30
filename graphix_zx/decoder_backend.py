"""Decoder backend modules.

This module provides:
- `BaseDecoder`: Base class for decoders.
- `XORDecoder`: XOR decoder class.
"""

import abc
import functools
import operator
from abc import ABC
from collections.abc import Mapping, Sequence

import typing_extensions


class BaseDecoder(ABC):
    """Base class for decoders."""

    @abc.abstractmethod
    def decode(self, input_cbits: Mapping[int, bool], output_cbits: Sequence[int]) -> dict[int, bool]:
        r"""Decode the input classical bits to a single bit.

        Parameters
        ----------
        input_cbits : `collections.abc.Mapping`\[`int`, `bool`\]
            A mapping of bit positions to their boolean values.
        output_cbits : `collections.abc.Sequence`\[`int`\]
            A sequence of bit positions to be decoded.

        Returns
        -------
        `dict`\[`int`, `bool`\]
            Decoded results as a dictionary mapping bit positions to their boolean values.
        """


class XORDecoder(BaseDecoder):
    """XOR decoder class."""

    @typing_extensions.override
    def decode(self, input_cbits: Mapping[int, bool], output_cbits: Sequence[int]) -> dict[int, bool]:
        r"""Decode the input classical bits to a single bit.

        Parameters
        ----------
        input_cbits : `collections.abc.Mapping`\[`int`, `bool`\]
            A mapping of bit positions to their boolean values.
        output_cbits : `collections.abc.Sequence`\[`int`\]
            A sequence of bit positions to be decoded.

        Returns
        -------
        `dict`\[`int`, `bool`\]
            The results of XOR operation on the input bits.
        """
        result: bool = functools.reduce(operator.xor, input_cbits.values(), False)
        return dict.fromkeys(output_cbits, result)


# another decoder class for FTQC will be added later
